import pytest

from issuewatcher import AssertGitHubIssue
from tests.unit.github.constants import CLOSED_ISSUE_NUMBER, OPEN_ISSUE_NUMBER


class TestChecksLive:
    @staticmethod
    def test_open_issue_check_fails_when_closed(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        with pytest.raises(AssertionError):
            try:
                assert_github_issue_no_cache.is_open(CLOSED_ISSUE_NUMBER, "Custom message.")
            except AssertionError as ex:
                print(ex)
                raise ex

    @staticmethod
    def test_open_issue_check_does_not_fail_when_open(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        assert_github_issue_no_cache.is_open(OPEN_ISSUE_NUMBER)

    @staticmethod
    def test_closed_issue_check_fails_when_open(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        with pytest.raises(AssertionError):
            assert_github_issue_no_cache.is_closed(OPEN_ISSUE_NUMBER)

    @staticmethod
    def test_closed_issue_check_does_not_fail_when_closed(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        assert_github_issue_no_cache.is_closed(CLOSED_ISSUE_NUMBER)

    @staticmethod
    def test_release_number_check_fails_when_new_releases_available(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        with pytest.raises(AssertionError, match=".*New release of .*") as ex:
            assert_github_issue_no_cache.current_release(0)

        print(ex)  # for quick grab of string for documentation

    @staticmethod
    def test_version_check_fails_when_available(
        assert_github_issue_no_cache: AssertGitHubIssue
    ):
        with pytest.raises(AssertionError, match="Release '2\\.0\\.0' of") as ex:
            assert_github_issue_no_cache.fixed_in(
                "2.0.0", pattern="releases/(?P<version>.*)"
            )

        print(ex)  # for quick grab of string for documentation
