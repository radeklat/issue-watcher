import re
from unittest.mock import MagicMock

import pytest

from issue_watcher import AssertGitHubIssue
from tests.unit.github.mocking import set_git_tags_to


class TestReleaseVersionCheck:
    @staticmethod
    @pytest.mark.parametrize(
        "latest_version",
        [
            pytest.param("2.0.0", id="exact match"),
            pytest.param("2.0.0+1", id="build metadata above expected"),
            pytest.param("2.0.1", id="patch number above expected"),
            pytest.param("2.1.0", id="minor number above expected"),
            pytest.param("3.0.0", id="major number above expected"),
        ],
    )
    def test_it_fails_when_latest_version_is(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock, latest_version: str
    ):
        set_git_tags_to(requests_mock, [latest_version])
        with pytest.raises(AssertionError, match=f"Release '2\\.0\\.0' of.*'{re.escape(latest_version)}'"):
            assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    def test_it_fails_when_latest_version_high_enough_but_first_is_tag_is_not(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_git_tags_to(requests_mock, ["1.0.0", "3.0.0"])
        with pytest.raises(AssertionError, match="Release '2\\.0\\.0' of.*'3\\.0\\.0'"):
            assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    def test_it_ignores_invalid_version_numbers(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_git_tags_to(requests_mock, ["not_a_release", "1.0.0", "releases/3.0.0"])
        assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    @pytest.mark.parametrize(
        "latest_version",
        [
            pytest.param("2.0.0-alpha", id="pre-release above expected"),
            pytest.param("2.0.0-alpha.1", id="numbered pre-release above expected"),
            pytest.param("2.0.0-alpha+1", id="pre-release and build metadata above expected"),
            pytest.param("2.0.0a", id="non-semantic pre-release above expected"),
            pytest.param("2.0.0a0", id="non-semantic numbered pre-release above expected"),
            pytest.param("1.0.0", id="below expected"),
        ],
    )
    def test_it_does_not_fail_when_latest_version_is(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock, latest_version: str
    ):
        set_git_tags_to(requests_mock, [latest_version])
        assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    @pytest.mark.parametrize(
        "version",
        [
            pytest.param("releases/2.0.1", id="releases/2.0.1"),
            pytest.param("not_a_release_tag", id="not_a_release_tag"),
        ],
    )
    def test_it_ignores_invalid_version_tags(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock, version: str
    ):
        set_git_tags_to(requests_mock, [version, "1.0.0"])
        assert_github_issue_no_cache.fixed_in("2.0.0")

    @staticmethod
    def test_it_shows_current_release_number_if_none_given(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_git_tags_to(requests_mock, ["2.0.0"])
        with pytest.raises(
            AssertionError, match=".*test does not have expected version number set.*version is.*2\\.0\\.0"
        ):
            assert_github_issue_no_cache.fixed_in()

    @staticmethod
    def test_it_parses_out_version_specified_by_pattern(
        assert_github_issue_no_cache: AssertGitHubIssue, requests_mock: MagicMock
    ):
        set_git_tags_to(requests_mock, ["releases/3.0.0", "1.0.0", "not_a_release_tag", "releases/not_a_version"])
        with pytest.raises(AssertionError, match="Release '2\\.0\\.0' of.*'3\\.0\\.0'"):
            assert_github_issue_no_cache.fixed_in("2.0.0", pattern="releases/(?P<version>.*)")

    @staticmethod
    def test_it_refuses_pattern_without_a_group(
        assert_github_issue_no_cache: AssertGitHubIssue,
    ):
        with pytest.raises(ValueError, match=".*group.*"):
            assert_github_issue_no_cache.fixed_in("2.0.0", pattern="no_group")
