from unittest.mock import patch, MagicMock

from parameterized import parameterized

from issuewatcher import GitHubIssueTestCase, GitHubIssueState


class DefaultOwnerAndRepositoryGitHubIssueTestCase(GitHubIssueTestCase):
    def setUp(self):
        requests_patcher = patch("issuewatcher.github.requests")
        self._requests_mock = requests_patcher.start()
        self.addCleanup(requests_patcher.stop)

    def _set_issue_state(self, value: str):
        json_mock = MagicMock()
        json_mock.json.return_value = {"state": value, "title": _ISSUE_TITLE}
        self._requests_mock.get.return_value = json_mock

    def _fail_open_state_check(self, msg: str = ""):
        self._set_issue_state(GitHubIssueState.closed.value)
        self.assert_github_issue_is_open(_ISSUE_NUMBER, msg)


class NoOwnerGitHubIssueTestCase(DefaultOwnerAndRepositoryGitHubIssueTestCase):
    _REPOSITORY = "issue-watcher"

    def test_it_checks_owner_is_set(self):
        with self.assertRaises(RuntimeError):
            self._fail_open_state_check()


class NoRepositoryGitHubIssueTestCase(DefaultOwnerAndRepositoryGitHubIssueTestCase):
    _OWNER = "radeklat"

    def test_it_checks_owner_is_set(self):
        with self.assertRaises(RuntimeError):
            self._fail_open_state_check()


_ISSUE_NUMBER = 123
_ISSUE_TITLE = "Sample issue title"


def get_test_case_name_without_index(test_case_func, _param_num, params):
    return f"{test_case_func.__name__}_{parameterized.to_safe_name(params[0][0])}"


class GitHubIssueStateChecksTestCase(DefaultOwnerAndRepositoryGitHubIssueTestCase):
    _OWNER = "radeklat"
    _REPOSITORY = "issue-watcher"

    @parameterized.expand(
        [
            ("open closed", GitHubIssueState.open, "closed"),
            ("closed open", GitHubIssueState.closed, "open"),
        ],
        name_func=get_test_case_name_without_index,
    )
    def test_state_check_fails_on_non_matching_state(
        self, _, expected_state, returned_state
    ):
        self._set_issue_state(returned_state)

        with self.assertRaises(AssertionError):
            self.assert_github_issue_is_state(_ISSUE_NUMBER, expected_state)

    @parameterized.expand(
        [("open", GitHubIssueState.open), ("closed", GitHubIssueState.closed)],
        name_func=get_test_case_name_without_index,
    )
    def test_state_check_does_not_fail_on_matching_state(
        self, returned_state, expected_state
    ):
        self._set_issue_state(returned_state)
        self.assert_github_issue_is_state(_ISSUE_NUMBER, expected_state)

    @parameterized.expand(
        [
            (
                "link to issue",
                f"https://github.com/radeklat/issue-watcher/issues/{_ISSUE_NUMBER}",
            ),
            ("issue title", f"'{_ISSUE_TITLE}'"),
            ("expected issue state", "no longer open\\."),
            ("issue number", f"#{_ISSUE_NUMBER}"),
        ],
        name_func=get_test_case_name_without_index,
    )
    def test_failing_state_check_contains(self, _name, regexp):
        with self.assertRaisesRegex(AssertionError, f".*{regexp}.*"):
            self._fail_open_state_check()

    def test_failing_state_check_contains_custom_message_if_one_provided(self):
        msg = "Sample custom message"
        with self.assertRaisesRegex(AssertionError, f".*open\\. {msg} Visit.*"):
            self._fail_open_state_check(msg=msg)

    def test_failing_state_check_does_not_contains_custom_message_if_none_provided(self):
        with self.assertRaisesRegex(AssertionError, f".*open\\. Visit.*"):
            self._fail_open_state_check()

    def test_open_issue_check_fails_when_closed(self):
        self._set_issue_state("closed")

        with self.assertRaises(AssertionError):
            self.assert_github_issue_is_open(_ISSUE_NUMBER)

    def test_closed_issue_check_fails_when_open(self):
        self._set_issue_state("open")

        with self.assertRaises(AssertionError):
            self.assert_github_issue_is_closed(_ISSUE_NUMBER)

    def test_open_issue_check_does_not_fail_when_open(self):
        self._set_issue_state("open")
        self.assert_github_issue_is_open(_ISSUE_NUMBER)

    def test_closed_issue_check_does_not_fail_when_closed(self):
        self._set_issue_state("closed")
        self.assert_github_issue_is_closed(_ISSUE_NUMBER)


class GitHubReleaseChecksTestCase(DefaultOwnerAndRepositoryGitHubIssueTestCase):
    _CURRENT_NUMBER_OF_RELEASES = 3

    def _set_number_or_releases_to(self, count: int):
        json_mock = MagicMock()
        json_mock.json.return_value = [{}] * count
        self._requests_mock.get.return_value = json_mock

    def test_release_number_check_fails_when_new_releases_available(self):
        self._set_number_or_releases_to(self._CURRENT_NUMBER_OF_RELEASES + 1)
        with self.assertRaisesRegex(AssertionError, "New release of .*"):
            self.assert_no_new_release_is_available(self._CURRENT_NUMBER_OF_RELEASES)

    def test_release_number_check_does_not_fail_when_expected_releases_available(self):
        self._set_number_or_releases_to(self._CURRENT_NUMBER_OF_RELEASES)
        self.assert_no_new_release_is_available(self._CURRENT_NUMBER_OF_RELEASES)

    def test_release_number_check_checks_if_release_number_is_properly_configured(self):
        self._set_number_or_releases_to(self._CURRENT_NUMBER_OF_RELEASES - 1)
        with self.assertRaisesRegex(AssertionError, ".*improperly configured.*"):
            self.assert_no_new_release_is_available(self._CURRENT_NUMBER_OF_RELEASES)
