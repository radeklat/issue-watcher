"""
Runnable tasks for this project. Project tooling for build, distribute, etc.

Invoked with the Python `invoke` framework. Tasks should be invoked from the project root directory, not
the `tasks` dir.

Task code is for tooling only and should strictly not be mixed with `src` code.
"""

from invoke import Collection

from tasks.format import run_format
from tasks.lint import lint, lint_pycodestyle, lint_docstyle, lint_pylint
from tasks.utils import switch_python_version
from tasks.test import coverage_open, coverage_report, test, test_unit
from tasks.typecheck import typecheck
from tasks.verify_all import verify_all
from tasks.build import build

namespace = Collection()  # pylint: disable=invalid-name

namespace.add_task(run_format)
namespace.add_task(typecheck)

namespace.add_task(lint)
namespace.add_task(lint_pylint)
namespace.add_task(lint_pycodestyle)
namespace.add_task(lint_docstyle)

namespace.add_task(test_unit)
namespace.add_task(test)
namespace.add_task(coverage_report)
namespace.add_task(coverage_open)

namespace.add_task(verify_all)

namespace.add_task(build)
namespace.add_task(switch_python_version)
