# issue-watcher
Sometimes it happens that you discover a bug in a library that you are using and have to create a workaround (technical debt). However, it would be good to also remove the workaround once a bugfix is released.

This library provides several useful assertions that are watching when an issue is closed and failing a test to let you know fixed functionality is available. A good way to automatically manage and reduce known technical debt.

![PyPI - Downloads](https://img.shields.io/pypi/dm/issue-watcher)
![CircleCI](https://img.shields.io/circleci/build/github/radeklat/issue-watcher)
![Codecov](https://img.shields.io/codecov/c/github/radeklat/issue-watcher)
![PyPI - License](https://img.shields.io/pypi/l/issue-watcher)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/issue-watcher)
![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/radeklat/issue-watcher)
![Maintenance](https://img.shields.io/maintenance/yes/2022)
![GitHub last commit](https://img.shields.io/github/last-commit/radeklat/issue-watcher)

# Installation

    pip install issue-watcher
    
# Support

## Issue trackers

* GitHub
    
# Usage

Let's assume you want to watch a [Safety](https://github.com/pyupio/safety) [issue #119](https://github.com/pyupio/safety/issues/119) preventing you from running the tool on Windows. Once fixed, you would like to enable it on Windows.

Following examples will show typical steps you would take and automation available from this package.

## Issue is open

You would like to be notified once the issue is resolved (closed) and enable the currently disabled behaviour. To get notified in relevant place, create the following test case:

    from unittest import TestCase
    
    from issuewatcher import AssertGitHubIssue
    
    class BugsInSafetyAreFixedTestCase(TestCase):
        def test_safety_cannot_be_enable_on_windows(self):
            AssertGitHubIssue("pyupio/safety").is_open(
                119, "Check if safety can be enabled on Windows."
            )
            
Alternatively, with pytest:

    from issuewatcher import AssertGitHubIssue
    
    def test_safety_cannot_be_enable_on_windows(self):
        AssertGitHubIssue("pyupio/safety").is_open(
            119, "Check if safety can be enabled on Windows."
        )
        
Once the issue is closed on GitHub, the test will fail with the following error message:

    GitHub issue #119 from 'pyupio/safety' is no longer open. Check if safety 
    can be enabled on Windows. Visit https://github.com/pyupio/safety/issues/119.
    
## Issues is closed ...

You can update the test case to watch if issue is not re-opened. Change the test case from:

    def test_safety_cannot_be_enable_on_windows(self):
        AssertGitHubIssue("pyupio/safety").is_open(
            119, "Check if safety can be enabled on Windows."
        )
        
to

    def test_safety_can_be_enable_on_windows(self):
        AssertGitHubIssue("pyupio/safety").is_closed(
            119, "Check if safety should be disabled on Windows."
        )

The updated test case will now fail if issue gets re-opened.

## ... but fix is not released yet

To watch for the fix to be released, you can add a release watch test.

### I don't know which version will contain the fix

Assuming that there are 25 releases at the moment of writing the test:

    def test_safety_fix_has_not_been_released(self):
        AssertGitHubIssue("pyupio/safety").current_release(25)
        
If you're not sure how many releases there are at the moment, you can leave the release number empty:

    def test_safety_fix_has_not_been_released(self):
        AssertGitHubIssue("pyupio/safety").current_release()
        
and the test will report it in the failing test:

    This test does not have any number of releases set. Current number of releases is '25'.

### I know the version of a release that will contain the fix

Sometimes the maintainer will mention which release will include the fix. Let's assume the release will be `2.0.0`. To get notified about it, use:

    def test_safety_fix_has_not_been_released(self):
        AssertGitHubIssue("pyupio/safety").fixed_in("2.0.0")
        
## Fix is released
        
Once a new release is available, the test above will fail with:

    New release of 'pyupio/safety' is available. Expected 25 releases but 26 are
    now available. Visit https://github.com/pyupio/safety/releases.

or

    Release '2.0.0' of 'pyupio/safety' is available. Latest version is
    '2.2.4'. Visit https://github.com/pyupio/safety/releases.
    
Now you can remove the tech debt and the release test case. However, keep the issue status test case to check for a regression.

# Environment variables

`GITHUB_USER_NAME`, `GITHUB_PERSONAL_ACCESS_TOKEN`: Set to GitHub user name and [personal access token](https://github.com/settings/tokens) to raise API limit from 60 requests/hour for a host to 5000 requests/hour on that API key.

`CACHE_INVALIDATION_IN_SECONDS`: Set to number of seconds for invalidating cached data retrieved from HTTP calls. Default value is `3600` seconds (1 day). Use `0` to disable caching. This is useful if you run tests frequently to speed them up and prevent API quota depletion.