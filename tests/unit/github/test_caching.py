from contextlib import contextmanager
from time import perf_counter

import pytest

from issuewatcher import AssertGitHubIssue
from tests.unit.github.constants import CLOSED_ISSUE_NUMBER, REPOSITORY_ID

# False positive caused by pytest fixtures and class use
# pylint: disable=redefined-outer-name


@contextmanager
def _timer():
    start = perf_counter()
    try:
        yield
    finally:
        print(f"Executed in {(perf_counter() - start) * 1000000:.3f}us")


@pytest.fixture()
def assert_github_issue_caching():
    assert_github_issue = AssertGitHubIssue(REPOSITORY_ID)

    # first call can be cache miss
    assert_github_issue.is_closed(CLOSED_ISSUE_NUMBER)
    try:
        assert_github_issue.current_release(0)
    except AssertionError:
        pass

    assert_github_issue.fixed_in("0.0.0")

    return assert_github_issue


class TestCaching:
    @staticmethod
    def test_closed_issue_check_does_not_fail_when_closed(
        assert_github_issue_caching: AssertGitHubIssue
    ):
        with _timer():
            assert_github_issue_caching.is_closed(CLOSED_ISSUE_NUMBER)

    @staticmethod
    def test_release_check_fails_when_new_releases_available(
        assert_github_issue_caching: AssertGitHubIssue
    ):
        with _timer():
            with pytest.raises(AssertionError, match=".*New release of .*"):
                assert_github_issue_caching.current_release(0)

    @staticmethod
    def test_version_check_fails_when_available(
        assert_github_issue_caching: AssertGitHubIssue
    ):
        with _timer():
            assert_github_issue_caching.fixed_in(
                "2.0.0", pattern="releases/(?P<version>.*)"
            )
