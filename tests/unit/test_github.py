import re
import warnings
from contextlib import ExitStack, contextmanager
from time import perf_counter, time
from typing import Callable, List
from unittest.mock import ANY, MagicMock, patch

import pytest
from requests import HTTPError

from issuewatcher import AssertGitHubIssue, GitHubIssueState

# False positive caused by pytest fixtures and class use
# pylint: disable=redefined-outer-name, too-few-public-methods


_REPOSITORY_ID = "radeklat/issue-watcher"


class TestRepositoryAttributeHandling:
    @staticmethod
    @pytest.mark.parametrize(
        "constructor_arguments",
        [
            pytest.param([""], id="has no slashes"),
            pytest.param(["//"], id="has too many slashes"),
        ],
    )
    def test_it_raises_error_when_repository_id(constructor_arguments: List):
        with pytest.raises(ValueError):
            AssertGitHubIssue(*constructor_arguments)


_ISSUE_NUMBER = 123


@pytest.fixture()
def requests_mock():
    requests_patcher = patch("issuewatcher.github.requests")

    try:
        yield requests_patcher.start()
    finally:
        requests_patcher.stop()


@pytest.fixture()
def assert_github_issue_no_cache():
    with patch.dict("os.environ", {"CACHE_INVALIDATION_IN_SECONDS": "0"}):
        assert_github_issue = AssertGitHubIssue(_REPOSITORY_ID)

    return assert_github_issue


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
        assert_github_issue_no_cache: AssertGitHubIssue,
        requests_mock: MagicMock,
        expected_state: GitHubIssueState,
        returned_state: str,
    ):
        _set_issue_state(requests_mock, returned_state)

        with pytest.raises(AssertionError):
            assert_github_issue_no_cache.is_state(_ISSUE_NUMBER, expected_state)

    @staticmethod
    @pytest.mark.parametrize(
        "expected_state,returned_state",
        [
            pytest.param(GitHubIssueState.open, "open", id="open"),
            pytest.param(GitHubIssueState.closed, "closed", id="closed"),
        ],
    )
    def test_it_does_not_fail_on_matching_state(
        assert_github_issue_no_cache: AssertGitHubIssue,
        requests_mock: MagicMock,
        expected_state: GitHubIssueState,
        returned_state: str,
    ):
        _set_issue_state(requests_mock, returned_state)
        assert_github_issue_no_cache.is_state(_ISSUE_NUMBER, expected_state)


def _fail_open_state_check(
    assert_github_issue: AssertGitHubIssue, req_mock: MagicMock, msg: str = ""
):
    _set_issue_state(req_mock, GitHubIssueState.closed.value)
    assert_github_issue.is_open(_ISSUE_NUMBER, msg)


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
        regexp: str,
        assert_github_issue_no_cache: AssertGitHubIssue,
        requests_mock: MagicMock,
    ):
        with pytest.raises(AssertionError, match=f".*{regexp}.*"):
            _fail_open_state_check(assert_github_issue_no_cache, requests_mock)

    @staticmethod
    def test_it_contains_custom_message_if_one_provided(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        msg = "Sample custom message"
        with pytest.raises(AssertionError, match=f".*open\\. {msg} Visit.*"):
            _fail_open_state_check(assert_github_issue_no_cache, requests_mock, msg=msg)

    @staticmethod
    def test_it_does_not_contains_custom_message_if_none_provided(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        with pytest.raises(AssertionError, match=".*open\\. Visit.*"):
            _fail_open_state_check(assert_github_issue_no_cache, requests_mock)


_CURRENT_NUMBER_OF_RELEASES = 3


def _set_number_of_releases_to(req_mock: MagicMock, count: int, status_code: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = [{}] * count
    mock_response.status_code = status_code
    req_mock.get.return_value = mock_response


def _set_git_tags_to(req_mock: MagicMock, tags: List[str], status_code: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"ref": f"refs/tags/{tag}"} for tag in tags]
    mock_response.status_code = status_code
    req_mock.get.return_value = mock_response


class TestReleaseNumberCheck:
    @staticmethod
    def test_it_fails_when_new_releases_available(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_number_of_releases_to(requests_mock, _CURRENT_NUMBER_OF_RELEASES + 1)
        with pytest.raises(AssertionError, match="New release of .*"):
            assert_github_issue_no_cache.current_release(_CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_does_not_fail_when_expected_releases_available(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_number_of_releases_to(requests_mock, _CURRENT_NUMBER_OF_RELEASES)
        assert_github_issue_no_cache.current_release(_CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_checks_if_release_number_is_properly_configured(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_number_of_releases_to(requests_mock, _CURRENT_NUMBER_OF_RELEASES - 1)
        with pytest.raises(AssertionError, match=".*improperly configured.*"):
            assert_github_issue_no_cache.current_release(_CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_shows_current_release_number_if_none_given(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_number_of_releases_to(requests_mock, 1)
        with pytest.raises(
            AssertionError,
            match=".*test does not have any number of releases set.*"
            "number of releases is '[0-9]+'",
        ):
            assert_github_issue_no_cache.current_release()


class TestReleaseVersionCheck:
    @staticmethod
    @pytest.mark.parametrize(
        "latest_version",
        [
            pytest.param("2.0.0", id="exact match"),
            pytest.param("2.0.0+1", id="build metadata above expected"),
            pytest.param("2.0.1", id="patch number above expected"),
            pytest.param("2.1.0", id="minor number above expected"),
            pytest.param("3.0.0", id="major number above expected"),
        ],
    )
    def test_it_fails_when_latest_version_is(
        assert_github_issue_no_cache: AssertGitHubIssue,
        requests_mock: MagicMock,
        latest_version: str,
    ):
        _set_git_tags_to(requests_mock, [latest_version])
        with pytest.raises(
            AssertionError, match=f"Release '2\\.0\\.0' of.*'{re.escape(latest_version)}'"
        ):
            assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    def test_it_fails_when_latest_version_high_enough_but_first_is_tag_is_not(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_git_tags_to(requests_mock, ["1.0.0", "3.0.0"])
        with pytest.raises(AssertionError, match=f"Release '2\\.0\\.0' of.*'3\\.0\\.0'"):
            assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    def test_it_ignores_invalid_version_numbers(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_git_tags_to(requests_mock, ["not_a_release", "1.0.0", "releases/3.0.0"])
        assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    @pytest.mark.parametrize(
        "latest_version",
        [
            pytest.param("2.0.0-alpha", id="pre-release above expected"),
            pytest.param("2.0.0-alpha.1", id="numbered pre-release above expected"),
            pytest.param(
                "2.0.0-alpha+1", id="pre-release and build metadata above expected"
            ),
            pytest.param("2.0.0a", id="non-semantic pre-release above expected"),
            pytest.param("2.0.0a0", id="non-semantic numbered pre-release above expected"),
            pytest.param("1.0.0", id="below expected"),
        ],
    )
    def test_it_does_not_fail_when_latest_version_is(
        assert_github_issue_no_cache: AssertGitHubIssue,
        requests_mock: MagicMock,
        latest_version: str,
    ):
        _set_git_tags_to(requests_mock, [latest_version])
        assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    @pytest.mark.parametrize(
        "version",
        [
            pytest.param("releases/2.0.1", id="releases/2.0.1"),
            pytest.param("not_a_release_tag", id="not_a_release_tag"),
        ],
    )
    def test_it_ignores_invalid_version_tags(
        assert_github_issue_no_cache: AssertGitHubIssue,
        requests_mock: MagicMock,
        version: str,
    ):
        _set_git_tags_to(requests_mock, [version, "1.0.0"])
        assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    def test_it_shows_current_release_number_if_none_given(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_git_tags_to(requests_mock, ["2.0.0"])
        with pytest.raises(
            AssertionError,
            match=".*test does not have expected version number set.*version is.*2\\.0\\.0",
        ):
            assert_github_issue_no_cache.fixed_in()


class TestHttpErrorRaising:
    _GENERIC_ERROR_MESSAGE_PATTERN = ".*Request to GitHub Failed.*"

    def test_it_raises_when_status_not_200_in_state_check(
        self, assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_issue_state(requests_mock, "open", 500)

        with pytest.raises(HTTPError, match=self._GENERIC_ERROR_MESSAGE_PATTERN):
            assert_github_issue_no_cache.is_open(_ISSUE_NUMBER)

    def test_it_raises_when_status_not_200_in_releases_check(
        self, assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_number_of_releases_to(requests_mock, _CURRENT_NUMBER_OF_RELEASES, 500)

        with pytest.raises(HTTPError, match=self._GENERIC_ERROR_MESSAGE_PATTERN):
            assert_github_issue_no_cache.current_release(_CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_raises_with_info_about_rate_limit_when_exceeded(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        _set_limit_exceeded(requests_mock)

        with pytest.raises(HTTPError, match=".*Current quota:.*"):
            assert_github_issue_no_cache.is_open(_ISSUE_NUMBER)


_OPEN_ISSUE_NUMBER = 1
_CLOSED_ISSUE_NUMBER = 2


class TestChecksLive:
    @staticmethod
    def test_open_issue_check_fails_when_closed(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        with pytest.raises(AssertionError):
            try:
                assert_github_issue_no_cache.is_open(
                    _CLOSED_ISSUE_NUMBER, "Custom message."
                )
            except AssertionError as ex:
                print(ex)
                raise ex

    @staticmethod
    def test_open_issue_check_does_not_fail_when_open(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        assert_github_issue_no_cache.is_open(_OPEN_ISSUE_NUMBER)

    @staticmethod
    def test_closed_issue_check_fails_when_open(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        with pytest.raises(AssertionError):
            assert_github_issue_no_cache.is_closed(_OPEN_ISSUE_NUMBER)

    @staticmethod
    def test_closed_issue_check_does_not_fail_when_closed(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        assert_github_issue_no_cache.is_closed(_CLOSED_ISSUE_NUMBER)

    @staticmethod
    def test_release_number_check_fails_when_new_releases_available(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        with pytest.raises(AssertionError, match=".*New release of .*") as ex:
            assert_github_issue_no_cache.current_release(0)

        print(ex)  # for quick grab of string for documentation


@contextmanager
def _timer():
    start = perf_counter()
    try:
        yield
    finally:
        print(f"Executed in {(perf_counter() - start) * 1000000:.3f}us")


@pytest.fixture()
def assert_github_issue_caching():
    assert_github_issue = AssertGitHubIssue(_REPOSITORY_ID)

    # first call can be cache miss
    assert_github_issue.is_closed(_CLOSED_ISSUE_NUMBER)
    try:
        assert_github_issue.current_release(0)
    except AssertionError:
        pass

    return assert_github_issue


class TestCaching:
    @staticmethod
    def test_closed_issue_check_does_not_fail_when_closed(
        assert_github_issue_caching: AssertGitHubIssue
    ):
        with _timer():
            assert_github_issue_caching.is_closed(_CLOSED_ISSUE_NUMBER)

    @staticmethod
    def test_release_check_fails_when_new_releases_available(
        assert_github_issue_caching: AssertGitHubIssue
    ):
        with _timer():
            with pytest.raises(AssertionError, match=".*New release of .*"):
                assert_github_issue_caching.current_release(0)


def noop(_: AssertGitHubIssue):
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
        assertion: Callable[[AssertGitHubIssue], None] = noop,
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
            assert_github_issue = AssertGitHubIssue(_REPOSITORY_ID)
            assert_github_issue.is_open(_ISSUE_NUMBER)
            assertion(assert_github_issue)

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
        def _assertion(assert_github_issue: AssertGitHubIssue):
            _set_limit_exceeded(requests_mock)

            with pytest.raises(HTTPError, match=".*Consider setting.*"):
                assert_github_issue.is_open(_ISSUE_NUMBER)

        self._init_with_user_name_token_and_assert(requests_mock, "", "", _assertion)


@pytest.fixture(scope="function")
def python_version_mock(request):
    patcher = patch("platform.python_version", return_value=request.param)

    try:
        yield patcher.start()
    finally:
        patcher.stop()


class TestPythonSupportChecks:
    @staticmethod
    @pytest.mark.parametrize(
        "python_version_mock,expectation",
        [
            pytest.param(
                "3.5.0", pytest.raises(OSError), id="OSError when Python version is too low"
            ),
            pytest.param(
                "3.6.0", ExitStack(), id="nothing when Python version is in range"
            ),
            pytest.param(
                "3.9.0", pytest.warns(Warning), id="Warning when Python version is too high"
            ),
        ],
        indirect=["python_version_mock"],
    )
    def test_it_raises(python_version_mock, expectation):  # pylint: disable=unused-argument
        with expectation:
            AssertGitHubIssue(_REPOSITORY_ID)
