from pathlib import Path

import pytest
import toml
from delfino.constants import PYPROJECT_TOML_FILENAME
from delfino.models.pyproject_toml import Poetry, PyprojectToml


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def pyproject_toml(project_root) -> PyprojectToml:
    return PyprojectToml(**toml.load(project_root / PYPROJECT_TOML_FILENAME))


@pytest.fixture(scope="session")
def poetry(pyproject_toml) -> Poetry:
    assert pyproject_toml.tool.poetry
    return pyproject_toml.tool.poetry
