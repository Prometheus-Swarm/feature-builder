"""Stage for creating the aggregator repository."""

import requests


def prepare(runner, worker):
    """Prepare data for creating a repository"""
    return {
        "taskId": runner.get("task_id"),
        "roundNumber": runner.get("current_round"),
        "action": "create-repo",
    }


def execute(runner, worker, data):
    """Execute repository creation step"""
    url = f"{worker.get('url')}/create-aggregator-repo/{data['taskId']}"
    response = requests.post(url, json=data)
    result = response.json()

    # Handle 409 gracefully - no eligible issues is an expected case
    if response.status_code == 409:
        print(f"✓ {result.get('message', 'No eligible issues')} - continuing")
        # Set flag to skip next step
        runner.set("no_repo", True, scope="round")
        return {"success": True, "message": result.get("message")}

    if result.get("success"):
        # Store repository data in state
        runner.set("fork_url", result["data"]["fork_url"], scope="global")
        runner.set("issue_uuid", result["data"]["issue_uuid"], scope="global")
        runner.set("branch_name", result["data"]["branch_name"], scope="global")
        runner.set("bounty_id", result["data"]["bounty_id"], scope="global")
        # Clear skip flag since we want to continue
        runner.set("skip_next_step", False, scope="round")

    return result
