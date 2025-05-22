"""Stage for leader tasks."""

import requests
from prometheus_test.utils import create_signature


def prepare(runner, worker):
    """Prepare data for leader task"""
    # Create fetch-issue payload for stakingSignature and publicSignature
    fetch_issue_payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "action": "fetch-issue",
        "githubUsername": worker.get_env("GITHUB_USERNAME"),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
    }

    # Create add-pr payload for addPRSignature
    add_pr_payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "action": "add-issue-pr",
        "githubUsername": worker.get_env("GITHUB_USERNAME"),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "isFinal": False,  # Draft PR
        "prUrl": None,  # Will be filled in later
    }

    return {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "stakingSignature": create_signature(
            worker.get_key("staking_signing"), fetch_issue_payload
        ),
        "publicSignature": create_signature(
            worker.get_key("main_signing"), fetch_issue_payload
        ),
        "addPRSignature": create_signature(
            worker.get_key("staking_signing"), add_pr_payload
        ),
    }


def execute(runner, worker, data):
    """Execute leader task step"""
    url = f"{worker.get('url')}/leader-task/{data['roundNumber']}"
    response = requests.post(url, json=data)
    result = response.json()

    # Handle 409 gracefully - no eligible issues is an expected case
    if response.status_code == 409:
        print(f"✓ {result.get('message', 'No eligible issues')} - continuing")
        return {"success": True, "message": result.get("message")}

    if result.get("success") and "pr_url" in result:
        # Store PR URL in state
        runner.set("pr_urls.leader", result["pr_url"], scope="round")

        # Store submission data
        submission_data = {
            "githubUsername": worker.get_env("GITHUB_USERNAME"),
            "nodeType": "leader",
            "prUrl": result["pr_url"],
            "repoName": result.get("repoName"),
            "repoOwner": result.get("repoOwner"),
            "roundNumber": runner.get("current_round"),
            "taskId": runner.get("task_id"),
            "uuid": runner.get("issue_uuid"),  # Leader uses the issue UUID
            "stakingKey": worker.get_key("staking_public"),
            "pubKey": worker.get_key("main_public"),
            "bountyId": result.get("bounty_id"),
        }
        runner.set("submission_data.leader", submission_data, scope="round")

    return result
