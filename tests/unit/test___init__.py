import pytest

import issue_watcher


class TestLibraryTopLevelExports:  # pylint: disable=too-few-public-methods
    @staticmethod
    @pytest.mark.parametrize("name", ["AssertGitHubIssue", "GitHubIssueState"])
    def test_it_contains(name):
        assert hasattr(issue_watcher, name), f"'{name}' is not exported on top level."
