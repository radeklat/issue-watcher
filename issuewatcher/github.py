import os
import warnings
from datetime import timedelta
from enum import Enum
from time import time
from typing import Optional, Tuple

import requests
from requests import HTTPError, Response

from issuewatcher.temporary_cache import TemporaryCache


class GitHubIssueState(Enum):
    open = "open"
    closed = "closed"


class GitHubIssueTestCase:
    _URL_API: str = "https://api.github.com"
    _URL_WEB: str = "https://github.com"
    _ENV_VAR_USERNAME = "GITHUB_USER_NAME"
    _ENV_VAR_TOKEN = "GITHUB_PERSONAL_ACCESS_TOKEN"

    _OWNER: str = ""
    _REPOSITORY: str = ""

    def __init__(self, owner: Optional[str] = None, repository: Optional[str] = None):
        """
        All options for the calls can be supplied either via class attributes or
        via constructor parameters. This is for compatibility reasons:

            * Class can be sub-classed and used as a Mixin with
                :py:class:`unittest.TestCase` - use class attributes.
            * Class can use used as instance with pytest - use constructor parameters.

        All options must be supplied by either of the methods. Mixing the methods
        is not allowed. If both methods are used fully, constructor parameters
        take precedence.

        :param owner: Repository owner, matches :py:attr:`~GitHubIssueTestCase._OWNER`.
        :param repository: Repository name, matches
            :py:attr:`~GitHubIssueTestCase._REPOSITORY`.
        :raises ValueError: When not all options are supplied or method of supplying
            them is mixed.
        """
        self._rate_limit_exceeded_extra_msg: str = ""
        self._auth: Optional[Tuple[str, str]] = (
            os.environ.get(self._ENV_VAR_USERNAME, ""),
            os.environ.get(self._ENV_VAR_TOKEN, ""),
        )
        if not all(self._auth):
            if any(self._auth):
                warnings.warn(
                    "issuewatcher seems to be improperly configured. Expected both "
                    f"'{self._ENV_VAR_USERNAME}' and '{self._ENV_VAR_TOKEN}' environment "
                    "variable to be set or both unset. However, only one is set, GitHub "
                    "authentication remains disabled and API rate limiting will be "
                    "limited.",
                    RuntimeWarning,
                )
            self._auth = None
            self._rate_limit_exceeded_extra_msg = (
                f"Consider setting '{self._ENV_VAR_USERNAME}' and "
                f"'{self._ENV_VAR_TOKEN}' environment variables to turn on GitHub "
                f"authentication and raise the API rate limit. "
                f"See https://github.com/radeklat/issue-watcher#environment-variables"
            )

        if all([owner, repository]):
            self._repo_id = f"{owner}/{repository}"
        elif all([self._OWNER, self._REPOSITORY]):
            self._repo_id = f"{self._OWNER}/{self._REPOSITORY}"
        else:
            raise ValueError(
                f"Repository name and owner must be both set either via class "
                f"attributes '_OWNER' and '_REPOSITORY' or via constructor "
                f"parameters 'owner' and 'repository'."
            )

        self._cache = TemporaryCache(self._repo_id)

    def _handle_rate_limit_error(self, response: Response):
        headers = response.headers
        if not int(headers.get("X-RateLimit-Remaining", 1)):
            message = response.json()["message"]
            limit = headers.get("X-RateLimit-Limit")
            now = int(time())
            reset_delay = timedelta(
                seconds=int(headers.get("X-RateLimit-Reset", now)) - now
            )

            raise HTTPError(
                f"{message} Current quota: {limit}. Limit will reset in {reset_delay}."
                f"{self._rate_limit_exceeded_extra_msg}"
            )

    def _handle_connection_error(self, response: Response):
        self._handle_rate_limit_error(response)

        if response.status_code != 200:
            raise HTTPError(
                f"Request to GitHub Failed.\n{response.status_code} {response.reason}\n"
                f"HEADERS:\n{response.headers}\nCONTENT:\n{response.content}"
            )

    def assert_github_issue_is_state(
        self, issue_number: int, expected_state: GitHubIssueState, msg: str = ""
    ) -> None:
        """
        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        :raises RuntimeError: When :py:attr:`~GitHubIssueTestCase._OWNER` or
            :py:attr:`~GitHubIssueTestCase._REPOSITORY` is not overwritten.
        """
        issue_identifier = f"issues/{issue_number}"

        try:
            current_state = self._cache[issue_identifier]
            pass  # pylint: disable=unnecessary-pass; this line should be covered
        except KeyError:
            # Response documented at https://developer.github.com/v3/issues/
            response: Response = requests.get(
                f"{self._URL_API}/repos/{self._repo_id}/{issue_identifier}", auth=self._auth
            )
            self._handle_connection_error(response)

            current_state = response.json()["state"]
            self._cache[issue_identifier] = current_state

        if msg:
            msg = f" {msg}"

        assert current_state == expected_state.value, (
            f"GitHub issue #{issue_number} from '{self._repo_id}'"
            f" is no longer {expected_state.value}.{msg} Visit "
            f"{self._URL_WEB}/{self._repo_id}/issues/{issue_number}."
        )

    def assert_github_issue_is_open(self, issue_number: int, msg: str = "") -> None:
        """
        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        """
        self.assert_github_issue_is_state(issue_number, GitHubIssueState.open, msg)

    def assert_github_issue_is_closed(self, issue_number: int, msg: str = "") -> None:
        """
        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        """
        self.assert_github_issue_is_state(issue_number, GitHubIssueState.closed, msg)

    def assert_no_new_release_is_available(self, expected_number_of_releases: int) -> None:
        """
        Checks number of releases of watched repository. Useful when issue is fixed (closed)
        but not released yet. This assertion will fail when the number of releases does not
        match.

        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        """
        releases_url = f"{self._URL_API}/repos/{self._repo_id}/git/refs/tags"

        try:
            actual_release_count = int(self._cache["release_count"])
            pass  # pylint: disable=unnecessary-pass; this line should be covered
        except (KeyError, ValueError):
            response: Response = requests.get(releases_url, auth=self._auth)
            self._handle_connection_error(response)

            actual_release_count = len(response.json())
            self._cache["release_count"] = str(actual_release_count)

        assert expected_number_of_releases <= actual_release_count, (
            f"This test case seems improperly configured. Expected "
            f"{expected_number_of_releases} releases but repository reports "
            f"{actual_release_count} available releases at the moment. Set the "
            f"expected number of releases to the current number of releases "
            f"({actual_release_count}). Visit {self._URL_WEB}/{self._repo_id}/releases "
            f"to see all releases."
        )

        assert actual_release_count <= expected_number_of_releases, (
            f"New release of '{self._repo_id}' is available. Expected "
            f"{expected_number_of_releases} releases but {actual_release_count} are now "
            f"available. Visit {self._URL_WEB}/{self._repo_id}/releases."
        )
