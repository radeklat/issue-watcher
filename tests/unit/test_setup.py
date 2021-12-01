from os.path import abspath, dirname, isfile, join
from shutil import rmtree
from subprocess import call

import pytest

from issue_watcher.constants import APPLICATION_NAME
from issue_watcher.constants import __version__ as app_version

SOURCES_ROOT = abspath(join(dirname(__file__), "..", ".."))

UNDERSCORED_APPLICATION_NAME = APPLICATION_NAME.replace("-", "_")

BUILD_ARTEFACTS = [
    join(SOURCES_ROOT, folder) for folder in ["dist", "build", UNDERSCORED_APPLICATION_NAME + ".egg-info"]
]

# pylint: disable=redefined-outer-name


def cleanup_build_artefacts():
    for folder in BUILD_ARTEFACTS:
        rmtree(folder, ignore_errors=True)


@pytest.fixture(scope="session")
def build_return_code():
    cleanup_build_artefacts()

    try:
        yield call(["poetry", "build"])
    finally:
        cleanup_build_artefacts()


class TestBuildProcess:
    @staticmethod
    def test_it_builds_sources(build_return_code):
        assert build_return_code == 0

    @staticmethod
    def assert_file_is_build(suffix, replace_hyphens=False):
        app_name = UNDERSCORED_APPLICATION_NAME if replace_hyphens else APPLICATION_NAME
        filename = join(BUILD_ARTEFACTS[0], f"{app_name}-{app_version}{suffix}")

        assert isfile(filename), f"File '{filename}' does not exist or is not a file."

    def test_it_creates_whl_file(self):
        self.assert_file_is_build("-py3-none-any.whl", replace_hyphens=True)

    def test_it_creates_tar_file(self):
        self.assert_file_is_build(".tar.gz")
