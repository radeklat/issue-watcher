# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).
Types of changes are:

- **Breaking changes** for breaking changes.
- **Features** for new features or changes in existing functionality.
- **Fixes** for any bug fixes.
- **Deprecated** for soon-to-be removed features.

## [Unreleased]

## [5.0.0] - 2022-12-30

### Breaking changes

- Removed `version_check.check_python_support()`. Python version support should be done by package manager instead.
- Removed unused constants from `constants`: `__version__`, `APPLICATION_NAME`, `MIN_SUPPORTED_PYTHON_VERSION_INCLUSIVE` and `MAX_SUPPORTED_PYTHON_VERSION_EXCLUSIVE`

### Features

- Added support for Python 3.11
- Added default timeout of 30s to all `requests` calls to prevent undesirably long waiting for responses.

### Fixes

- Dependencies update

## [4.0.2] - 2022-07-06

### Fixes

- Dependencies update

## [4.0.1] - 2022-02-08

### Fixes

- Wrong Python requirement clause in pyproject.toml causing the library not being available for Python 3.10.
- Dependencies update.

## [4.0.0] - 2021-12-01

### Features

- Support for Python 3.9 and 3.10

### Breaking changes

- `github.GitHubIssueState` states `open` and `closed` to `OPEN` and `CLOSED`.
- Top level import renamed from `issuewatcher` to `issue_watcher` to match the package name.
- Removed support for Python 3.6

### Fixes

- Update dependencies.
- Missing explicit encoding in `open`.

## [3.0.0] - 2021-01-04

### Breaking changes

- `AssertGitHubIssue.fixed_in()` will fail with `AssertionError` when list of versions from GitHub doesn't return any valid semantic versions.

### Fixes

- DeprecationError about soon to be removed `LegacyVersion` from `packaging`

## [2.3.0] - 2020-06-04

### Features

- Option to check release numbers with `AssertGitHubIssue.fixed_in()`.

## [2.2.4] - 2020-05-06

### Fixes

- Deprecation in the `semver` library.

## [2.2.3] - 2020-03-25

### Fixes

- Fixed version of pylint until testing script is compatible with 2.5.0+

## [2.2.2] - 2020-03-25

### Fixes

- Annotated package as typed according to [PEP 561](https://www.python.org/dev/peps/pep-0561/).

## [2.2.1] - 2019-11-08

### Features

- Verified support for Python 3.8 which required a couple of constants to be changed.

## [2.2.0] - 2019-10-20 

### Features

- Python version check to warn/fail for unsupported Python versions.

## [2.1.1] - 2019-10-19

### Fixes

- New mypy issue with bytes strings in format function.

## [2.1.0] - 2019-10-06

### Features

- `AssertGitHubIssue.current_release()` shows current number of releases in failing test when no number given.

## [2.0.0] - 2019-10-06

### Features

- Compatibility with pytest
- Repository ID supplied through constructor as a single string

### Breaking changes

- Tests rewritten from unittest to pytest
- GitHub issue class and assertions drop duplicate or unnecessary information for their name:
    - `GitHubIssueTestCase` -> `AssertGitHubIssue`
    - `assert_github_issue_is_state` -> `is_state`
    - `assert_github_issue_is_open` -> `is_open`
    - `assert_github_issue_is_closed` -> `is_closed`
    - `assert_no_new_release_is_available` -> `current_release`
- Method parameter `issue_number` renamed to `issue_id` in `is_state()`, `is_open()` and `is_closed()`.
- Removed sub-classing of `unittest.TestCase`
- Removes setting repository ID through class attributes

## [1.2.0] - 2019-08-14

### Features

- Caching functionality to speed up tests involving network calls and prevent API quota depletion.
- `CACHE_INVALIDATION_IN_SECONDS` [environment variables](README.md#environment-variables) for changing default cache invalidation period or disabling cache completely.

## [1.1.1] - 2019-08-08

### Fixes

- Drops Python 3.5 from classifiers as it was never supported.

## [1.1.0] - 2019-08-05

### Features

- `GITHUB_USER_NAME` and `GITHUB_PERSONAL_ACCESS_TOKEN` [environment variables](README.md#environment-variables) to allow authentication with GitHub API and higher API rate limit (5000/API token/hour instead of the default 60/host/hour).

## [1.0.0] - 2019-08-04

### Features

- Initial source code
- Error handling printing out full message received.
- Error handling of exceeded API rate limit, showing current quota and time until quota reset.

[Unreleased]: https://github.com/radeklat/issue-watcher/compare/5.0.0...HEAD
[5.0.0]: https://github.com/radeklat/issue-watcher/compare/releases/4.0.2...5.0.0
[4.0.2]: https://github.com/radeklat/issue-watcher/compare/releases/4.0.1...4.0.2
[4.0.1]: https://github.com/radeklat/issue-watcher/compare/releases/4.0.0...4.0.1
[4.0.0]: https://github.com/radeklat/issue-watcher/compare/releases/3.0.0...4.0.0
[3.0.0]: https://github.com/radeklat/issue-watcher/compare/releases/2.3.0...releases/3.0.0
[2.3.0]: https://github.com/radeklat/issue-watcher/compare/releases/2.2.4...releases/2.3.0
[2.2.4]: https://github.com/radeklat/issue-watcher/compare/releases/2.2.3...releases/2.2.4
[2.2.3]: https://github.com/radeklat/issue-watcher/compare/releases/2.2.2...releases/2.2.3
[2.2.2]: https://github.com/radeklat/issue-watcher/compare/releases/2.2.1...releases/2.2.2
[2.2.1]: https://github.com/radeklat/issue-watcher/compare/releases/2.2.0...releases/2.2.1
[2.2.0]: https://github.com/radeklat/issue-watcher/compare/releases/2.1.1...releases/2.2.0
[2.1.1]: https://github.com/radeklat/issue-watcher/compare/releases/2.1.0...releases/2.1.1
[2.1.0]: https://github.com/radeklat/issue-watcher/compare/releases/2.0.0...releases/2.1.0
[2.0.0]: https://github.com/radeklat/issue-watcher/compare/releases/1.2.0...releases/2.0.0
[1.2.0]: https://github.com/radeklat/issue-watcher/compare/releases/1.1.1...releases/1.2.0
[1.1.1]: https://github.com/radeklat/issue-watcher/compare/releases/1.1.0...releases/1.1.1
[1.1.0]: https://github.com/radeklat/issue-watcher/compare/releases/1.0.0...releases/1.1.1
[1.0.0]: https://github.com/radeklat/issue-watcher/compare/initial...releases/1.0.0
