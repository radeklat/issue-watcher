"""Linting checks on source code."""

import os
from itertools import groupby
from pathlib import Path
from typing import List, Optional

from invoke import Context, task

from tasks.utils import (
    PROJECT_INFO,
    ensure_reports_dir,
    format_messages,
    paths_to_str,
    print_header,
    read_contents,
    to_pathlib_path,
)

PYLINT_CONFIG_SOURCE_FPATH = Path(".pylintrc")
PYLINT_CONFIG_TESTS_FPATH = PROJECT_INFO.tests_directory / ".pylintrc"

REPORT_PYDOCSTYLE_FPATH = PROJECT_INFO.reports_directory / "pydocstyle-report.log"
REPORT_PYCODESTYLE_FPATH = PROJECT_INFO.reports_directory / "pycodestyle-report.log"
REPORT_PYLINT_SOURCE_FPATH = PROJECT_INFO.reports_directory / "pylint-report.log"
REPORT_PYLINT_TESTS_FPATH = PROJECT_INFO.reports_directory / "pylint-report-tests.log"


@task(iterable=["path"])
def lint_docstyle(ctx, path=None):
    _lint_docstyle(ctx, path)


def _lint_docstyle(ctx: Context, path: Optional[List[str]] = None):
    """Run docstring linting on source code.

    Docstring linting is done via pydocstyle. The pydocstyle config can be found in the `.pydocstyle` file.
    This ensures compliance with PEP 257, with a few exceptions. Note that pylint also carries out additional
    docstyle checks.

    Args:
        ctx: Context
        path: Path override. Run tests only on given paths.
    """
    print_header("documentation style", level=2)
    ensure_reports_dir()

    paths = to_pathlib_path(
        path, [PROJECT_INFO.source_directory, PROJECT_INFO.tests_directory, PROJECT_INFO.tasks_directory]
    )

    try:
        ctx.run(f"pydocstyle {paths_to_str(paths)} > {REPORT_PYDOCSTYLE_FPATH}")
    finally:
        if os.path.exists(REPORT_PYDOCSTYLE_FPATH):
            format_messages(read_contents(REPORT_PYDOCSTYLE_FPATH))


@task(iterable=["path"])
def lint_pycodestyle(ctx, path=None):
    _lint_pycodestyle(ctx, path)


def _lint_pycodestyle(ctx: Context, path: Optional[List[str]] = None):
    """Run PEP8 checking on code; this includes primary code (source) and secondary code (tests, tasks, etc.).

    PEP8 checking is done via pycodestyle.

    Args:
        ctx: Context
        path: Path override. Run tests only on given paths.
    """
    # Why pycodestyle and pylint? So far, pylint does not check against every convention in PEP8. As pylint's
    # functionality grows, we should move all PEP8 checking to pylint and remove pycodestyle
    print_header("code style (PEP8)", level=2)
    ensure_reports_dir()

    paths = to_pathlib_path(
        path, [PROJECT_INFO.source_directory, PROJECT_INFO.tests_directory, PROJECT_INFO.tasks_directory]
    )

    try:
        ctx.run(
            f"pycodestyle --ignore=E501,W503,E231 --exclude=.svn,CVS,.bzr,.hg,.git,__pycache__,.tox,*_config_parser.py "
            f"{paths_to_str(paths)} > {REPORT_PYCODESTYLE_FPATH}"
        )
        # Ignores explained:
        # - E501: Line length is checked by PyLint
        # - W503: Disable checking of "Line break before binary operator". PEP8 recently (~2019) switched to
        #         "line break before the operator" style, so we should permit this usage.
        # - E231: "missing whitespace after ','" is a false positive. Handled by black formatter.
    finally:
        if os.path.exists(REPORT_PYCODESTYLE_FPATH):
            format_messages(read_contents(REPORT_PYCODESTYLE_FPATH))


def run_pylint(ctx, source_dirs: List[Path], report_path: Path, pylintrc_fpath: Path):
    """Run pylint with a given configuration on a given code tree and output to a given report file."""
    print_header(paths_to_str(source_dirs, ", "), level=3)
    ensure_reports_dir()
    try:
        # pylint won't lint all `.py` files unless they're in a package (`__init__.py` must exist in the same dir)
        # see https://github.com/PyCQA/pylint/issues/352
        # instead of calling pylint directly, here we use `find` to search for all `py` files, regardless of being in
        # # a package
        ctx.run(
            f"export PYTHONPATH={PROJECT_INFO.source_directory}\n"
            f'find {paths_to_str(source_dirs)} -type f -name "*.py" | '
            f"xargs pylint --rcfile {pylintrc_fpath} > {report_path}"
        )
    finally:
        if os.path.exists(str(report_path)):
            format_messages(read_contents(report_path), "^.*rated at 10.00/10.*$")


@task(iterable=["path"])
def lint_pylint(ctx, path=None):
    _lint_pylint(ctx, path)


def _lint_pylint(ctx: Context, path: Optional[List[str]] = None):
    """Run pylint on code; this includes primary code (source) and secondary code (tests, tasks, etc.).

    The bulk of our code conventions are enforced via pylint. The pylint config can be found in the `.pylintrc` file.

    Args:
        ctx: Context
        path: Path override. Run tests only on given paths.
    """
    print_header("pylint", level=2)

    paths = to_pathlib_path(
        path, [PROJECT_INFO.source_directory, PROJECT_INFO.tests_directory, PROJECT_INFO.tasks_directory]
    )
    src = PROJECT_INFO.source_directory
    grouped_paths = groupby(paths, lambda current_path: src in current_path.parents or current_path == src)

    for is_source, group in grouped_paths:
        if is_source:
            run_pylint(ctx, list(group), REPORT_PYLINT_SOURCE_FPATH, PYLINT_CONFIG_SOURCE_FPATH)
        else:
            run_pylint(ctx, list(group), REPORT_PYLINT_TESTS_FPATH, PYLINT_CONFIG_TESTS_FPATH)


@task(iterable=["path"])
def lint(ctx, path=None):
    """Run linting on the entire code base (source code, tasks, tests).

    Args:
        ctx (invoke.Context): Context
        path (Optional[List[str]]): Path override. Run tests only on given paths.
    """
    print_header("Linting", icon="🔎")

    # These cannot be pre/post tasks because arguments cannot be passed through.
    _lint_pylint(ctx, path)
    _lint_pycodestyle(ctx, path)
    _lint_docstyle(ctx, path)
