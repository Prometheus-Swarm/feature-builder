"""Stage for updating audit results."""

import requests
from prometheus_test.utils import create_signature


def prepare(runner, worker, role: str):
    """Prepare data for updating audit results"""
    # Create payload with all required fields
    payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "role": role,
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "bountyId": runner.get("bounty_id"),
    }
    print(f"payload: {payload}")

    return {
        **payload,
        "stakingSignature": create_signature(
            worker.get_key("staking_signing"), payload
        ),
    }


def execute(runner, worker, data):
    """Execute audit results update"""
    url = f"{worker.get('url')}/update-audit-result/{runner.get('task_id')}/{data['roundNumber']}"

    # Structure the payload according to what the server expects
    payload = {
        "taskId": runner.get("task_id"),
        "round": data["roundNumber"],
        "auditType": data["role"],
    }

    response = requests.post(url, json=payload)
    result = response.json()

    if not result.get("success", False):
        raise Exception(
            f"Update audit result failed: {result.get('message', 'Unknown error')}"
        )

    return result
