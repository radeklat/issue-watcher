# issue-watcher
Python test cases watching when an issue is closed and failing a test to let you know fixed functionality is available. A good wayt to automatically manage and reduce know technical debt.

# Installation

    pip install issue-watcher
    
# Support

## Issue trackers

* GitHub

## Python

* 3.6
* 3.7

Why not 3.5 and lower? I wanted to build a modern library with full type hinting support and f-strings. 3.4 and lower already reached [end-of-life](https://devguide.python.org/devcycle/#end-of-life-branches).
    
# Usage

Let's assume you want to watch a [Safety](https://github.com/pyupio/safety) [issue #119](https://github.com/pyupio/safety/issues/119) preventing you from running the tool on Windows. Once fixed, you would like to enable it on Windows.

Following examples will show typical steps you would take and automation available from this package.

## Issue is open

You would like to be notified once the issue is resolved (closed) and enable the currently disabled behaviour. To get notified in relevant place, create the following test case:

    from issuewatcher import GitHubIssueTestCase
    
    class BugsInSafetyAreFixedTestCase(GitHubIssueTestCase):
        _OWNER = "pyupio"
        _REPOSITORY = "safety"

        def test_safety_cannot_be_enable_on_windows(self):
            self.assert_github_issue_is_open(
                119, "Check if safety can be enabled on Windows."
            )
        
Once the issue is closed on GitHub, the test will fail with the following error message:

    GitHub issue #119 from 'pyupio/safety' is no longer open.
    Visit https://github.com/pyupio/safety/issues/119.
    
## Issues is closed ...

You can update the test case to watch if issue is not re-opened. Change the test case from:

    def test_safety_cannot_be_enable_on_windows(self):
        self.assert_github_issue_is_open(
            119, "Check if safety can be enabled on Windows."
        )
        
to

    def test_safety_can_be_enable_on_windows(self):
        self.assert_github_issue_is_closed(
            119, "Check if safety can be enabled on Windows."
        )

The updated test case will now fail if issue gets re-opened.

## ... but fix is not released yet

To watch for the fix to be released, you can add a release watch test. Assuming that there are 25 releases at the moment of writing the test:

    def test_safety_fix_has_not_been_released(self):
        self.assert_no_new_release_is_available(25)
        
## Fix is released
        
Once a new release is available, the test above will fail with:

    New release of 'pyupio/safety' is available. Expected 25 releases but 26 are
    now available. Visit https://github.com/pyupio/safety/releases.
    
Now you can remove the tech debt and the release test case. However, keep the issue status test case to check for regression.

#Environment variables

`GITHUB_USER_NAME`, `GITHUB_PERSONAL_ACCESS_TOKEN`: Set to GitHub user name and [personal access token](https://github.com/settings/tokens) to raise API limit from 60 requests/hour for a host to 5000 requests/hour on that API key.