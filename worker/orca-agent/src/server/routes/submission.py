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
    # First find any completed submission
    initial_submission = (
        db.query(Submission)
        .filter(
            Submission.task_id == task_id,
            Submission.status == "completed",
        )
        .order_by(Submission.round_number.asc())
        .first()
    )

    if initial_submission:
        # Find all completed submissions with the same UUID
        all_submissions = (
            db.query(Submission)
            .filter(
                Submission.uuid == initial_submission.uuid,
                Submission.status == "completed",
            )
            .order_by(Submission.round_number.desc())
            .all()
        )

        if not all_submissions:
            return jsonify({"message": "No submission"}), 409

        # Get the newest submission (highest round number)
        newest_submission = all_submissions[0]

        # Mark older submissions as failed
        for sub in all_submissions[1:]:
            db.query(Submission).filter(
                Submission.uuid == sub.uuid, Submission.round_number == sub.round_number
            ).update({"status": "failed"})

        # Mark the newest submission as submitted
        db.query(Submission).filter(
            Submission.uuid == newest_submission.uuid,
            Submission.round_number == newest_submission.round_number,
        ).update({"status": "submitted"})

        db.commit()

        return jsonify(
            {
                "bountyId": newest_submission.bounty_id,
                "prUrl": newest_submission.pr_url,
                "githubUsername": newest_submission.username,
                "repoOwner": newest_submission.repo_owner,
                "repoName": newest_submission.repo_name,
                "nodeType": newest_submission.node_type,
                "uuid": newest_submission.uuid,
                "roundNumber": round_number,
            }
        )
    else:
        return jsonify({"message": "No submission"}), 409
