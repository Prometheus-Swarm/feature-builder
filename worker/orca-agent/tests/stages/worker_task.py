"""Stage for executing worker tasks."""

import requests
from prometheus_test.utils import create_signature


def prepare(runner, worker):
    """Prepare data for worker task"""
    # Create fetch-todo payload for stakingSignature and publicSignature
    fetch_todo_payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "action": "fetch-todo",
        "githubUsername": worker.get_env("GITHUB_USERNAME"),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
    }

    # Create add-pr payload for addPRSignature
    add_pr_payload = {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "action": "add-todo-pr",
        "githubUsername": worker.get_env("GITHUB_USERNAME"),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "isFinal": False,
    }

    return {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "stakingKey": worker.get_key("staking_public"),
        "pubKey": worker.get_key("main_public"),
        "stakingSignature": create_signature(
            worker.get_key("staking_signing"), fetch_todo_payload
        ),
        "publicSignature": create_signature(
            worker.get_key("main_signing"), fetch_todo_payload
        ),
        "addPRSignature": create_signature(
            worker.get_key("staking_signing"), add_pr_payload
        ),
    }


def execute(runner, worker, data):
    """Execute worker task step"""
    url = f"{worker.get('url')}/worker-task/{data['roundNumber']}"
    response = requests.post(url, json=data)
    result = response.json()

    # Handle 409 gracefully - no eligible todos is an expected case
    if response.status_code == 409:
        print(
            f"✓ {result.get('message', 'No eligible todos')} for {worker.get('name')} - continuing"
        )
        return {"success": True, "message": result.get("message")}

    if result.get("success") and "pr_url" in result:
        # Store PR URL in state
        runner.set(f"pr_urls.{worker.get('name')}", result["pr_url"], scope="round")

        # Store submission data
        submission_data = {
            "githubUsername": worker.get_env("GITHUB_USERNAME"),
            "nodeType": "worker",
            "prUrl": result["pr_url"],
            "repoName": result.get("repoName"),
            "repoOwner": result.get("repoOwner"),
            "roundNumber": runner.get("current_round"),
            "taskId": runner.get("task_id"),
            "uuid": result.get("uuid"),  # Should be provided by the worker
            "stakingKey": worker.get_key("staking_public"),
            "pubKey": worker.get_key("main_public"),
        }
        runner.set(
            f"submission_data.{worker.get('name')}", submission_data, scope="round"
        )

    return result
