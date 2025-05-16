"""Stage for handling leader submissions."""

import requests
from prometheus_test.utils import create_signature


def prepare(runner, worker):
    """Prepare data for leader submission"""
    # Check if PR URL exists for leader
    pr_url = runner.get("pr_urls.leader")
    if not pr_url:
        print("✓ No PR URL found for leader, skipping submission - continuing")
        return None

    # Get submission data from worker
    url = f"{worker.get('url')}/submission/{runner.get('task_id')}/{runner.get('current_round')}"
    response = requests.get(url)
    response.raise_for_status()
    submission_data = response.json()

    # Create signature for the submission
    submitter_payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "action": "audit",
        "githubUsername": worker.get_env("GITHUB_USERNAME"),
        "prUrl": submission_data.get("prUrl"),
    }

    return {
        **submission_data,
        "signature": create_signature(
            worker.get_key("staking_signing"), submitter_payload
        ),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
    }


def execute(runner, worker, data):
    """Store leader submission data"""
    # If prepare returned None, skip this step
    if data is None:
        return {"success": True, "message": "Skipped due to missing PR URL"}

    # Store submission data in state
    runner.set("submission_data.leader", data, scope="round")

    # Return success result
    return {"success": True, "data": data}
