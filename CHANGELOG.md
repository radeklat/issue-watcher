# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).
Types of changes are:

* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Deprecated** for soon-to-be removed features.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.
* **Security** in case of vulnerabilities.

## Unreleased

## Added
* Compatibility with pytest
* Repository ID supplied through constructor as a single string

### Changed
* Tests rewritten from unittest to pytest
* GitHub issue class and assertions drop duplicate or unnecessary information for their name:
    * `GitHubIssueTestCase` -> `AssertGitHubIssue`
    * `assert_github_issue_is_state` -> `is_state`
    * `assert_github_issue_is_open` -> `is_open`
    * `assert_github_issue_is_closed` -> `is_closed`
    * `assert_no_new_release_is_available` -> `fix_not_released`

### Removed
* Sub-classing of `unittest.TestCase`
* Setting repository ID through class attributes

## [1.2.0] - 2019-08-14

### Added
* Caching functionality to speed up tests involving network calls and prevent API quota depletion.
* `CACHE_INVALIDATION_IN_SECONDS` [environment variables](README.md#environment-variables) for changing default cache invalidation period or disabling cache completely. 

## [1.1.1] - 2019-08-08

### Fixed
* Drops Python 3.5 from classifiers as it was never supported.

## [1.1.0] - 2019-08-05

### Added
* `GITHUB_USER_NAME` and `GITHUB_PERSONAL_ACCESS_TOKEN` [environment variables](README.md#environment-variables) to allow authentication with GitHub API and higher API rate limit (5000/API token/hour instead of the default 60/host/hour).

## [1.0.0] - 2019-08-04

### Added
* Initial source code
* Error handling printing out full message received.
* Error handling of exceeded API rate limit, showing current quota and time until quota reset.

[Unreleased]: https://github.com/radeklat/issue-watcher/compare/releases/1.2.0...HEAD
[1.2.0]: https://github.com/radeklat/issue-watcher/compare/releases/1.1.1...releases/1.2.0
[1.1.1]: https://github.com/radeklat/issue-watcher/compare/releases/1.1.0...releases/1.1.1
[1.1.0]: https://github.com/radeklat/issue-watcher/compare/releases/1.0.0...releases/1.1.1
[1.0.0]: https://github.com/radeklat/issue-watcher/compare/initial...releases/1.0.0
