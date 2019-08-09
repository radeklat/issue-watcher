from os.path import abspath, dirname, isfile, join
from shutil import rmtree
from subprocess import DEVNULL, call
from unittest import TestCase

from issuewatcher import APPLICATION_NAME, __version__ as app_version

SOURCES_ROOT = abspath(join(dirname(__file__), "..", ".."))

UNDERSCORED_APPLICATION_NAME = APPLICATION_NAME.replace("-", "_")

BUILD_ARTEFACTS = [
    join(SOURCES_ROOT, folder)
    for folder in ["dist", "build", UNDERSCORED_APPLICATION_NAME + ".egg-info"]
]


def cleanup_build_artefacts():
    for folder in BUILD_ARTEFACTS:
        rmtree(folder, ignore_errors=True)


class BuildProcess(TestCase):
    def setUp(self):
        cleanup_build_artefacts()
        self._build_return_code = call(
            ["python", "setup.py", "sdist", "bdist_wheel"], stdout=DEVNULL, stderr=DEVNULL
        )
        self.addCleanup(cleanup_build_artefacts)

    def test_it_builds_sources(self):
        self.assertEqual(0, self._build_return_code)

    def assert_file_is_build(self, suffix, replace_hyphens=False):
        app_name = UNDERSCORED_APPLICATION_NAME if replace_hyphens else APPLICATION_NAME
        filename = join(BUILD_ARTEFACTS[0], f"{app_name}-{app_version}{suffix}")

        self.assertTrue(
            isfile(filename), msg=f"File '{filename}' does not exist or is not a file."
        )

    def test_it_creates_whl_file(self):
        self.assert_file_is_build("-py3-none-any.whl", replace_hyphens=True)

    def test_it_creates_tar_file(self):
        self.assert_file_is_build(".tar.gz")
