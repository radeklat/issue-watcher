import warnings
from contextlib import contextmanager
from time import perf_counter, time
from typing import Callable, List, Type
from unittest.mock import ANY, MagicMock, patch

import pytest
from requests import HTTPError

from issuewatcher import GitHubIssueState, GitHubIssueTestCase

# False positive cause by pytest fixtures
# pylint: disable=redefined-outer-name


class _ClassWithRepositoryOnly(GitHubIssueTestCase):
    _REPOSITORY = "issue-watcher"


class _ClassWithOwnerOnly(GitHubIssueTestCase):
    _OWNER = "radeklat"


class OwnerAndRepoSet(_ClassWithRepositoryOnly, _ClassWithOwnerOnly):
    pass


class TestRepositoryAttributeHandling:
    @staticmethod
    @pytest.mark.parametrize(
        "testing_class,constructor_arguments",
        [
            pytest.param(_ClassWithRepositoryOnly, [], id="class, name only"),
            pytest.param(_ClassWithOwnerOnly, [], id="class, owner only"),
            pytest.param(GitHubIssueTestCase, ["owner_only"], id="constructor, owner only"),
            pytest.param(
                GitHubIssueTestCase, [None, "repo_only"], id="constructor, name only"
            ),
            pytest.param(
                _ClassWithOwnerOnly,
                [None, "repo_only"],
                id="class - owner, constructor - name",
            ),
            pytest.param(
                _ClassWithRepositoryOnly,
                ["owner_only"],
                id="class - name, constructor - owner",
            ),
        ],
    )
    def test_it_raises_error_when_some_parameters_are_missing(
        testing_class: Type[GitHubIssueTestCase], constructor_arguments: List
    ):
        with pytest.raises(ValueError):
            testing_class(*constructor_arguments)

    @staticmethod
    def test_contructor_arguments_have_precedence_over_class_attributes():
        owner = "other_owner"
        name = "other_name"
        instance = OwnerAndRepoSet(owner, name)

        assert instance._repo_id == f"{owner}/{name}"


_ISSUE_NUMBER = 123


@pytest.fixture()
def requests_mock():
    requests_patcher = patch("issuewatcher.github.requests")

    try:
        yield requests_patcher.start()
    finally:
        requests_patcher.stop()


@pytest.fixture()
def instance_no_caching():
    with patch.dict("os.environ", {"CACHE_INVALIDATION_IN_SECONDS": "0"}):
        instance = OwnerAndRepoSet()

    return instance


def _set_issue_state(req_mock: MagicMock, value: str, status_code: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = {"state": value}
    mock_response.status_code = status_code
    req_mock.get.return_value = mock_response


class TestStateCheck:
    @staticmethod
    @pytest.mark.parametrize(
        "expected_state,returned_state",
        [
            pytest.param(GitHubIssueState.open, "closed", id="open closed"),
            pytest.param(GitHubIssueState.closed, "open", id="closed open"),
        ],
    )
    def test_it_fails_on_non_matching_state(
        instance_no_caching: GitHubIssueTestCase,
        requests_mock: MagicMock,
        expected_state: GitHubIssueState,
        returned_state: str,
    ):
        _set_issue_state(requests_mock, returned_state)

        with pytest.raises(AssertionError):
            instance_no_caching.assert_github_issue_is_state(_ISSUE_NUMBER, expected_state)

    @staticmethod
    @pytest.mark.parametrize(
        "expected_state,returned_state",
        [
            pytest.param(GitHubIssueState.open, "open", id="open"),
            pytest.param(GitHubIssueState.closed, "closed", id="closed"),
        ],
    )
    def test_it_does_not_fail_on_matching_state(
        instance_no_caching: GitHubIssueTestCase,
        requests_mock: MagicMock,
        expected_state: GitHubIssueState,
        returned_state: str,
    ):
        _set_issue_state(requests_mock, returned_state)
        instance_no_caching.assert_github_issue_is_state(_ISSUE_NUMBER, expected_state)


def _fail_open_state_check(
    issue_test_case: GitHubIssueTestCase, req_mock: MagicMock, msg: str = ""
):
    _set_issue_state(req_mock, GitHubIssueState.closed.value)
    issue_test_case.assert_github_issue_is_open(_ISSUE_NUMBER, msg)


class TestFailingStateCheck:
    @staticmethod
    @pytest.mark.parametrize(
        "regexp",
        [
            pytest.param(
                f"https://github.com/radeklat/issue-watcher/issues/{_ISSUE_NUMBER}",
                id="link to issue",
            ),
            pytest.param("'radeklat/issue-watcher'", id="owner and repository"),
            pytest.param("no longer open\\.", id="expected issue state"),
            pytest.param(f"#{_ISSUE_NUMBER}", id="issue number"),
        ],
    )
    def test_it_contains(
        regexp: str, instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        with pytest.raises(AssertionError, match=f".*{regexp}.*"):
            _fail_open_state_check(instance_no_caching, requests_mock)

    @staticmethod
    def test_it_contains_custom_message_if_one_provided(
        instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        msg = "Sample custom message"
        with pytest.raises(AssertionError, match=f".*open\\. {msg} Visit.*"):
            _fail_open_state_check(instance_no_caching, requests_mock, msg=msg)

    @staticmethod
    def test_it_does_not_contains_custom_message_if_none_provided(
        instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        with pytest.raises(AssertionError, match=f".*open\\. Visit.*"):
            _fail_open_state_check(instance_no_caching, requests_mock)


_CURRENT_NUMBER_OF_RELEASES = 3


def _set_number_or_releases_to(req_mock: MagicMock, count: int, status_code: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = [{}] * count
    mock_response.status_code = status_code
    req_mock.get.return_value = mock_response


class TestReleaseNumberCheck:
    @staticmethod
    def test_it_fails_when_new_releases_available(
        instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        _set_number_or_releases_to(requests_mock, _CURRENT_NUMBER_OF_RELEASES + 1)
        with pytest.raises(AssertionError, match="New release of .*"):
            instance_no_caching.assert_no_new_release_is_available(
                _CURRENT_NUMBER_OF_RELEASES
            )

    @staticmethod
    def test_it_does_not_fail_when_expected_releases_available(
        instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        _set_number_or_releases_to(requests_mock, _CURRENT_NUMBER_OF_RELEASES)
        instance_no_caching.assert_no_new_release_is_available(_CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_checks_if_release_number_is_properly_configured(
        instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        _set_number_or_releases_to(requests_mock, _CURRENT_NUMBER_OF_RELEASES - 1)
        with pytest.raises(AssertionError, match=".*improperly configured.*"):
            instance_no_caching.assert_no_new_release_is_available(
                _CURRENT_NUMBER_OF_RELEASES
            )


class TestHttpErrorRaising:
    _GENERIC_ERROR_MESSAGE_PATTERN = ".*Request to GitHub Failed.*"

    def test_it_raises_when_status_not_200_in_state_check(
        self, instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        _set_issue_state(requests_mock, "open", 500)

        with pytest.raises(HTTPError, match=self._GENERIC_ERROR_MESSAGE_PATTERN):
            instance_no_caching.assert_github_issue_is_open(_ISSUE_NUMBER)

    def test_it_raises_when_status_not_200_in_releases_check(
        self, instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        _set_number_or_releases_to(requests_mock, _CURRENT_NUMBER_OF_RELEASES, 500)

        with pytest.raises(HTTPError, match=self._GENERIC_ERROR_MESSAGE_PATTERN):
            instance_no_caching.assert_no_new_release_is_available(
                _CURRENT_NUMBER_OF_RELEASES
            )

    @staticmethod
    def test_it_raises_with_info_about_rate_limit_when_exceeded(
        instance_no_caching: GitHubIssueTestCase, requests_mock: MagicMock
    ):
        _set_limit_exceeded(requests_mock)

        with pytest.raises(HTTPError, match=".*Current quota:.*"):
            instance_no_caching.assert_github_issue_is_open(_ISSUE_NUMBER)


_OPEN_ISSUE_NUMBER = 1
_CLOSED_ISSUE_NUMBER = 2


class TestChecksLive:
    @staticmethod
    def test_open_issue_check_fails_when_closed(instance_no_caching: GitHubIssueTestCase):
        with pytest.raises(AssertionError):
            try:
                instance_no_caching.assert_github_issue_is_open(
                    _CLOSED_ISSUE_NUMBER, "Custom message."
                )
            except AssertionError as ex:
                print(ex)
                raise ex

    @staticmethod
    def test_open_issue_check_does_not_fail_when_open(
        instance_no_caching: GitHubIssueTestCase
    ):
        instance_no_caching.assert_github_issue_is_open(_OPEN_ISSUE_NUMBER)

    @staticmethod
    def test_closed_issue_check_fails_when_open(instance_no_caching: GitHubIssueTestCase):
        with pytest.raises(AssertionError):
            instance_no_caching.assert_github_issue_is_closed(_OPEN_ISSUE_NUMBER)

    @staticmethod
    def test_closed_issue_check_does_not_fail_when_closed(
        instance_no_caching: GitHubIssueTestCase
    ):
        instance_no_caching.assert_github_issue_is_closed(_CLOSED_ISSUE_NUMBER)

    @staticmethod
    def test_release_number_check_fails_when_new_releases_available(
        instance_no_caching: GitHubIssueTestCase
    ):
        with pytest.raises(AssertionError, match=".*New release of .*") as ex:
            instance_no_caching.assert_no_new_release_is_available(0)

        print(ex)  # for quick grab of string for documentation


@contextmanager
def _timer():
    start = perf_counter()
    try:
        yield
    finally:
        print(f"Executed in {(perf_counter() - start) * 1000000:.3f}us")


@pytest.fixture()
def instance_caching():
    instance = OwnerAndRepoSet()

    # first call can be cache miss
    instance.assert_github_issue_is_closed(_CLOSED_ISSUE_NUMBER)
    try:
        instance.assert_no_new_release_is_available(0)
    except AssertionError:
        pass

    return instance


class TestCaching:
    @staticmethod
    def test_closed_issue_check_does_not_fail_when_closed(
        instance_caching: GitHubIssueTestCase
    ):
        with _timer():
            instance_caching.assert_github_issue_is_closed(_CLOSED_ISSUE_NUMBER)

    @staticmethod
    def test_release_check_fails_when_new_releases_available(
        instance_caching: GitHubIssueTestCase
    ):
        with _timer():
            with pytest.raises(AssertionError, match=".*New release of .*"):
                instance_caching.assert_no_new_release_is_available(0)


def noop(_: GitHubIssueTestCase):
    pass


def _set_limit_exceeded(req_mock: MagicMock):
    mock_message = "Message from GitHub"
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": mock_message}
    mock_response.status_code = 403
    mock_response.headers = {
        "X-RateLimit-Remaining": 0,
        "X-RateLimit-Limit": 60,
        "X-RateLimit-Reset": time() + 3600,
    }
    req_mock.get.return_value = mock_response


class TestAuthentication:
    @staticmethod
    def _init_with_user_name_token_and_assert(
        requests_mock: MagicMock,
        username: str,
        token: str,
        assertion: Callable[[GitHubIssueTestCase], None] = noop,
    ):
        with patch.dict(
            "os.environ",
            {
                "GITHUB_USER_NAME": username,
                "GITHUB_PERSONAL_ACCESS_TOKEN": token,
                "CACHE_INVALIDATION_IN_SECONDS": "0",
            },
        ):
            _set_issue_state(requests_mock, "open")
            instance = OwnerAndRepoSet()
            instance.assert_github_issue_is_open(_ISSUE_NUMBER)
            assertion(instance)

    @pytest.mark.parametrize(
        "username,token",
        [
            pytest.param("", "", id="no user or token supplied"),
            pytest.param("", "sometoken", id="no user supplied"),
            pytest.param("some user", "", id="no token supplied"),
        ],
    )
    def test_it_is_not_used_when(self, requests_mock: MagicMock, username: str, token: str):
        try:
            warnings.simplefilter("ignore", category=RuntimeWarning)
            self._init_with_user_name_token_and_assert(
                requests_mock,
                username,
                token,
                lambda _: requests_mock.get.assert_called_with(ANY, auth=None),
            )
        finally:
            warnings.resetwarnings()

    def test_it_displays_warning_when_partial_credentials_supplied(
        self, requests_mock: MagicMock
    ):
        with pytest.warns(RuntimeWarning, match=".*improperly configured.*"):
            self._init_with_user_name_token_and_assert(
                requests_mock, "some username no token", ""
            )

    @pytest.mark.parametrize(
        "username,token",
        [
            pytest.param("", "", id="no user or token supplied"),
            pytest.param("some user", "some token", id="both user and token supplier"),
        ],
    )
    def test_it_displays_no_warnings_when(
        self, requests_mock: MagicMock, username: str, token: str
    ):
        with warnings.catch_warnings(record=True) as warnings_list:
            self._init_with_user_name_token_and_assert(requests_mock, username, token)
            assert not warnings_list

    def test_it_is_used_when_credentials_supplied(self, requests_mock: MagicMock):
        credentials = ("some username", "some token")

        self._init_with_user_name_token_and_assert(
            requests_mock,
            *credentials,
            assertion=lambda _: requests_mock.get.assert_called_with(ANY, auth=credentials),
        )

    def test_it_is_suggested_when_api_rate_exceeded(self, requests_mock: MagicMock):
        def _assertion(instance: GitHubIssueTestCase):
            _set_limit_exceeded(requests_mock)

            with pytest.raises(HTTPError, match=".*Consider setting.*"):
                instance.assert_github_issue_is_open(_ISSUE_NUMBER)

        self._init_with_user_name_token_and_assert(requests_mock, "", "", _assertion)
