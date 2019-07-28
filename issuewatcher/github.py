from enum import Enum
from unittest import TestCase

import requests


class GithubIssueState(Enum):
    open = "open"
    closed = "closed"


class GithubIssueTestCase(TestCase):
    _URL_API: str = "https://api.github.com"
    _URL_WEB: str = "https://github.com"
    _OWNER: str = ""
    _REPOSITORY: str = ""

    def assert_github_issue_is_state(
        self, issue_number: int, expected_state: GithubIssueState, msg: str = ""
    ) -> None:
        issue_identifier = f"{self._OWNER}/{self._REPOSITORY}/issues/{issue_number}"

        # Response documented at https://developer.github.com/v3/issues/
        current_state = requests.get(f"{self._URL_API}/repos/{issue_identifier}").json()[
            "state"
        ]

        if msg:
            msg = f" {msg} "

        self.assertEqual(
            current_state,
            expected_state.value,
            msg=f"GitHub issue {self._URL_WEB}/{issue_identifier} is no longer "
            f"{expected_state.value}.{msg}Visit "
            f"{self._URL_WEB}/{self._OWNER}/{self._REPOSITORY}/issues/{issue_number}.",
        )

    def assert_github_issue_is_open(self, issue_number: int, msg: str = "") -> None:
        self.assert_github_issue_is_state(issue_number, GithubIssueState.open, msg)

    def assert_github_issue_is_closed(self, issue_number: int, msg: str = "") -> None:
        self.assert_github_issue_is_state(issue_number, GithubIssueState.closed, msg)

    def assert_no_new_release_is_available(self, current_number_of_releases: int) -> None:
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

        self.assertLessEqual(
            actual_release_count,
            current_number_of_releases,
            f"New release of {self._OWNER}/{self._REPOSITORY} is available. Expected "
            f"{current_number_of_releases} releases but {actual_release_count} are now "
            f"available. Visit {self._URL_WEB}/{self._OWNER}/{self._REPOSITORY}/releases.",
        )
