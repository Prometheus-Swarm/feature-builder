import requests
from prometheus_test.utils import create_signature
import os


def prepare(runner, worker):
    """Prepare data for worker PR recording"""
    pr_url = runner.get(f"pr_urls.{worker.get('name')}")
    submission_data = runner.get(f"submission_data.{worker.get('name')}")

    if pr_url is None or submission_data is None:
        print(
            f"✓ No PR URL or submission data found for {worker.get('name')} - continuing"
        )
        return None

    # Create payload for PR recording
    payload = {
        "taskId": runner.get("task_id"),
        "action": "add-todo-pr",
        "roundNumber": runner.get("current_round"),
        "isFinal": True,
        "prUrl": pr_url,
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "todo_uuid": submission_data.get("uuid"),
    }

    return {
        "signature": create_signature(worker.get_key("staking_signing"), payload),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "prUrl": pr_url,
        "isFinal": True,
        "todo_uuid": submission_data.get("uuid"),
    }


def execute(runner, worker, data):
    """Execute worker PR recording step"""
    if not data:
        return {"success": True, "message": "No PR URL found"}

    # Send PR to middle server with all required fields
    url = f"{os.getenv('MIDDLE_SERVER_URL')}/api/builder/add-pr-to-to-do"
    response = requests.post(url, json=data)
    result = response.json()

    # Handle 409 gracefully - no eligible todos is an expected case
    if response.status_code == 409:
        print(
            f"✓ {result.get('message', 'No eligible todos')} for {worker.get('name')} - continuing"
        )
        return {"success": True, "message": result.get("message")}

    if not response.ok:
        print(
            f"✗ Failed to record PR for {worker.get('name')}: {result.get('error', 'Unknown error')}"
        )
        return {"success": False, "message": result.get("error", "Unknown error")}

    print(f"✓ PR recorded successfully for {worker.get('name')}")
    return {"success": True, "message": "PR recorded successfully"}
