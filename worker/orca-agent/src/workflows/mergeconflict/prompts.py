"""Merge conflict workflow prompts."""

PROMPTS = {
    "resolve_conflicts": {
        "system": "You are an AI assistant helping to resolve merge conflicts in a GitHub repository.",
        "human": """I need help resolving merge conflicts in a Git repository.

The conflicts occurred while merging PRs into a consolidated branch.

Please help me resolve these conflicts by:
1. Examining the conflicting files
2. Understanding the changes from each PR
3. Resolving conflicts in a way that preserves the intended functionality
4. Ensuring the code remains valid and follows best practices

Available files: {current_files}

Please analyze the conflicts and suggest resolutions.""",
    },
    "create_draft_pr": {
        "system": "You are an AI assistant helping to create a draft pull request for tracking work in progress.",
        "human": """I need to create an initial draft pull request to track the progress of merging multiple PRs.

The PR should:
1. Be created as a draft PR with [WIP] prefix
2. Include a description explaining that this is a work in progress
3. List the PRs that will be merged
4. Be created from the {head_branch} branch to the upstream default branch

Source fork info:
- URL: {source_fork[url]}
- Owner: {source_fork[owner]}
- Name: {source_fork[name]}
- Branch: {source_fork[branch]}

Working fork info:
- URL: {working_fork[url]}
- Owner: {working_fork[owner]}
- Name: {working_fork[name]}

Upstream repo info:
- URL: {upstream[url]}
- Owner: {upstream[owner]}
- Name: {upstream[name]}
- Default branch: {upstream[default_branch]}

Please create a draft PR to track this work.""",
    },
    "create_consolidated_pr": {
        "system": "You are an AI assistant helping to create a pull request that consolidates multiple PRs.",
        "human": """I need to create a pull request that consolidates multiple PRs into a single PR.

The PR should:
1. Include a clear title describing the consolidated changes
2. List all the PRs that were merged
3. Credit the original PR authors
4. Include relevant test results
5. Be created from the {head_branch} branch to the upstream default branch

Source fork info:
- URL: {source_fork[url]}
- Owner: {source_fork[owner]}
- Name: {source_fork[name]}
- Branch: {source_fork[branch]}

Working fork info:
- URL: {working_fork[url]}
- Owner: {working_fork[owner]}
- Name: {working_fork[name]}

Upstream repo info:
- URL: {upstream[url]}
- Owner: {upstream[owner]}
- Name: {upstream[name]}
- Default branch: {upstream[default_branch]}

Merged PRs:
{pr_details}

Please create a consolidated PR that properly credits all contributors.""",
    },
    "verify_tests": {
        "system": "You are an AI assistant helping to verify and fix tests after merging multiple PRs.",
        "human": """I need to verify that all tests pass after merging multiple PRs.

Please:
1. Run the test suite
2. Analyze any failures
3. Fix any issues found
4. Ensure all tests pass before proceeding

Available files: {current_files}

Please run the tests and fix any issues.""",
    },
}
