from typing import List

import pytest

from issuewatcher import AssertGitHubIssue

# False positive caused by pytest fixtures and class use
# pylint: disable=too-few-public-methods


class TestRepositoryAttributeHandling:
    @staticmethod
    @pytest.mark.parametrize(
        "constructor_arguments",
        [
            pytest.param([""], id="has no slashes"),
            pytest.param(["//"], id="has too many slashes"),
        ],
    )
    def test_it_raises_error_when_repository_id(constructor_arguments: List):
        with pytest.raises(ValueError):
            AssertGitHubIssue(*constructor_arguments)
