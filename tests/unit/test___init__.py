import pytest

import issuewatcher


class TestLibraryTopLevelExports:  # pylint: disable=too-few-public-methods
    @staticmethod
    @pytest.mark.parametrize("name", ["AssertGitHubIssue", "GitHubIssueState"])
    def test_it_contains(name):
        assert hasattr(issuewatcher, name), f"'{name}' is not exported on top level."
