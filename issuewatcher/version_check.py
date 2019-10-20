import platform
import warnings

import semver

from issuewatcher.constants import (
    APPLICATION_NAME,
    MAX_SUPPORTED_PYTHON_VERSION_EXCLUSIVE,
    MIN_SUPPORTED_PYTHON_VERSION_INCLUSIVE,
)


def check_python_support():
    """
    Shows warning when Python version is too high.
    :raises OSError: When Python version is too low.
    """
    current_version = platform.python_version()
    if semver.compare(current_version, MIN_SUPPORTED_PYTHON_VERSION_INCLUSIVE) < 0:
        raise OSError(
            f"Current Python version is '{current_version}' but minimum supported "
            f"Python version by '{APPLICATION_NAME}' is "
            f"{MIN_SUPPORTED_PYTHON_VERSION_INCLUSIVE}."
        )

    if semver.compare(current_version, MAX_SUPPORTED_PYTHON_VERSION_EXCLUSIVE) >= 0:
        warnings.warn(
            f"Current Python version is '{current_version}' but maximum supported "
            f"Python version by '{APPLICATION_NAME}' is "
            f"{MAX_SUPPORTED_PYTHON_VERSION_EXCLUSIVE}. Correct functionality of "
            f"this library is not guaranteed."
        )
