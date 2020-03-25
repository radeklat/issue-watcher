#!/usr/bin/env bash

VERSION=3.4.2

### PROJECT DEFAULTS ###
# To override these values, use the --generate-rc-file switch and modify the generated file

ENABLE_UNITTESTS=true
ENABLE_COVERAGE=true
ENABLE_BDD=false
ENABLE_FORMATTER=true
ENABLE_TYPES=true
ENABLE_TODOS=true
ENABLE_SAFETY=true
DJANGO_AWARE=false  # makes tools Django aware, requires extra libraries

MIN_PYTHON_VERSION="3.5"
MAX_PYTHON_VERSION="3.7"
CHECK_PYTHON_PATCH_VERSION=false
MIN_PYLINT_SCORE_SOURCE=10.0
MIN_PYLINT_SCORE_TESTS=10.0

SOURCES_FOLDER='src'
TESTS_FOLDER='tests'
UNIT_TESTS_FOLDER="${TESTS_FOLDER}/unit"
BDD_TESTS_FOLDER="${TESTS_FOLDER}/features"
EXCLUDE_PATH_FROM_TESTS_REGEXP=""  # Used when searching for python files. See man of 'find -regex'.

GITHUB_UPDATE_PERSONAL_ACCESS_TOKEN=''
GITHUB_UPDATE_REPOSITORY='radeklat/python-before-push'  # <owner>/<repository>
GITHUB_UPDATE_TEST_SCRIPT='test.sh'

# To skip a file, use: GITHUB_UPDATE_SOURCES_TARGETS["..."]="" (empty string as destination)
declare -A GITHUB_UPDATE_SOURCES_TARGETS=(
    ["${GITHUB_UPDATE_TEST_SCRIPT}"]="$(basename "$0")"
    ["tests/.pylintrc"]="${TESTS_FOLDER}/.pylintrc"
    ["src/.pylintrc"]="${SOURCES_FOLDER}/.pylintrc"
    ["pyproject.toml"]="pyproject.toml"
    [".pre-commit-config.yaml"]=".pre-commit-config.yaml"
)

COVERAGE_MIN_PERCENTAGE=0
TODOS_LIMIT_PER_PERSON=10

### DON'T CHANGE ANYTHING AFTER THIS POINT ###
# Change offset here if you change the number of lines in previous section
# Check if correct with `bash test.sh --generate-rc-file`
declare -A TEST_RC_FILE_HEAD_OFFSET=( ["start"]=8 ["end"]=43 )

ROOT_FOLDER="$( cd "$( dirname "$0" )" && pwd )"
cd "${ROOT_FOLDER}"

BRED='\033[1;31m'
BGREEN='\033[1;32m'
BYELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color
TEST_RC_FILE=".testrc"
COVERAGE_FILE="${COVERAGE_FILE:-coverage.xml}"

if [[ -f ${TEST_RC_FILE} ]]; then
    echo "Using '${TEST_RC_FILE}'."
    source ${TEST_RC_FILE}
else
    echo "No '${TEST_RC_FILE}' found. Using global values. You can generate one with --generate-rc-file."
fi

# Will either produce URL that can be used as <URL>/<file> to fetch a file from Github
# or empty string if no updates are needed. Assessed by latest version from Github
# release tag vs. version in this file.
get_update_url() {
    local release_tag_prefix="releases/"
    local authorization_header=""
    local authorization_token=""

    if [[ -n ${GITHUB_UPDATE_PERSONAL_ACCESS_TOKEN} ]]; then
        authorization_header="Authorization: token ${GITHUB_UPDATE_PERSONAL_ACCESS_TOKEN}"
        authorization_token="${GITHUB_UPDATE_PERSONAL_ACCESS_TOKEN}@"
    fi

    local latest_release_tag=$(\
        curl -s -H "${authorization_header}" -X GET "https://api.github.com/repos/${GITHUB_UPDATE_REPOSITORY}/tags" \
        | grep "\"name\": \"${release_tag_prefix}" \
        | sed 's|.*\('"${release_tag_prefix}"'[^"]*\).*|\1|;/-/!{s/$/_/;}' \
        | sort -V | sed 's/_$//' | tail -n 1
    )

    local latest_version=$(echo "${latest_release_tag}" | sed 's|'"${release_tag_prefix}"'||')

    if [[ "${latest_version}" != "${VERSION}" ]]; then
        >&2 echo "Latest version of '${GITHUB_UPDATE_REPOSITORY}' '${latest_version}' != local version '${VERSION}'. Will do an update."
        echo "https://${authorization_token}raw.githubusercontent.com/${GITHUB_UPDATE_REPOSITORY}/${latest_release_tag}"
    else
        >&2 echo "Latest version of '${GITHUB_UPDATE_REPOSITORY}' '${latest_version}' is same as local. No update needed."
        echo ""
    fi
}

export PYTHONPATH="$(pwd)/${SOURCES_FOLDER}:$(pwd):${PYTHONPATH}"  # PYTHONPATH for imports

CURRENT_OS="$(uname -s)"
PIPS=("pip3" "pip")
PYTHON_EXE=""

if [[ "${CURRENT_OS}" =~ (CYGWIN|MINGW).* ]]; then
    PYTHONS=("python3.exe" "python.exe")
    COVER_PATH="$(cygpath.exe -w "$(pwd)")"
    VENV_SUDO=""
    export PATH="/usr/local/bin:/usr/bin:$PATH"
else
    VENV_SUDO="echo 'Needs sudo to install virtualenv via pip.'; sudo -H "
    PYTHONS=("python3" "python")
    COVER_PATH="${COVER_PATH:-$PWD}"
fi

# Discover python executable on current OS
for py in ${PYTHONS[*]}; do
    ${py} --version >/dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        PYTHON_EXE="${py}"
        break
    fi
done

# platform-specific command to open an HTML file in a default browser
[[ "${CURRENT_OS}" == "Darwin" ]] && WEBSITE_OPENER="open" || WEBSITE_OPENER="${PYTHON_EXE} -m webbrowser -t"

# RUNTIME GLOBALS
failed=0
result_code=0
fail_strict=false

sigint_handler() {
    echo "Terminating ..."
    exit 1
}

trap sigint_handler INT

print_header() {
    local text="$1"
    local color="$2"
    local len="${#text}"
    local width="$(tput cols 2>/dev/null || echo '80')" # fallback for no terminal
    local block=$(echo "(${width}-${len}-4)/2" | bc)
    local line=$(printf '=%.0s' $(eval "echo {1..${block}}"))

    echo -e "\n${color}${line}  ${text}  ${line}${NC}\n"
}

# Tests exit code. Exits on failure and prints message.
# On success, prints optional message.
# $1 = return code to check. 0 is success, anything else failure
# $2 = error message
# $3 = optional success message
test_exit() {
    if [[ $1 -ne 0 ]]; then
        echo -e "$2"
        exit $1
    elif [[ -n ${3+x} ]]; then
        echo -e "$3"
    fi
}

TEST_FAILURES=""

# Marks a test as failed/passed with a message base on return code.
# $1 = exit code to test
# $2 = test type (string)
# $3 = trailing string (optional)
test_failed() {
    if [[ $1 -ne 0 ]]; then
        failed=$(expr ${failed} + 1);
        [[ ${fail_strict} == true ]] && result_code=1
        echo -e "${BRED}$2 failed.${3:-}${NC}"
        TEST_FAILURES="${TEST_FAILURES}\n  * $2"
        return 1
    fi

    echo -e "${GREEN}$2 passed.${3:-}${NC}"
}

# Discovers pip executable on current OS
discover_pip() {
    for pie in ${PIPS[*]}; do
        ${pie} --version >/dev/null 2>&1
        if [[ $? -eq 0 ]]; then
            echo "${pie}"
            return 0
        fi
    done

    return 1
}

while [[ "$#" > 0 ]]; do
    case $1 in
        -o|--browser) open_in_browser=true;;
        -p|--pylint) use_pylint=true;;
        -t|--types) use_typecheck=true;;
        -u|--unittests) use_unittests=true;;
        -c|--coverage) use_coverage=true;;
        -b|--bdd) use_bdd=true;;
        --todo) use_todos=true;;
        --safety) use_safety=true;;
        -fmt|--format) use_formatter=true;;
        -np|--no-pylint) use_pylint=false;;
        -nt|--no-types) use_typecheck=false;;
        -nu|--no-unittests) use_unittests=false;;
        -nc|--no-coverage) use_coverage=false;;
        -nfmt|--no-format) use_formatter=false;;
        -nb|--no-bdd) use_bdd=false;;
        --no-todo) use_todos=false;;
        --no-safety) use_safety=false;;
        -f) use_file="$2"; shift;;
        -tf) use_testfile="$2"; shift;;
        -h|--help) show_help=true;;
        --install) do_install_requirements=true;;
        -ni|--noinstall) no_install_requirements=true;;
        -nv|--novirtualenv) no_virtualenv=true;;
        --update) do_update=true;;
        --no-update) no_update=true;;
        -pe|--python) PYTHON_EXE="$2"; shift;;
        --strict) fail_strict=true;;
        --generate-rc-file) generate_rc_file=true;;
        *) test_exit 1 "Unknown option '$1'. Run program with -h or --help for help.";;
    esac
    shift
done

if [[ -n ${show_help+x} ]]; then
    echo -e "Sanity testing script. If no tool is selected, all will run by default.\n"
    echo -e "Run as:\n  $0 [options]\n\nPossible options are:"
    echo -e "  -h, --help: Displays this help.\n"
    echo -e "Will run only selected tools:"
    echo -e "  -p, --pylint: Run PyLint."
    [[ ${ENABLE_TYPES} == true ]] && echo -e "  -t, --types: Run Mypy for checking types usage."
    [[ ${ENABLE_COVERAGE} == true ]] && echo -e "  -c, --coverage: Run coverage tests." \
        "Use export KEEP_COVERAGE_FILE=1 to prevent automatic deletion of previous .coverage file. This is useful for parallel CI pipelines."
    [[ ${ENABLE_UNITTESTS} == true ]] && echo -e "  -u, --unittests: Run unit tests. " \
        "You can pass additional parameters to pytests with the UNIT_TEST_EXTRA_PARAMS environment variable:\n" \
        "\texport UNIT_TEST_EXTRA_PARAMS='-m not database' ./$0 -u  # Will not run unit tests marked as 'database'"
    [[ ${ENABLE_FORMATTER} == true ]] && echo -e "  -fmt, --format: Run code formatter. "
    [[ ${ENABLE_BDD} == true ]] && echo -e "  -b, --bdd: Run BDD tests with Behave."
    [[ ${ENABLE_TODOS} == true ]] && echo -e "  --todo: Run check of TODOs."
    [[ ${ENABLE_SAFETY} == true ]] && echo -e "  --safety: Run security checks against requirements.txt file."
    echo -e "Will run run everything but selected tools:"
    echo -e "  -np, --no-pylint: Do not run PyLint."
    [[ ${ENABLE_TYPES} == true ]] && echo -e "  -nt, --no-types: Do not run Mypy for checking types usage."
    [[ ${ENABLE_UNITTESTS} == true ]] && echo -e "  -nu, --no-unittests: Do not run unit tests."
    [[ ${ENABLE_COVERAGE} == true ]] && echo -e "  -nc, --no-coverage: Do not run coverage tests."
    [[ ${ENABLE_BDD} == true ]] && echo -e "  -nb, --no-bdd: Do not run BDD tests with Behave."
    [[ ${ENABLE_TODOS} == true ]] && echo -e "  --no-todo: Do not run check of TODOs."
    [[ ${ENABLE_SAFETY} == true ]] && echo -e "  --no-safety: Do not run security checks against requirements.txt file."
    echo -e "  -f: Run PyLint and MyPy only on selected file.\n"
    echo -e "  -tf: Run unit tests only on selected files.\n"
    [[ ${ENABLE_COVERAGE} == true ]] && echo -e "  -o, --browser: Open coverage results in browser."
    echo -e "  --install: Only install requirements and dependencies, then exit."
    echo -e "  -ni, --noinstall: Do not install requirements and dependencies.\n"
    echo -e "  -nv, --novirtualenv: Do not create/use virtualenv."
    [[ ${ENABLE_FORMATTER} == true ]] && echo -e "  -nfmt --no-format: Do not use formatter."
    echo -e "  --update: Only update team related files, then exit."
    echo -e "  --no-update: Don't update team related files."
    echo -e "  -pe, --python: Specify python executable to use for virtualenv."
    echo -e "  --strict: If used, exit code will be non-zero if any test fails."
    echo -e "  --generate-rc-file: Generate RC file for this test script. This file allows to override default settings."
    exit 255
fi

if [[ -z "${PYTHON_EXE}" ]]; then
    test_exit 253 "No python executable found."
fi

PYTHON_EXE="${PYTHON_EXE/#\~/$HOME}"
CURRENT_PYTHON_VERSION="$(${PYTHON_EXE} --version 2>&1 | cut -d ' ' -f 2 | sed 's/\r//')"
${PYTHON_EXE} --version

VENV=".venv_${CURRENT_OS}_${CURRENT_PYTHON_VERSION}"
[[ "${CURRENT_OS}" =~ (CYGWIN|MINGW).* ]] && VENV_ACTIVATE="${VENV}/Scripts/activate" || VENV_ACTIVATE="${VENV}/bin/activate"

# Check if discovered python version is within allowed range.
check_supported_python_version() {
    [[ "${CURRENT_OS}" =~ (CYGWIN|MINGW).* ]] && CURRENT_PYTHON_VERSION="$(echo ${CURRENT_PYTHON_VERSION} | tr --delete '\r')"

    local max_version_number_to_check=2
    [[ ${CHECK_PYTHON_PATCH_VERSION} == true ]] && max_version_number_to_check=3

    strip_version_number() {
        echo $1 | cut -d "." -f 1-${max_version_number_to_check}
    }

    local stripped_current_version=$(strip_version_number "${CURRENT_PYTHON_VERSION}")
    local stripped_min_version=$(strip_version_number "${MIN_PYTHON_VERSION}")
    local stripped_max_version=$(strip_version_number "${MAX_PYTHON_VERSION}")

    ver() {
        printf "%02d%02d%02d" $(echo "$1" | tr '.' ' ')
    }

    local current_version=$(ver "${stripped_current_version}")
    local min_version=$(ver "${stripped_min_version}")
    local max_version=$(ver "${stripped_max_version}")

    [[ ${current_version#0} -ge ${min_version#0} && ${current_version#0} -le ${max_version#0} ]]
    test_exit $? "Python version ${stripped_current_version} is not supported. Supported versions range is <${stripped_min_version}, ${stripped_max_version}>.\nUse pyenv or the '-pe' option to specify different python executable."
}

# Sets default values to switches
# $1 = value to set
set_default_values() {
    local default=$1
    use_pylint=${use_pylint:-${default}}
    use_typecheck=${use_typecheck:-${default}}
    use_unittests=${use_unittests:-${default}}
    use_coverage=${use_coverage:-${default}}
    use_bdd=${use_bdd:-${default}}
    use_todos=${use_todos:-${default}}
    use_safety=${use_safety:-${default}}
    use_formatter=${use_formatter:-${default}}
}

# set everything to true by default, leave only explicitly disabled as false
if [[ ${use_pylint:-false} == false && ${use_typecheck:-false} == false && \
      ${use_unittests:-false} == false && ${use_coverage:-false} == false && \
      ${use_bdd:-false} == false && ${use_todos:-false} == false && \
      ${use_safety:-false} == false && ${use_formatter:-false} == false ]]
then
    set_default_values true
else # only some tests selected, set the rest to false if not defined
    set_default_values false
fi

# turn off disabled
[[ ${ENABLE_TYPES} == false ]] && use_typecheck=false
[[ ${ENABLE_UNITTESTS} == false ]] && use_unittests=false
[[ ${ENABLE_COVERAGE} == false ]] && use_coverage=false
[[ ${ENABLE_BDD} == false ]] && use_bdd=false
[[ ${ENABLE_TODOS} == false ]] && use_todos=false
[[ ${ENABLE_SAFETY} == false ]] && use_safety=false
[[ ${ENABLE_FORMATTER} == false ]] && use_formatter=false

open_in_browser=${open_in_browser:-false}
no_install_requirements=${no_install_requirements:-false}
do_install_requirements=${do_install_requirements:-false}
no_virtualenv=${no_virtualenv:-false}
do_update=${do_update:-false}
no_update=${no_update:-false}
generate_rc_file=${generate_rc_file:-false}

source_files=$(find "${use_file:-${SOURCES_FOLDER}}" -name "*.py" ! -regex "\.\/\.venv_.*" ! -regex "${EXCLUDE_PATH_FROM_TESTS_REGEXP:-^$}" 2>/dev/null)
test_files=$(find "${use_testfile:-${TESTS_FOLDER}}" -name "*.py" ! -regex "\.\/\.venv_.*" ! -regex "${EXCLUDE_PATH_FROM_TESTS_REGEXP:-^$}" 2>/dev/null)

if [[ ${generate_rc_file} == true ]]; then
    echo -e "# Uncomment only lines you need to change.\n" >${TEST_RC_FILE}

    head -n ${TEST_RC_FILE_HEAD_OFFSET["end"]} $0 | \
    tail -n +${TEST_RC_FILE_HEAD_OFFSET["start"]} | \
    sed 's/\(..*\)/#\1/' \
    >>${TEST_RC_FILE}

    echo "Test RC file generated into '${TEST_RC_FILE}'."
    exit 0
fi

if [[ ${no_update} == false && -n ${GITHUB_UPDATE_REPOSITORY} && ${#GITHUB_UPDATE_SOURCES_TARGETS[@]} -gt 0 ]]; then
    print_header "Updating team files"

    GITHUB_UPDATE_BASE_URL="$(get_update_url)"

    if [[ -n ${GITHUB_UPDATE_BASE_URL} ]]; then
        for source_file in "${!GITHUB_UPDATE_SOURCES_TARGETS[@]}"; do
            url="${GITHUB_UPDATE_BASE_URL}/${source_file}"
            target_file="${GITHUB_UPDATE_SOURCES_TARGETS[${source_file}]}"
            [[ -z ${target_file} ]] && continue  # Skip files with no target location

            target_path="$(dirname "${target_file}")"
            success_msg="File '${target_file}' updated."
            fail_msg="File '$source_file' from '${GITHUB_UPDATE_REPOSITORY}' repository could not be updated.\nCheck error output above."
            downloaded_file=$(mktemp)

            # Download is faster than checking if file has been modified via API
            curl_output=$(curl --fail -o "${downloaded_file}" "${url}" 2>&1)
            test_exit $? "${curl_output}\n\n${fail_msg}" "${success_msg}"

            mkdir -p "${target_path}"
            mv "${downloaded_file}" "${target_file}"
        done
    fi

    [[ ${do_update} == true ]] && exit 0
fi

if [[ ${no_virtualenv} == false ]]; then
    if [[ ! -d "${VENV}" ]]; then
        check_supported_python_version
        print_header "Creating virtualenv"

        if ! ${PYTHON_EXE} -m virtualenv --version >/dev/null 2>&1; then
            ${PYTHON_EXE} -m pip install --user --upgrade virtualenv
            test_exit $? "Could not install virtualenv via pip."
        fi

        ${PYTHON_EXE} --version >/dev/null 2>&1
        test_exit $? "Python executable '${PYTHON_EXE}' does not exist. Cannot create virtualenv."

        ${PYTHON_EXE} -m virtualenv -p "${PYTHON_EXE}" "${VENV}"
    fi

    source "${VENV_ACTIVATE}"
    test_exit $? "Failed to activate virtualenv."
else
    check_supported_python_version
fi

PIP_EXE="$(discover_pip)"
test_exit $? "No pip executable found. Please install pip."

# Install given libraries if condition variable is true
# $1 = condition variable
# $@ = library names
fail_if_enabled_but_not_installed () {
    [[ $1 == false ]] && return 1

    shift
    while [[ -n "$1" ]]; do
        echo -n "Checking '$1' is installed ... "
        ${PIP_EXE} show $1 >/dev/null 2>&1
        test_exit $? "not installed but required by this script. Add it to your requirements-test.txt file." "OK"
        shift
    done
}

if [[ ${no_install_requirements} == false ]]; then
    print_header "Refreshing dependencies"

    if [[ "${CURRENT_OS}" =~ (CYGWIN|MINGW).* ]]; then
        ${PIP_EXE} install --upgrade pypiwin32
        test_exit $? "Failed to install pypiwin32 via pip."
    fi

    for requirements_file_name in requirements*.txt; do
        if [[ -f "${requirements_file_name}" ]]; then
            ${PIP_EXE} install --upgrade -r "${requirements_file_name}"
            test_exit $? "Failed to install requirements via pip from '${requirements_file_name}'."
        fi
    done

    fail_if_enabled_but_not_installed true pylint
    fail_if_enabled_but_not_installed ${ENABLE_TYPES} mypy
    fail_if_enabled_but_not_installed ${ENABLE_UNITTESTS} pytest
    fail_if_enabled_but_not_installed ${ENABLE_BDD} behave
    fail_if_enabled_but_not_installed ${ENABLE_COVERAGE} coverage pytest-cov
    fail_if_enabled_but_not_installed ${ENABLE_FORMATTER} pre-commit black
    fail_if_enabled_but_not_installed ${ENABLE_SAFETY} safety
    fail_if_enabled_but_not_installed ${DJANGO_AWARE} pylint-django

    pre-commit install

    echo -e "\nUse '-ni' command line argument to prevent installing requirements."

    [[ ${do_install_requirements} == true ]] && exit 0
fi

if [[ ${use_formatter} == true ]]; then
    print_header "Running formatter"
    pre-commit run black --all-files
    test_failed $? "Formatter"
fi

if [[ ${use_bdd} == true ]]; then
    print_header "Running behave"
    behave ${BDD_TESTS_FOLDER}
    test_failed $? "Behave BDD tests"
fi

if [[ ${ENABLE_COVERAGE} == true && ${use_coverage} == true ]]; then
    coverage_pytest_args="--cov=""${SOURCES_FOLDER}"" --cov-branch --cov-report= "
fi

if [[ ${ENABLE_UNITTESTS} == true && ${use_unittests} == true ]]; then
    print_header "Running unit tests"
    env $(cat .env | xargs) pytest -v --junitxml=unit_test_results.xml ${coverage_pytest_args} ${UNIT_TEST_EXTRA_PARAMS} ${UNIT_TESTS_FOLDER}
    test_failed $? "Unit tests"
fi

if [[ ${ENABLE_COVERAGE} == true && ${use_coverage} == true ]]; then
    print_header "Running coverage test"
    coverage report --skip-covered --fail-under=${COVERAGE_MIN_PERCENTAGE:-0}
    test_failed $? "Test for minimum coverage of ${COVERAGE_MIN_PERCENTAGE:-0}%"

    coverage html -d "${COVER_PATH}/cover"
    coverage xml -o "${COVER_PATH}/cover/coverage.xml"

    # open in default browser
    [[ ${open_in_browser} == true ]] && ${WEBSITE_OPENER} "${COVER_PATH}/cover/index.html"
fi

if [[ -z ${KEEP_COVERAGE_FILE} ]]; then
    rm -f .coverage
fi

if [[ ${ENABLE_TYPES} == true && ${use_typecheck} == true ]]; then
    print_header "Running type check"

    mypy_exe="mypy"
    if [[ "${CURRENT_OS}" =~ (CYGWIN|MINGW).* ]]; then
        mypy_exe="${PYTHON_EXE} ${VENV}/Lib/site-packages/mypy/"
    fi

    # --disallow-untyped-calls
    ${mypy_exe} --ignore-missing-imports ${source_files} ${test_files}
    test_failed $? "Type checks"
fi

# $1 = 'source', 'tests'
# $2 = minimum pylint score
run_pylint() {
    # unused-import disabled because it is picking up typing imports. Fix is coming.

    local msg_template='{C}:{line:3d},{column:2d}: {msg} ({symbol}, {msg_id})'
    local extra_params=""
    local files=""
    local min_score=$2

    [[ ${DJANGO_AWARE} == true ]] && extra_params="${extra_params}'--load-plugins','pylint_django',"

    if [[ $1 == 'source' ]]; then  # running pylint for source code
        export PYLINTRC="${SOURCES_FOLDER}/.pylintrc"
        files=${source_files}
    elif [[ $1 == 'tests' ]]; then  # running pylint for tests code
        export PYLINTRC="${TESTS_FOLDER}/.pylintrc"
        extra_params="${extra_params}'--disable=protected-access',"
        files=${test_files}
    else  # invalid option
        test_exit 1 "Invalid pylint run type '$1'."
    fi

    # The following code is horrible. Caused by https://github.com/PyCQA/pylint/issues/2242
    ${PYTHON_EXE} -c "
from pylint import lint
from sys import exit
run = lint.Run([
    '--jobs', '0',
    '--disable', 'all,RP0001,RP0002,RP0003,RP0101,RP0401,RP0701,RP0801',
    '--enable', 'F,E,W,R,C',
    '--msg-template', '${msg_template}',
    '--disable', '''
        missing-docstring,
        missing-type-doc,
        missing-returns-doc,
        missing-return-type-doc,
        missing-yield-doc,
        missing-yield-type-doc,
        logging-fstring-interpolation,

        apply-builtin,
        bad-continuation,
        backtick,
        basestring-builtin,
        buffer-builtin,
        cmp-builtin,
        cmp-method,
        coerce-builtin,
        coerce-method,
        delslice-method,
        dict-iter-method,
        dict-view-method,
        execfile-builtin,
        file-builtin,
        filter-builtin-not-iterating,
        getslice-method,
        hex-method,
        import-star-module-level,
        indexing-exception,
        input-builtin,
        intern-builtin,
        long-builtin,
        long-suffix,
        map-builtin-not-iterating,
        metaclass-assignment,
        next-method-called,
        no-absolute-import,
        nonzero-method,
        oct-method,
        old-division,
        old-ne-operator,
        old-octal-literal,
        old-raise-syntax,
        parameter-unpacking,
        print-statement,
        raising-string,
        range-builtin-not-iterating,
        raw_input-builtin,
        reduce-builtin,
        reload-builtin,
        round-builtin,
        setslice-method,
        standarderror-builtin,
        unichr-builtin,
        unicode-builtin,
        unpacking-in-except,
        using-cmp-argument,
        xrange-builtin,
        zip-builtin-not-iterating
    ''',
    '--evaluation', '10.0 - ((float(20 * fatal + 10 * error + 5 * warning + 2 * refactor + convention) / statement) * 10)',
    '--enable', 'useless-suppression',
    ${extra_params}
    *'''${files}'''.split('\n'),
], do_exit=False)
exit(bool(run.linter.stats['global_note'] < ${min_score}))"

    return $?
}

if [[ ${use_pylint} == true ]]; then
    if [[ "${CURRENT_OS}" =~ (CYGWIN|MINGW).* ]]; then
        # color fix for windows terminals
        export TERM=xterm-16color
    fi

    if [[ -n "${source_files}" ]]; then
        print_header "Running pylint on source code"
        run_pylint 'source' ${MIN_PYLINT_SCORE_SOURCE}
        test_failed $? "PyLint checks on source code" "\nMinimum score is ${MIN_PYLINT_SCORE_SOURCE}"
    fi

    if [[ -n "${test_files}" ]]; then
        print_header "Running pylint on tests"
        run_pylint 'tests' ${MIN_PYLINT_SCORE_TESTS}
        test_failed $? "PyLint checks on tests" "\nMinimum score is ${MIN_PYLINT_SCORE_TESTS}"
    fi
fi

if [[ ${use_todos} == true ]]; then
    print_header "Running TODOs check"

    todos="$(grep -Enr --exclude-dir=$EXCLUDE_PATH_FROM_TESTS_REGEXP --include=*.{py,sh,feature} --include={Docker,Jenkins}file 'TODO *[(:]' Dockerfile Jenkinsfile ${SOURCES_FOLDER} ${TESTS_FOLDER} | tr -s ' ')"
    unnamed_todos=$(echo "${todos}" | grep -E "TODO[^(]*:")
    named_todos=$(echo "${todos}" | grep -E "TODO *\([^)]*\):")
    name_counts="$(echo "${named_todos}" | sed 's/.*TODO *(\([^)]*\)).*/\1/' |
                   tr '[:upper:]' '[:lower:]' | sort | uniq -c |
                   awk '{print toupper(substr($2,0,1))tolower(substr($2,2))": "$1}')"
    ok_todos="$(echo "${name_counts}" | awk -v limit=${TODOS_LIMIT_PER_PERSON} '$2 <= limit{print $0}')"
    too_many_todos="$(echo "${name_counts}" | awk -v limit=${TODOS_LIMIT_PER_PERSON} '$2 > limit{print $0}')"

    [[ $(echo "${named_todos}" | wc -c) -gt 1 ]] && echo -e "All named TODOs:\n\n${named_todos}"

    if [[ $(echo "${unnamed_todos}" | wc -c) -gt 1 ]]; then
        echo -e "\nUnnamed TODOs:\n\n${unnamed_todos}\n"
        test_failed 1 "All TODOs must be named (# TODO(<name>): <comment>). Test"
    fi

    [[ $(echo "${named_todos}" | wc -c) -gt 1 ]] && echo -e "\nTODO counts per person (maximum is ${TODOS_LIMIT_PER_PERSON}):\n\n${ok_todos}\n"

    if [[ $(echo "${too_many_todos}" | wc -c) -gt 1 ]]; then
        echo -e "Too many TODOs per person (maximum is ${TODOS_LIMIT_PER_PERSON}):\n\n${too_many_todos}\n"
        test_failed 1 "Every person must have at most ${TODOS_LIMIT_PER_PERSON} TODOs. Test"
    fi
fi

if [[ ${use_safety} == true ]]; then
    print_header "Running Safety check"

    if [[ "${CURRENT_OS}" =~ (CYGWIN|MINGW).* ]]; then
        echo -e "${BYELLOW}Safety currently doesn't work on Windows. See https://github.com/pyupio/safety/issues/119${NC}"
    else
        results=$(safety check -r requirements.txt 2>&1)
        error_code=$?

        if [[ ${error_code} -ne 0 ]]; then
            echo "${results}" | grep -v "unpinned requirement" | tail -n +15 | sed 's/╞/╒/;s/╡/╕/'
        else
            echo "${results}" | grep -q "unpinned requirement"

            if [[ $? -eq 0 ]]; then
                error_code=1
                echo "${results}" | grep "unpinned requirement"
                echo ""
            fi
        fi

        test_failed ${error_code} "Safety checks on requirements.txt"
    fi
fi

if [[ ${no_virtualenv} == false ]]; then
    deactivate
fi

if [[ ${failed} -ne 0 ]]; then
    echo -e "\n${BRED}Some tests failed:${TEST_FAILURES}${NC}"
else
    echo -e "\n${BGREEN}All tests passed.${NC}"
fi

exit ${result_code}
