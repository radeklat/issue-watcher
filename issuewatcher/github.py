from enum import Enum
from unittest import TestCase

import requests


class GitHubIssueState(Enum):
    open = "open"
    closed = "closed"


class GitHubIssueTestCase(TestCase):
    _URL_API: str = "https://api.github.com"
    _URL_WEB: str = "https://github.com"
    _OWNER: str = ""
    _REPOSITORY: str = ""

    def assert_github_issue_is_state(
        self, issue_number: int, expected_state: GitHubIssueState, msg: str = ""
    ) -> None:
        for attribute in ["_OWNER", "_REPOSITORY"]:
            if not getattr(self, attribute):
                raise RuntimeError(
                    f"Attribute '{attribute}' on class '{self.__class__.__name__}' must "
                    f"be set."
                )

        issue_identifier = f"{self._OWNER}/{self._REPOSITORY}/issues/{issue_number}"

        # Response documented at https://developer.github.com/v3/issues/
        response = requests.get(f"{self._URL_API}/repos/{issue_identifier}").json()
        issue_title = response["title"]

        if msg:
            msg = f" {msg}"

        self.assertEqual(
            response["state"],
            expected_state.value,
            msg=f"GitHub issue #{issue_number} '{issue_title}' is no longer "
            f"{expected_state.value}.{msg} Visit "
            f"{self._URL_WEB}/{self._OWNER}/{self._REPOSITORY}/issues/{issue_number}.",
        )

    def assert_github_issue_is_open(self, issue_number: int, msg: str = "") -> None:
        self.assert_github_issue_is_state(issue_number, GitHubIssueState.open, msg)

    def assert_github_issue_is_closed(self, issue_number: int, msg: str = "") -> None:
        self.assert_github_issue_is_state(issue_number, GitHubIssueState.closed, msg)

    def assert_no_new_release_is_available(self, expected_number_of_releases: int) -> None:
        """
        Checks number of releases of watched repository. Useful when issue is fixed (closed)
        but not released yet. This assertion will fail when the number of releases does not
        match.
        """
        releases_url = (
            f"{self._URL_API}/repos/{self._OWNER}/{self._REPOSITORY}/git/refs/tags"
        )
        releases = requests.get(releases_url).json()
        actual_release_count = len(releases)

        self.assertFalse(
            expected_number_of_releases > actual_release_count,
            f"This test case seems improperly configured. Expected "
            f"{expected_number_of_releases} releases but repository reports "
            f"{actual_release_count} available releases at the moment. Set the "
            f"expected number of releases to the current number of releases "
            f"({actual_release_count}). Visit {self._URL_WEB}/{self._OWNER}/"
            f"{self._REPOSITORY}/releases to see all releases.",
        )

        self.assertTrue(
            actual_release_count <= expected_number_of_releases,
            f"New release of {self._OWNER}/{self._REPOSITORY} is available. Expected "
            f"{expected_number_of_releases} releases but {actual_release_count} are now "
            f"available. Visit {self._URL_WEB}/{self._OWNER}/{self._REPOSITORY}/releases.",
        )
