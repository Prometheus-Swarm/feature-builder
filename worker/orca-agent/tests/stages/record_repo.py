"""Stage for recording the aggregator repository."""

import requests
from prometheus_test.utils import create_signature


def prepare(runner, worker):
    """Prepare data for recording aggregator info"""
    # Check required state values
    fork_url = runner.get("fork_url")
    issue_uuid = runner.get("issue_uuid")
    if not fork_url or not issue_uuid:
        raise ValueError("Fork URL or Issue UUID not found in state")

    # Create payload with all required fields
    payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "action": "create-repo",
        "githubUsername": worker.get_env("GITHUB_USERNAME"),
        "issueUuid": issue_uuid,
        "aggregatorUrl": fork_url,
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
    }

    return {
        **payload,
        "signature": create_signature(worker.get_key("staking_signing"), payload),
    }


def execute(runner, worker, data):
    """Execute recording of aggregator info"""
    url = f"{worker.get('url')}/add-aggregator-info/{data['taskId']}"
    response = requests.post(url, json=data)
    return response.json()
