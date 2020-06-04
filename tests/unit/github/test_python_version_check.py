from contextlib import ExitStack
from unittest.mock import patch

import pytest

from issuewatcher import AssertGitHubIssue
from tests.unit.github.constants import REPOSITORY_ID

# False positive caused by pytest fixtures and class use
# pylint: disable=redefined-outer-name, too-few-public-methods


@pytest.fixture(scope="function")
def python_version_mock(request):
    patcher = patch("platform.python_version", return_value=request.param)

    try:
        yield patcher.start()
    finally:
        patcher.stop()


class TestPythonSupportChecks:
    @staticmethod
    @pytest.mark.parametrize(
        "python_version_mock,expectation",
        [
            pytest.param(
                "3.5.0", pytest.raises(OSError), id="OSError when Python version is too low"
            ),
            pytest.param(
                "3.6.0", ExitStack(), id="nothing when Python version is in range"
            ),
            pytest.param(
                "3.9.0", pytest.warns(Warning), id="Warning when Python version is too high"
            ),
        ],
        indirect=["python_version_mock"],
    )
    def test_it_raises(python_version_mock, expectation):  # pylint: disable=unused-argument
        with expectation:
            AssertGitHubIssue(REPOSITORY_ID)
