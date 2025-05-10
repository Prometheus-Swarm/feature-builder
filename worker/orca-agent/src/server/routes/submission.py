from flask import Blueprint, jsonify
from src.database import get_db, Submission
from prometheus_swarm.utils.logging import logger

bp = Blueprint("submission", __name__)


@bp.get("/submission/<task_id>/<round_number>")
def fetch_submission(task_id, round_number):
    """Fetch submission for a given round and task.

    Query parameters:
        taskId: The task ID to fetch submission for
    """
    logger.info(f"Fetching submission for round: {round_number}")
    round_number = int(round_number)

    db = get_db()
    submission = (
        db.query(Submission)
        .filter(
            Submission.status == "completed",
        )
        .order_by(Submission.round_number.asc())
        .first()
    )

    if submission:
        db.query(Submission).filter(Submission.uuid == submission.uuid).update(
            {"status": "submitted"}
        )
        db.commit()

        return jsonify(
            {
                "bountyId": submission.bounty_id,
                "prUrl": submission.pr_url,
                "githubUsername": submission.username,
                "repoOwner": submission.repo_owner,
                "repoName": submission.repo_name,
                "nodeType": submission.node_type,
                "uuid": submission.uuid,
                "roundNumber": round_number,
            }
        )
    else:
        return jsonify({"message": "No submission"}), 409
