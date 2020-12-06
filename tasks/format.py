"""Type checking on source code."""

from invoke import Result, UnexpectedExit, task
from termcolor import cprint

from tasks.utils import PROJECT_INFO, ensure_pre_commit, print_header


@task(name="format", pre=[ensure_pre_commit])
def run_format(ctx, check=False, quiet=False):
    """Run black code formatter on source code.

    :param [invoke.Context] ctx: Invoke context.
    :param [bool] check: Only check formatting, don't reformat the code.
    :param [bool] quiet: Don't show progress. Only errors.

    :raises UnexpectedExit: On formatter failure.
    """
    print_header("Formatting code", icon="🖤")
    flags = []

    if check:
        flags.append("--check")

    if quiet:
        flags.append("--quiet")

    dirs = f"{PROJECT_INFO.source_directory} {PROJECT_INFO.tests_directory} {PROJECT_INFO.tasks_directory}"
    cmd = f"black {dirs} " + " ".join(flags)

    result: Result = ctx.run(cmd, pty=True, warn=True)

    if result.return_code == 1 and check:
        cprint(
            "Code was not formatted before commit. Try following:\n"
            " * Enable pre-commit hook by running `pre-commit install` in the repository.\n"
            " * Run formatter manually with `pipenv run inv format` before committing code.",
            color="red",
        )
        raise UnexpectedExit(result)

    if result.return_code > 1:
        raise UnexpectedExit(result)
