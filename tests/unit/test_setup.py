from pathlib import Path
from shutil import rmtree
from subprocess import call

import pytest
from delfino.models import Poetry


def cleanup_build_artefacts(project_root: Path, app_name: str):
    for folder in ["dist", "build", app_name.replace("-", "_") + ".egg-info"]:
        rmtree(project_root / folder, ignore_errors=True)


@pytest.fixture(scope="session")
def build_return_code(poetry, project_root):
    cleanup_build_artefacts(project_root, poetry.name)

    try:
        yield call(["poetry", "build"])
    finally:
        cleanup_build_artefacts(project_root, poetry.name)


class TestBuildProcess:
    @staticmethod
    def test_it_builds_sources(build_return_code):
        assert build_return_code == 0

    @staticmethod
    def assert_file_is_build(project_root: Path, poetry: Poetry, suffix: str):
        app_name = poetry.name.replace("-", "_")
        filename = project_root / "dist" / f"{app_name}-{poetry.version}{suffix}"

        assert filename.is_file(), f"File '{filename}' does not exist or is not a file."

    def test_it_creates_whl_file(self, poetry, project_root):
        self.assert_file_is_build(project_root, poetry, "-py3-none-any.whl")

    def test_it_creates_tar_file(self, poetry, project_root):
        self.assert_file_is_build(project_root, poetry, ".tar.gz")
