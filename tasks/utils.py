"""General-purpose utilities for this project's pyinvoke tasks."""
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from invoke import task
from termcolor import cprint


@dataclass(frozen=True)
class ProjectInfo:
    """Information about this project."""

    source_directory: Path = Path("issuewatcher")  # top of source code tree
    tests_directory: Path = Path("tests")
    unit_tests_directory: Path = tests_directory / "unit"
    tasks_directory: Path = Path("tasks")
    reports_directory: Path = Path("reports")


PROJECT_INFO = ProjectInfo()


def ensure_reports_dir() -> None:
    """Ensures that the reports directory exists."""
    PROJECT_INFO.reports_directory.mkdir(parents=True, exist_ok=True)


def read_contents(fpath: Path, strip_newline=True) -> str:
    """Read plain text file contents as string."""
    with open(str(fpath)) as f_in:
        contents = "".join(f_in.readlines())
        if strip_newline:
            contents = contents.rstrip("\n")
        return contents


def format_messages(messages: str, success_pattern: str = "^$"):
    if re.match(success_pattern, messages, re.DOTALL):
        cprint("✔ No issues found.", "green")
    else:
        print(messages)


@task
def ensure_pre_commit(ctx):
    ctx.run("pre-commit install", pty=True, hide="both")


_HEADER_LEVEL_CHARACTERS = {1: "#", 2: "=", 3: "-"}


def print_header(text: str, level: int = 1, icon: str = ""):
    if icon:
        icon += " "

    padding_character = _HEADER_LEVEL_CHARACTERS[level]
    if os.getenv("CIRCLECI", ""):
        padding_length = 80
    else:
        padding_length = max(shutil.get_terminal_size((80, 20)).columns - (len(icon) * 2), 0)

    padding = f"\n{{:{padding_character}^{padding_length}}}\n"
    if level == 1:
        text = text.upper()
    print(padding.format(f" {icon}{text} {icon}"))


def to_pathlib_path(path: Optional[List[str]], default: Optional[List[Path]] = None) -> List[Path]:
    """Normalize optional ``path`` argument of tasks into ``List[Path]``."""
    if not path:
        return default if default else []

    return list(map(Path, path))


def paths_to_str(paths: List[Path], delimiter: str = " ") -> str:
    return delimiter.join(map(str, paths))


@task()
def switch_python_version(ctx, version):
    """Switches the local Python virtual environment to a different Python version.

    Use this to test the sub-packages with a different Python version. CI pipeline always
    checks all supported versions automatically.

    Notes:
        This task calls ``deactivate`` as a precaution for cases when the task is called
        from an active virtual environment.

    Args:
        ctx (invoke.Context): Context
        version (str): Desired Python version. You can use only MAJOR.MINOR (for example 3.6).
    """
    print_header(f"Switching to Python {version}", icon="🐍")
    ctx.run(f"source deactivate; git clean -fxd .venv && pipenv sync --python {version} -d", pty=True)
