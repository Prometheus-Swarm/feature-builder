"""Stage for leader audits."""

import requests
from prometheus_test.utils import create_signature


def prepare(runner, worker):
    """Prepare data for leader audit"""
    # Check if PR URL exists for leader
    pr_url = runner.get("pr_urls.leader")
    if not pr_url:
        print("✓ No PR URL found for leader, skipping leader audit - continuing")
        return None

    # Get submission data from state
    submission_data = runner.get("submission_data.leader")
    if not submission_data:
        print(
            "✓ No submission data found for leader, skipping leader audit - continuing"
        )
        return None

    # Create auditor payload which is used to generate the signature
    auditor_payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "prUrl": pr_url,
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
    }

    # Structure the payload according to what the server expects
    return {
        "submission": {
            "taskId": runner.get("task_id"),
            "roundNumber": runner.get("current_round"),
            "prUrl": pr_url,
            "githubUsername": submission_data.get("githubUsername"),
            "repoOwner": submission_data.get("repoOwner"),
            "repoName": submission_data.get("repoName"),
            "stakingKey": submission_data.get("stakingKey"),
            "pubKey": submission_data.get("pubKey"),
            "uuid": submission_data.get("uuid"),
            "nodeType": submission_data.get("nodeType"),
        },
        "submitterSignature": submission_data.get("signature"),
        "submitterStakingKey": submission_data.get("stakingKey"),
        "submitterPubKey": submission_data.get("pubKey"),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "stakingSignature": create_signature(
            worker.get_key("staking_signing"), auditor_payload
        ),
        "publicSignature": create_signature(
            worker.get_key("main_signing"), auditor_payload
        ),
        "prUrl": pr_url,
        "repoOwner": submission_data.get("repoOwner"),
        "repoName": submission_data.get("repoName"),
        "githubUsername": worker.get_env("GITHUB_USERNAME"),
    }


def execute(runner, worker, data):
    """Execute leader audit step"""
    # If prepare returned None, skip this step
    if data is None:
        return {
            "success": True,
            "message": "Skipped due to missing PR URL or submission data",
        }

    url = f"{worker.get('url')}/leader-audit/{runner.get('current_round')}"
    response = requests.post(url, json=data)
    result = response.json()

    return result
