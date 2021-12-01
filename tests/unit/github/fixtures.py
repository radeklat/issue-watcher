from unittest.mock import patch

import pytest

from issue_watcher import AssertGitHubIssue
from tests.unit.github.constants import REPOSITORY_ID


@pytest.fixture()
def assert_github_issue_no_cache():
    with patch.dict("os.environ", {"CACHE_INVALIDATION_IN_SECONDS": "0"}):
        assert_github_issue = AssertGitHubIssue(REPOSITORY_ID)

    return assert_github_issue


@pytest.fixture()
def requests_mock():
    requests_patcher = patch("issue_watcher.github.requests")

    try:
        yield requests_patcher.start()
    finally:
        requests_patcher.stop()
