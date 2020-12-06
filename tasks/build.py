"""Type checking on source code."""

import shutil

from invoke import task

from tasks.utils import PROJECT_INFO, print_header


@task()
def build(ctx):
    print_header("Running build", icon="🔨")

    print("Cleanup the 'build' directory")
    shutil.rmtree("build", ignore_errors=True)

    ctx.run("python setup.py sdist bdist_wheel", pty=True, env={"PYTHONPATH": PROJECT_INFO.source_directory})

    print_header("Check PyPI description", icon="👀", level=2)
    ctx.run("twine check dist/*")
