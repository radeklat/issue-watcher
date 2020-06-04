import warnings
from typing import Callable
from unittest.mock import ANY, MagicMock, patch

import pytest
from requests import HTTPError

from issuewatcher import AssertGitHubIssue
from tests.unit.github.constants import ISSUE_NUMBER, REPOSITORY_ID
from tests.unit.github.mocking import set_issue_state, set_limit_exceeded


def noop(_: AssertGitHubIssue):
    pass


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
            set_issue_state(requests_mock, "open")
            assert_github_issue = AssertGitHubIssue(REPOSITORY_ID)
            assert_github_issue.is_open(ISSUE_NUMBER)
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
            set_limit_exceeded(requests_mock)

            with pytest.raises(HTTPError, match=".*Consider setting.*"):
                assert_github_issue.is_open(ISSUE_NUMBER)

        self._init_with_user_name_token_and_assert(requests_mock, "", "", _assertion)
