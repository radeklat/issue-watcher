from os.path import dirname, join

import pytest

from issuewatcher import __version__


@pytest.fixture(scope="module")
def changelog() -> str:
    return open(join(dirname(__file__), "../../CHANGELOG.md"), "r").read()


class TestChangeLog:
    @staticmethod
    def should_have_current_version_as_a_header(changelog: str):
        assert f"## [{__version__}] - " in changelog
