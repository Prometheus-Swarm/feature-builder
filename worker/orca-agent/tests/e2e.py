"""End-to-end test for the builder task."""

from pathlib import Path
from prometheus_test import TestRunner
import dotenv
import argparse
import uuid
from .steps import steps


dotenv.load_dotenv()


def parse_args():
    parser = argparse.ArgumentParser(description="Run builder test sequence")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Force reset of all databases before running tests",
    )
    return parser.parse_args()


def add_uuids(db):
    """Post-load callback to process MongoDB data after JSON import"""
    issues = list(db.issues.find({"taskId": runner.get("task_id")}))
    # Create a mapping of bounty ID to issue UUID
    bounty_to_issue = {}
    for issue in issues:
        if "uuid" not in issue:
            issue["uuid"] = str(uuid.uuid4())
        if "bountyId" in issue:
            bounty_to_issue[issue["bountyId"]] = issue["uuid"]
        db.issues.replace_one({"_id": issue["_id"]}, issue)

    # Process todos collection
    todos = list(db.todos.find({"taskId": runner.get("task_id")}))

    # First pass: generate UUIDs and create title mapping
    todo_mapping = {}
    for todo in todos:
        if "uuid" not in todo:
            todo["uuid"] = str(uuid.uuid4())
        todo_mapping[todo["title"]] = todo["uuid"]

    # Second pass: link dependencies and issues
    for todo in todos:
        # Link to issue based on bounty ID
        if (
            "issueUuid" not in todo
            and "bountyId" in todo
            and todo["bountyId"] in bounty_to_issue
        ):
            todo["issueUuid"] = bounty_to_issue[todo["bountyId"]]
        elif "issueUuid" not in todo and issues:
            # Fallback to first issue only if no bounty ID match found
            todo["issueUuid"] = issues[0]["uuid"]

        # Process dependencies
        if "dependencyTasks" in todo:
            todo["dependencyTasks"] = [
                todo_mapping.get(title, title) for title in todo["dependencyTasks"]
            ]

        # Update the todo in database
        db.todos.replace_one({"_id": todo["_id"]}, todo)


# Global reference to the test runner
runner = None


def main():
    global runner
    args = parse_args()

    # Create test runner with config from YAML
    base_dir = Path(__file__).parent
    runner = TestRunner(
        steps=steps,
        config_file=base_dir / "config.yaml",
        config_overrides={"post_load_callback": add_uuids},
    )

    # Run test sequence
    runner.run(force_reset=args.reset)


if __name__ == "__main__":
    main()
