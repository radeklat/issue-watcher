from unittest import TestCase

from parameterized import parameterized

import issuewatcher
from tests.helpers.parameterized import get_test_case_name_without_index


class LibraryTopLevelExports(TestCase):
    @parameterized.expand(
        ["GitHubIssueTestCase", "GitHubIssueState"],
        name_func=get_test_case_name_without_index,
    )
    def test_it_contains(self, name):
        self.assertTrue(
            hasattr(issuewatcher, name), f"'{name}' is not exported on top level."
        )
