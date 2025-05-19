from flask import Blueprint, jsonify, request
from src.server.services import task_service
from prometheus_swarm.utils.logging import logger
import requests
import os
from src.database import get_db, Submission
from concurrent.futures import ThreadPoolExecutor

bp = Blueprint("task", __name__)
executor = ThreadPoolExecutor(max_workers=2)

# Track in-progress tasks
in_progress_tasks = set()


def post_task_result(future, round_number, request_data, node_type, task_id):
    try:
        # Remove from in-progress tasks when done
        task_key = f"{node_type}_{round_number}"
        in_progress_tasks.discard(task_key)

        response = future.result()
        response_data = response.get("data", {})

        if not response.get("success", False):
            logger.error(f"Task failed: {response.get('error', 'Unknown error')}")
            return

        # Send PR URL back to JS side
        try:
            js_response = requests.post(
                f"http://host.docker.internal:30017/task/{task_id}/add-pr",
                json={
                    "prUrl": response_data["pr_url"],
                    "signature": request_data["addPRSignature"],
                    "success": True,
                    "action": (
                        "add-todo-pr" if node_type == "worker" else "add-issue-pr"
                    ),
                    "message": response_data.get(
                        "message", "Task completed successfully"
                    ),
                    "roundNumber": round_number,
                },
            )
            js_response.raise_for_status()
            logger.info(f"Successfully sent PR URL to JS side for task {task_id}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send PR URL to JS side: {str(e)}")

    except Exception as e:
        logger.error(f"Error in post_task_result: {str(e)}")
        if hasattr(e, "__traceback__"):
            import traceback

            logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")


@bp.post("/worker-task/<round_number>")
def start_worker_task(round_number):
    return start_task(round_number, "worker", request)


@bp.post("/leader-task/<round_number>")
def start_leader_task(round_number):
    return start_task(round_number, "leader", request)


@bp.post("/create-aggregator-repo/<task_id>")
def create_aggregator_repo(task_id):
    print("\n=== ROUTE HANDLER CALLED ===")
    print(f"task_id: {task_id}")

    # Create the aggregator repo (which now handles assign_issue internally)
    result = task_service.create_aggregator_repo()
    print(f"result: {result}")

    # Extract status code from result if present, default to 200
    status_code = result.pop("status", 200) if isinstance(result, dict) else 200
    return jsonify(result), status_code


@bp.post("/add-aggregator-info/<task_id>")
def add_aggregator_info(task_id):
    print("\n=== ADD AGGREGATOR INFO ROUTE HANDLER CALLED ===")
    print(f"task_id: {task_id}")
    request_data = request.get_json()
    print(f"request_data: {request_data}")
    if not request_data:
        return jsonify({"success": False, "error": "Invalid request body"}), 401

    # Call the task service to update aggregator info with the middle server
    result = task_service.add_aggregator_info(
        task_id,
        request_data.get("stakingKey"),
        request_data.get("pubKey"),
        request_data.get("signature"),
    )
    print(f"result: {result}")

    # Extract status code from result if present, default to 200
    status_code = result.pop("status", 200) if isinstance(result, dict) else 200
    return jsonify(result), status_code


def start_task(round_number, node_type, request):
    if node_type not in ["worker", "leader"]:
        return jsonify({"success": False, "message": "Invalid node type"}), 400

    task_functions = {
        "worker": task_service.complete_todo,
        "leader": task_service.consolidate_prs,
    }
    logger.info(f"{node_type.capitalize()} task started for round: {round_number}")

    request_data = request.get_json()
    logger.info(f"Task data: {request_data}")

    required_fields = [
        "roundNumber",
        "stakingKey",
        "stakingSignature",
        "pubKey",
        "publicSignature",
        "addPRSignature",
        "taskId",
    ]

    if any(request_data.get(field) is None for field in required_fields):
        missing_fields = [
            field for field in required_fields if request_data.get(field) is None
        ]
        logger.error(f"Missing required fields: {missing_fields}")
        return (
            jsonify({"success": False, "message": f"Missing data: {missing_fields}"}),
            401,
        )

    # Check if this task is already being processed
    task_key = f"{node_type}_{round_number}"
    if task_key in in_progress_tasks:
        return (
            jsonify({"success": False, "message": "Task is already being processed"}),
            409,
        )

    # Mark this task as in progress
    in_progress_tasks.add(task_key)

    # In test mode, run synchronously
    if os.getenv("TEST_MODE") == "true":
        try:
            # Call task function directly
            response = task_functions[node_type](
                task_id=request_data["taskId"],
                round_number=int(round_number),
                staking_signature=request_data["stakingSignature"],
                staking_key=request_data["stakingKey"],
                public_signature=request_data["publicSignature"],
                pub_key=request_data["pubKey"],
                pr_signature=request_data["addPRSignature"],
            )
            response_data = response.get("data", {})
            if not response.get("success", False):
                status = response.get("status", 500)
                error = response.get("error", "Unknown error")
                return jsonify({"success": False, "message": error}), status

            logger.info(response_data["message"])

            # Get the todo_uuid from the database
            db = get_db()
            submission = (
                db.query(Submission)
                .filter(
                    Submission.bounty_id == response_data["bounty_id"],
                    Submission.round_number == int(round_number),
                )
                .first()
            )
            if not submission or not submission.uuid:
                logger.error("No submission found or missing todo_uuid")
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "No submission found or missing todo_uuid",
                        }
                    ),
                    500,
                )

            # In test mode, just return the PR URL without recording it
            # The worker_pr step will handle recording with the middle server
            return jsonify(
                {
                    "success": True,
                    "message": "PR created successfully",
                    "pr_url": response_data["pr_url"],
                    "bounty_id": response_data["bounty_id"],
                    "uuid": submission.uuid,  # Get todo_uuid from submission
                }
            )
        finally:
            # Remove from in-progress tasks
            in_progress_tasks.discard(task_key)

    # Production mode - use background task
    future = executor.submit(
        task_functions[node_type],
        task_id=request_data["taskId"],
        round_number=int(round_number),
        staking_signature=request_data["stakingSignature"],
        staking_key=request_data["stakingKey"],
        public_signature=request_data["publicSignature"],
        pub_key=request_data["pubKey"],
        pr_signature=request_data["addPRSignature"],
    )

    # Add callback to handle the result
    future.add_done_callback(
        lambda f: post_task_result(
            f, round_number, request_data, node_type, request_data["taskId"]
        )
    )

    return jsonify({"status": "Task is being processed"}), 200


@bp.post("/update-audit-result/<task_id>/<round_number>")
def update_audit_result(task_id, round_number):
    try:
        # Convert round_number to integer
        round_number = int(round_number)

        response = requests.post(
            os.environ["MIDDLE_SERVER_URL"] + "/api/builder/update-audit-result",
            json={
                "taskId": task_id,
                "round": round_number,
            },
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()

        result = response.json()
        if not result.get("success", False):
            return (
                jsonify(
                    {
                        "success": False,
                        "message": result.get("message", "Unknown error"),
                    }
                ),
                500,
            )
        return jsonify({"success": True, "message": "Audit results processed"}), 200
    except ValueError:
        return jsonify({"success": False, "message": "Invalid round number"}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": str(e)}), 500


@bp.get("/check-availability")
def check_availability():
    """Check if there are any running tasks.

    Returns:
        bool: True if no running tasks, False if there is a running task
    """
    db = get_db()
    running_task = db.query(Submission).filter(Submission.status == "running").first()

    return jsonify({"available": running_task is None})
