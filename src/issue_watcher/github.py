import os
import re
import warnings
from datetime import timedelta
from enum import Enum
from time import time
from typing import Any, Dict, List, Optional, Pattern, Tuple

import requests
from packaging.version import InvalidVersion, Version
from requests import HTTPError, Response

from issue_watcher.constants import DEFAULT_REQUESTS_TIMEOUT_SEC
from issue_watcher.temporary_cache import TemporaryCache


class GitHubIssueState(Enum):
    OPEN = "open"
    CLOSED = "closed"


class AssertGitHubIssue:
    _URL_API: str = "https://api.github.com"
    _URL_WEB: str = "https://github.com"
    _ENV_VAR_USERNAME = "GITHUB_USER_NAME"
    _ENV_VAR_TOKEN = "GITHUB_PERSONAL_ACCESS_TOKEN"
    _NO_VERSION_AVAILABLE = ""

    def __init__(self, repository_id: str):
        """Constructor.

        :param repository_id: GitHub repository ID formatted as "owner/repository name".
        :raises ValueError: When the repository ID is not two slash separated strings.
        """
        self._rate_limit_exceeded_extra_msg: str = ""
        self._auth: Optional[Tuple[str, str]] = (
            os.environ.get(self._ENV_VAR_USERNAME, ""),
            os.environ.get(self._ENV_VAR_TOKEN, ""),
        )
        if not all(self._auth):
            if any(self._auth):
                warnings.warn(
                    "issue_watcher seems to be improperly configured. Expected both "
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

        self._repository_id = repository_id
        if len(repository_id.split("/")) != 2:
            raise ValueError(
                f"repository_id must be two slash separated strings "
                f"('owner/repository name') but '{repository_id}' given."
            )

        self._cache = TemporaryCache(self._repository_id)

    def _handle_rate_limit_error(self, response: Response) -> None:
        headers = response.headers
        if not int(headers.get("X-RateLimit-Remaining", 1)):
            message = response.json()["message"]
            limit = headers.get("X-RateLimit-Limit")
            now = int(time())
            reset_delay = timedelta(seconds=int(headers.get("X-RateLimit-Reset", now)) - now)

            raise HTTPError(
                f"{message} Current quota: {limit}. Limit will reset in {reset_delay}."
                f"{self._rate_limit_exceeded_extra_msg}"
            )

    def _handle_connection_error(self, response: Response) -> None:
        self._handle_rate_limit_error(response)

        if response.status_code != 200:
            raise HTTPError(
                f"Request to GitHub Failed.\n{response.status_code} {response.reason}\n"
                f"HEADERS:\n{response.headers}\nCONTENT:\n{response.content!r}"
            )

    def is_state(self, issue_id: int, expected_state: GitHubIssueState, msg: str = "") -> None:
        """Checks state of given issue.

        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        """
        issue_identifier = f"issues/{issue_id}"

        try:
            current_state = self._cache[issue_identifier]
            pass  # pylint: disable=unnecessary-pass; this line should be covered
        except KeyError:
            # Response documented at https://developer.github.com/v3/issues/
            response: Response = requests.get(
                f"{self._URL_API}/repos/{self._repository_id}/{issue_identifier}",
                auth=self._auth,
                timeout=DEFAULT_REQUESTS_TIMEOUT_SEC,
            )
            self._handle_connection_error(response)

            current_state = response.json()["state"]
            self._cache[issue_identifier] = current_state

        if msg:
            msg = f" {msg}"

        assert current_state == expected_state.value, (
            f"GitHub issue #{issue_id} from '{self._repository_id}'"
            f" is no longer {expected_state.value}.{msg} Visit "
            f"{self._URL_WEB}/{self._repository_id}/issues/{issue_id}."
        )

    def is_open(self, issue_id: int, msg: str = "") -> None:
        """Check if give issue is open.

        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        """
        self.is_state(issue_id, GitHubIssueState.OPEN, msg)

    def is_closed(self, issue_id: int, msg: str = "") -> None:
        """Check if given issue is closed.

        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        """
        self.is_state(issue_id, GitHubIssueState.CLOSED, msg)

    def current_release(self, current_release_number: Optional[int] = None) -> None:
        """Checks number of releases of watched repository.

        Useful when issue is fixed (closed) but not released yet. This assertion
        will fail when the number of releases does not match.

        If you don't know how many releases are there at the moment, leave the
        ``current_release_number`` unset. This test will fail and show the
        current number as part of the error message.

        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        """
        releases_url = f"{self._URL_API}/repos/{self._repository_id}/git/refs/tags"

        try:
            actual_release_count = int(self._cache["release_count"])
            pass  # pylint: disable=unnecessary-pass; this line should be covered
        except (KeyError, ValueError):
            response: Response = requests.get(releases_url, auth=self._auth, timeout=DEFAULT_REQUESTS_TIMEOUT_SEC)
            self._handle_connection_error(response)

            actual_release_count = len(response.json())
            self._cache["release_count"] = str(actual_release_count)

        assert current_release_number is not None, (
            f"This test does not have any number of releases set. Current number "
            f"of releases is '{actual_release_count}'."
        )

        assert current_release_number <= actual_release_count, (
            f"This test seems improperly configured. Expected '{current_release_number}' "
            f"releases but repository reports '{actual_release_count}' available "
            f"releases at the moment. Set the current_release_number to the "
            f"current number of releases ({actual_release_count}). Visit "
            f"{self._URL_WEB}/{self._repository_id}/releases to see all releases."
        )

        assert actual_release_count <= current_release_number, (
            f"New release of '{self._repository_id}' is available. Expected "
            f"{current_release_number} releases but {actual_release_count} are now "
            f"available. Visit {self._URL_WEB}/{self._repository_id}/releases."
        )

    @staticmethod
    def _parse_version_number(string: str, pattern: Pattern[str]) -> Optional[Version]:
        match = pattern.match(string.replace("refs/tags/", ""))
        if not match:
            return None
        try:
            return Version(match.group("version"))
        except InvalidVersion:
            return None

    def _ordered_version_numbers(self, tags: List[Dict[str, Any]], pattern: str) -> List[Version]:
        version_pattern = re.compile(pattern)
        return sorted(
            (
                version
                for version in (self._parse_version_number(item["ref"], version_pattern) for item in tags)
                if version is not None
            ),
            reverse=True,
        )

    def fixed_in(self, version: Optional[str] = None, pattern: str = "(?P<version>.*)") -> None:
        """Checks if there is a release with higher or equal version number in the watched repository.

        Useful when issue is fixed (closed), not yet released but the maintainer
        has stated in which version it will be released. This assertion will fail when the
        expected version or higher is available.

        Git tags are used as version numbers and are interpreted according to PEP 440
        (https://www.python.org/dev/peps/pep-0440/). Anything that does not resemble a
        valid version number will be ignored. To parse git tags that contain version
        numbers, use the ``pattern`` argument.

        :param version: The lowest version number to trigger an ``AssertionError``.
        :param pattern: Use for parsing version number out of a git tag. The value is a
            regular expression acceptable by :py:func:`re.compile`. It is expected that the
            version is wrapped in a group named ``version``.

            Example: To match version number ``2.3.4`` in ``releases/2.3.4``, use
            ``pattern="releases/(?P<version>.*)"``. Note that :py:func:`re.match` is used
            internally so the string must be matched from the beginning.

            If you would like to test the version parsing, leave the ``version`` parameter
            unset. The test will fail and show the latest version as part of the error
            message.

        :raises requests.HTTPError: When response status code from GitHub is not 200.
        :raises AssertionError: When test fails.
        :raises ValueError: When ``pattern`` does not contain correct group.
        """
        releases_url = f"{self._URL_API}/repos/{self._repository_id}/git/refs/tags"

        if "(?P<version>" not in pattern:
            raise ValueError("The 'pattern' parameter must contain a group '(?P<version>…)'.")

        try:
            latest_version = Version(self._cache["latest_version"])
            pass  # pylint: disable=unnecessary-pass; this line should be covered
        except (KeyError, ValueError):
            response: Response = requests.get(releases_url, auth=self._auth, timeout=DEFAULT_REQUESTS_TIMEOUT_SEC)
            self._handle_connection_error(response)

            versions = self._ordered_version_numbers(response.json(), pattern)
            assert versions, "No tags with a valid semantic versions were found in the repository."
            latest_version = versions[0]

            self._cache["latest_version"] = str(latest_version)

        assert (
            version is not None
        ), f"This test does not have expected version number set. Latest version is '{latest_version}'."

        awaiting_version = Version(version)

        assert latest_version < awaiting_version, (
            f"Release '{version}' of '{self._repository_id}' is available. Latest version "
            f"is '{latest_version}'. Visit {self._URL_WEB}/{self._repository_id}/releases."
        )
