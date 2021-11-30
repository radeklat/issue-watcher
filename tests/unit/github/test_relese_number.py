from unittest.mock import MagicMock

import pytest

from issue_watcher import AssertGitHubIssue
from tests.unit.github.constants import CURRENT_NUMBER_OF_RELEASES
from tests.unit.github.mocking import set_number_of_releases_to


class TestReleaseNumberCheck:
    @staticmethod
    def test_it_fails_when_new_releases_available(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_number_of_releases_to(requests_mock, CURRENT_NUMBER_OF_RELEASES + 1)
        with pytest.raises(AssertionError, match="New release of .*"):
            assert_github_issue_no_cache.current_release(CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_does_not_fail_when_expected_releases_available(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_number_of_releases_to(requests_mock, CURRENT_NUMBER_OF_RELEASES)
        assert_github_issue_no_cache.current_release(CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_checks_if_release_number_is_properly_configured(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_number_of_releases_to(requests_mock, CURRENT_NUMBER_OF_RELEASES - 1)
        with pytest.raises(AssertionError, match=".*improperly configured.*"):
            assert_github_issue_no_cache.current_release(CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_shows_current_release_number_if_none_given(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_number_of_releases_to(requests_mock, 1)
        with pytest.raises(
            AssertionError, match=".*test does not have any number of releases set.*" "number of releases is '[0-9]+'"
        ):
            assert_github_issue_no_cache.current_release()
