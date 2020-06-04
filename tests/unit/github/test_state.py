from unittest.mock import MagicMock

import pytest

from issuewatcher import AssertGitHubIssue, GitHubIssueState
from tests.unit.github.constants import ISSUE_NUMBER
from tests.unit.github.mocking import set_issue_state


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
        set_issue_state(requests_mock, returned_state)

        with pytest.raises(AssertionError):
            assert_github_issue_no_cache.is_state(ISSUE_NUMBER, expected_state)

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
        set_issue_state(requests_mock, returned_state)
        assert_github_issue_no_cache.is_state(ISSUE_NUMBER, expected_state)


def _fail_open_state_check(
    assert_github_issue: AssertGitHubIssue, req_mock: MagicMock, msg: str = ""
):
    set_issue_state(req_mock, GitHubIssueState.closed.value)
    assert_github_issue.is_open(ISSUE_NUMBER, msg)


class TestFailingStateCheck:
    @staticmethod
    @pytest.mark.parametrize(
        "regexp",
        [
            pytest.param(
                f"https://github.com/radeklat/issue-watcher/issues/{ISSUE_NUMBER}",
                id="link to issue",
            ),
            pytest.param("'radeklat/issue-watcher'", id="owner and repository"),
            pytest.param("no longer open\\.", id="expected issue state"),
            pytest.param(f"#{ISSUE_NUMBER}", id="issue number"),
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
