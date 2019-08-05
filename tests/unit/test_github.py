import warnings
from time import time
from typing import Any
from unittest.mock import ANY, MagicMock, patch

from parameterized import parameterized
from requests import HTTPError

from issuewatcher import GitHubIssueState, GitHubIssueTestCase


class EmptyOwnerAndRepository(GitHubIssueTestCase):
    def setUp(self):
        requests_patcher = patch("issuewatcher.github.requests")
        self._requests_mock = requests_patcher.start()
        self.addCleanup(requests_patcher.stop)

    def _set_issue_state(self, value: str, status_code: int = 200):
        mock_response = MagicMock()
        mock_response.json.return_value = {"state": value}
        mock_response.status_code = status_code
        self._requests_mock.get.return_value = mock_response

    def _set_number_or_releases_to(self, count: int, status_code: int = 200):
        mock_response = MagicMock()
        mock_response.json.return_value = [{}] * count
        mock_response.status_code = status_code
        self._requests_mock.get.return_value = mock_response

    def _fail_open_state_check(self, msg: str = ""):
        self._set_issue_state(GitHubIssueState.closed.value)
        self.assert_github_issue_is_open(_ISSUE_NUMBER, msg)


class RepositoryNameCheck(EmptyOwnerAndRepository):
    _REPOSITORY = "issue-watcher"

    def test_it_checks_it_is_set(self):
        with self.assertRaises(RuntimeError):
            self._fail_open_state_check()


class RepositoryOwnerCheck(EmptyOwnerAndRepository):
    _OWNER = "radeklat"

    def test_it_checks_it_is_set(self):
        with self.assertRaises(RuntimeError):
            self._fail_open_state_check()


class OwnerAndRepoSet(GitHubIssueTestCase):
    _OWNER = "radeklat"
    _REPOSITORY = "issue-watcher"


class MockedOwnerAndRepoSet(OwnerAndRepoSet, EmptyOwnerAndRepository):
    pass


def get_test_case_name_without_index(test_case_func, _param_num, params):
    return f"{test_case_func.__name__}_{parameterized.to_safe_name(params[0][0])}"


_ISSUE_NUMBER = 123


class StateCheck(MockedOwnerAndRepoSet):
    @parameterized.expand(
        [
            ("open closed", GitHubIssueState.open, "closed"),
            ("closed open", GitHubIssueState.closed, "open"),
        ],
        name_func=get_test_case_name_without_index,
    )
    def test_it_fails_on_non_matching_state(self, _, expected_state, returned_state):
        self._set_issue_state(returned_state)

        with self.assertRaises(AssertionError):
            self.assert_github_issue_is_state(_ISSUE_NUMBER, expected_state)

    @parameterized.expand(
        [("open", GitHubIssueState.open), ("closed", GitHubIssueState.closed)],
        name_func=get_test_case_name_without_index,
    )
    def test_it_does_not_fail_on_matching_state(self, returned_state, expected_state):
        self._set_issue_state(returned_state)
        self.assert_github_issue_is_state(_ISSUE_NUMBER, expected_state)


class FailingStateCheck(MockedOwnerAndRepoSet):
    @parameterized.expand(
        [
            (
                "link to issue",
                f"https://github.com/radeklat/issue-watcher/issues/{_ISSUE_NUMBER}",
            ),
            ("owner and repository", "'radeklat/issue-watcher'"),
            ("expected issue state", "no longer open\\."),
            ("issue number", f"#{_ISSUE_NUMBER}"),
        ],
        name_func=get_test_case_name_without_index,
    )
    def test_it_contains(self, _name, regexp):
        with self.assertRaisesRegex(AssertionError, f".*{regexp}.*"):
            self._fail_open_state_check()

    def test_it_contains_custom_message_if_one_provided(self):
        msg = "Sample custom message"
        with self.assertRaisesRegex(AssertionError, f".*open\\. {msg} Visit.*"):
            self._fail_open_state_check(msg=msg)

    def test_it_does_not_contains_custom_message_if_none_provided(self):
        with self.assertRaisesRegex(AssertionError, f".*open\\. Visit.*"):
            self._fail_open_state_check()


class OpenIssueCheck(MockedOwnerAndRepoSet):
    def test_it_fails_when_closed(self):
        self._set_issue_state("closed")

        with self.assertRaises(AssertionError):
            self.assert_github_issue_is_open(_ISSUE_NUMBER)

    def test_it_does_not_fail_when_open(self):
        self._set_issue_state("open")
        self.assert_github_issue_is_open(_ISSUE_NUMBER)


class ClosedIssueCheck(MockedOwnerAndRepoSet):
    def test_it_fails_when_open(self):
        self._set_issue_state("open")

        with self.assertRaises(AssertionError):
            self.assert_github_issue_is_closed(_ISSUE_NUMBER)

    def test_it_does_not_fail_when_closed(self):
        self._set_issue_state("closed")
        self.assert_github_issue_is_closed(_ISSUE_NUMBER)


_CURRENT_NUMBER_OF_RELEASES = 3


class ReleaseNumberCheck(MockedOwnerAndRepoSet):
    def test_it_fails_when_new_releases_available(self):
        self._set_number_or_releases_to(_CURRENT_NUMBER_OF_RELEASES + 1)
        with self.assertRaisesRegex(AssertionError, "New release of .*"):
            self.assert_no_new_release_is_available(_CURRENT_NUMBER_OF_RELEASES)

    def test_it_does_not_fail_when_expected_releases_available(self):
        self._set_number_or_releases_to(_CURRENT_NUMBER_OF_RELEASES)
        self.assert_no_new_release_is_available(_CURRENT_NUMBER_OF_RELEASES)

    def test_it_checks_if_release_number_is_properly_configured(self):
        self._set_number_or_releases_to(_CURRENT_NUMBER_OF_RELEASES - 1)
        with self.assertRaisesRegex(AssertionError, ".*improperly configured.*"):
            self.assert_no_new_release_is_available(_CURRENT_NUMBER_OF_RELEASES)


class HttpErrorRaising(MockedOwnerAndRepoSet):
    _GENERIC_ERROR_MESSAGE_PATTERN = ".*Request to GitHub Failed.*"

    def test_it_raises_when_status_not_200_in_state_check(self):
        self._set_issue_state("open", 500)

        with self.assertRaisesRegex(HTTPError, self._GENERIC_ERROR_MESSAGE_PATTERN):
            self.assert_github_issue_is_open(_ISSUE_NUMBER)

    def test_it_raises_when_status_not_200_in_releases_check(self):
        self._set_number_or_releases_to(_CURRENT_NUMBER_OF_RELEASES, 500)

        with self.assertRaisesRegex(HTTPError, self._GENERIC_ERROR_MESSAGE_PATTERN):
            self.assert_no_new_release_is_available(_CURRENT_NUMBER_OF_RELEASES)

    def test_it_raises_with_info_about_rate_limit_when_exceeded(self):
        mock_message = "Message from GitHub"
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": mock_message}
        mock_response.status_code = 403
        mock_response.headers = {
            "X-RateLimit-Remaining": 0,
            "X-RateLimit-Limit": 60,
            "X-RateLimit-Reset": time() + 3600,
        }
        self._requests_mock.get.return_value = mock_response

        with self.assertRaisesRegex(HTTPError, ".*Current quota:.*"):
            self.assert_github_issue_is_open(_ISSUE_NUMBER)


_OPEN_ISSUE_NUMBER = 1
_CLOSED_ISSUE_NUMBER = 2


class LiveOpenIssueCheck(OwnerAndRepoSet):
    def test_it_fails_when_closed(self):
        with self.assertRaises(AssertionError):
            try:
                self.assert_github_issue_is_open(_CLOSED_ISSUE_NUMBER)
            except AssertionError as ex:
                print(ex)
                raise ex

    def test_open_issue_check_does_not_fail_when_open(self):
        self.assert_github_issue_is_open(_OPEN_ISSUE_NUMBER)


class LiveClosedIssueCheck(OwnerAndRepoSet):
    def test_closed_issue_check_fails_when_open(self):
        with self.assertRaises(AssertionError):
            self.assert_github_issue_is_closed(_OPEN_ISSUE_NUMBER)

    def test_closed_issue_check_does_not_fail_when_closed(self):
        self.assert_github_issue_is_closed(_CLOSED_ISSUE_NUMBER)


class LiveReleaseNumberCheck(OwnerAndRepoSet):
    def test_it_fails_when_new_releases_available(self):
        try:
            self.assert_no_new_release_is_available(0)
            self.fail("Expected AssertionError exception not raised.")
        except AssertionError as ex:
            print(ex)
            if "New release of " not in str(ex):
                raise ex


class Authentication(MockedOwnerAndRepoSet):
    def _init_with_user_name_token_and_test_auth(
        self, username, token, auth: Any = "don't check"
    ):
        mock_environ = {"GITHUB_USER_NAME": username, "GITHUB_PERSONAL_ACCESS_TOKEN": token}
        with patch.dict("os.environ", mock_environ):

            class InitMock(MockedOwnerAndRepoSet):
                def run_test(self):
                    self._set_issue_state("open")

                    try:
                        self.assert_github_issue_is_open(_ISSUE_NUMBER)
                    except AssertionError:
                        pass

                    if auth != "don't check":
                        self._requests_mock.get.assert_called_with(ANY, auth=auth)

            init_mock = InitMock()
            init_mock.setUp()
            init_mock.run_test()
            init_mock.doCleanups()

    @parameterized.expand(
        [
            ("no user or token supplied", "", ""),
            ("no user supplied", "", "sometoken"),
            ("no token supplied", "some user", ""),
        ],
        name_func=get_test_case_name_without_index,
    )
    def test_it_is_not_used_when_no(self, _name, username, token):
        try:
            warnings.simplefilter("ignore", category=RuntimeWarning)
            self._init_with_user_name_token_and_test_auth(username, token, None)
        finally:
            warnings.resetwarnings()

    def test_it_displays_warning_when_partial_credentials_supplied(self):
        with self.assertWarnsRegex(RuntimeWarning, ".*improperly configured.*"):
            self._init_with_user_name_token_and_test_auth("some username no token", "")

    @parameterized.expand(
        [
            ("no user or token supplied", "", ""),
            ("both user and token supplier", "some user", "some token"),
        ],
        name_func=get_test_case_name_without_index,
    )
    def test_it_displays_no_warnings_when(self, _name, username, token):
        with warnings.catch_warnings(record=True) as warnings_list:
            self._init_with_user_name_token_and_test_auth(username, token)
            self.assertEqual(len(warnings_list), 0)

    def test_it_is_used_when_credentials_supplied(self):
        username_token = ("some username", "some token")
        self._init_with_user_name_token_and_test_auth(*username_token, username_token)
