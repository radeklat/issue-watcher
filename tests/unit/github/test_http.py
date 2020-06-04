from unittest.mock import MagicMock

import pytest
from requests import HTTPError

from issuewatcher import AssertGitHubIssue
from tests.unit.github.constants import CURRENT_NUMBER_OF_RELEASES, ISSUE_NUMBER
from tests.unit.github.mocking import (
    set_issue_state,
    set_limit_exceeded,
    set_number_of_releases_to,
)


class TestHttpErrorRaising:
    _GENERIC_ERROR_MESSAGE_PATTERN = ".*Request to GitHub Failed.*"

    def test_it_raises_when_status_not_200_in_state_check(
        self, assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_issue_state(requests_mock, "open", 500)

        with pytest.raises(HTTPError, match=self._GENERIC_ERROR_MESSAGE_PATTERN):
            assert_github_issue_no_cache.is_open(ISSUE_NUMBER)

    def test_it_raises_when_status_not_200_in_releases_check(
        self, assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_number_of_releases_to(requests_mock, CURRENT_NUMBER_OF_RELEASES, 500)

        with pytest.raises(HTTPError, match=self._GENERIC_ERROR_MESSAGE_PATTERN):
            assert_github_issue_no_cache.current_release(CURRENT_NUMBER_OF_RELEASES)

    @staticmethod
    def test_it_raises_with_info_about_rate_limit_when_exceeded(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_limit_exceeded(requests_mock)

        with pytest.raises(HTTPError, match=".*Current quota:.*"):
            assert_github_issue_no_cache.is_open(ISSUE_NUMBER)
