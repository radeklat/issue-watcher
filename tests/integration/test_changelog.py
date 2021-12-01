from os.path import dirname, join

import pytest

from issue_watcher import __version__


@pytest.fixture(scope="module")
def changelog() -> str:
    with open(join(dirname(__file__), "../../CHANGELOG.md"), "r", encoding="utf-8") as file:
        return file.read()


class TestChangeLog:
    @staticmethod
    def should_have_current_version_as_a_header(changelog: str):
        assert f"## [{__version__}] - " in changelog
