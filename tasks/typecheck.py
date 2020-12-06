"""Type checking on source code."""
from itertools import groupby
from pathlib import Path
from typing import List

from invoke import Result, task
from termcolor import cprint

from tasks.utils import PROJECT_INFO, ensure_reports_dir, paths_to_str, print_header, to_pathlib_path

_REPORTS_DIR = PROJECT_INFO.reports_directory / "typecheck/junit.xml"


def _handle_unexpected_pass(expected_to_fail: bool, result: Result, path: str):
    if expected_to_fail and not result.failed:
        result.exited = 1  # force failure
        cprint(
            f"\nThis folder was expected to fail but no errors were found.\n\nPlease edit the "
            f"'{__file__}' file and move '{path}' from `broken_directories` to `fixed_directories`.",
            "red",
            attrs=["bold"],
        )


def _typecheck(ctx, paths: List[Path], force_typing=False):
    print_header(("Forced" if force_typing else "Optional") + " typing", level=2)

    common_flags = [
        "--show-column-numbers",
        "--show-error-codes",
        "--color-output",
        "--warn-unused-config",
        "--warn-unused-ignores",
        "--follow-imports silent",
        f"--junit-xml {_REPORTS_DIR}",
        *(["--strict", "--allow-untyped-decorators"] if force_typing else []),
        # Untyped decorators are allowed because they may be third party decorators
    ]

    ctx.run(f"set -o pipefail; mypy {' '.join(common_flags)} {paths_to_str(paths)}", pty=True)


@task(iterable=["path"])
def typecheck(ctx, path=None):
    """Run type checking on source code.

    A non-zero return code from this task indicates invalid types were discovered.

    Args:
        ctx (invoke.Context): Invoke context.
        path (Optional[List[str]]): Path override. Run tests only on given paths.
    """
    print_header("RUNNING TYPE CHECKER")

    ensure_reports_dir()

    src = PROJECT_INFO.source_directory
    paths = to_pathlib_path(path, [src, PROJECT_INFO.tests_directory, PROJECT_INFO.tasks_directory])
    grouped_paths = groupby(paths, lambda current_path: src in current_path.parents or current_path == src)

    for force_typing, group in grouped_paths:
        _typecheck(ctx, list(group), force_typing)
