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
    print("Running add_uuids...")
    issues = list(db.issues.find({"taskId": runner.get("task_id")}))
    print(f"Found {len(issues)} issues")

    # Create a mapping of bounty ID to issue UUID
    bounty_to_issue = {}
    for issue in issues:
        print(
            f"Processing issue: {issue.get('title')} with current UUID: {issue.get('uuid')}"
        )
        if "uuid" not in issue:
            issue["uuid"] = str(uuid.uuid4())
            print(f"Generated new UUID: {issue['uuid']}")
        if "bountyId" in issue:
            bounty_to_issue[issue["bountyId"]] = issue["uuid"]
        db.issues.replace_one({"_id": issue["_id"]}, issue)
        print(f"Updated issue in database with UUID: {issue['uuid']}")

    # Process todos collection
    todos = list(db.todos.find({"taskId": runner.get("task_id")}))
    print(f"Found {len(todos)} todos")

    # First pass: generate UUIDs and create title mapping
    todo_mapping = {}
    for todo in todos:
        print(
            f"Processing todo: {todo.get('title')} with current UUID: {todo.get('uuid')}"
        )
        if "uuid" not in todo:
            todo["uuid"] = str(uuid.uuid4())
            print(f"Generated new UUID: {todo['uuid']}")
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
            print(
                f"Linked todo {todo.get('title')} to issue with UUID: {todo['issueUuid']}"
            )
        elif "issueUuid" not in todo and issues:
            # Fallback to first issue only if no bounty ID match found
            todo["issueUuid"] = issues[0]["uuid"]
            print(
                f"Linked todo {todo.get('title')} to first issue with UUID: {todo['issueUuid']}"
            )

        # Process dependencies
        if "dependencyTasks" in todo:
            todo["dependencyTasks"] = [
                todo_mapping.get(title, title) for title in todo["dependencyTasks"]
            ]
            print(
                f"Updated dependencies for todo {todo.get('title')}: {todo['dependencyTasks']}"
            )

        # Update the todo in database
        db.todos.replace_one({"_id": todo["_id"]}, todo)
        print(f"Updated todo in database with UUID: {todo.get('uuid')}")


def replace_placeholder_uuids(db):
    """Post-load callback to replace placeholder UUIDs with actual UUIDs.

    This callback collects all unique IDs from issues, todos, and prompts,
    creates mappings to new UUIDs, and then applies those mappings to update
    all collections while maintaining relationships.
    """
    print("Running replace_placeholder_uuids...")

    # Collect all unique IDs
    issue_uuids = set()
    todo_uuids = set()
    bounty_ids = set()

    # Collect from issues
    issues = list(db.issues.find({}))
    for issue in issues:
        if "uuid" in issue:
            issue_uuids.add(issue["uuid"])
        if "bountyId" in issue:
            bounty_ids.add(issue["bountyId"])
        if "predecessorUuid" in issue:
            issue_uuids.add(issue["predecessorUuid"])

    # Collect from todos
    todos = list(db.todos.find({}))
    for todo in todos:
        if "uuid" in todo:
            todo_uuids.add(todo["uuid"])
        if "bountyId" in todo:
            bounty_ids.add(todo["bountyId"])
        if "issueUuid" in todo:
            issue_uuids.add(todo["issueUuid"])
        if "dependencyTasks" in todo:
            todo_uuids.update(todo["dependencyTasks"])

    # Collect from prompts
    prompts = list(db.systemprompts.find({}))
    print(f"\nFound {len(prompts)} prompts")
    print("Prompts in database:")
    for prompt in prompts:
        print(f"Prompt: {prompt}")
        if "bountyId" in prompt:
            bounty_ids.add(prompt["bountyId"])

    # Create mappings
    issue_uuid_mapping = {old: str(uuid.uuid4()) for old in issue_uuids}
    todo_uuid_mapping = {old: str(uuid.uuid4()) for old in todo_uuids}
    bounty_id_mapping = {old: f"bounty-{str(uuid.uuid4())[:8]}" for old in bounty_ids}

    print("\nID mappings created:")
    print("\nIssue UUID mapping:")
    for old, new in issue_uuid_mapping.items():
        print(f"{old} -> {new}")
    print("\nTodo UUID mapping:")
    for old, new in todo_uuid_mapping.items():
        print(f"{old} -> {new}")
    print("\nBounty ID mapping:")
    for old, new in bounty_id_mapping.items():
        print(f"{old} -> {new}")

    # Update issues
    print("\nUpdating issues...")
    for issue in issues:
        updates = {}
        if "uuid" in issue:
            updates["uuid"] = issue_uuid_mapping[issue["uuid"]]
        if "bountyId" in issue:
            updates["bountyId"] = bounty_id_mapping[issue["bountyId"]]
        if "predecessorUuid" in issue:
            updates["predecessorUuid"] = issue_uuid_mapping[issue["predecessorUuid"]]

        if updates:
            db.issues.update_one({"_id": issue["_id"]}, {"$set": updates})
            print(f"Updated issue {issue.get('title')}: {updates}")

    # Update todos
    print("\nUpdating todos...")
    for todo in todos:
        updates = {}
        if "uuid" in todo:
            updates["uuid"] = todo_uuid_mapping[todo["uuid"]]
        if "bountyId" in todo:
            updates["bountyId"] = bounty_id_mapping[todo["bountyId"]]
        if "issueUuid" in todo:
            updates["issueUuid"] = issue_uuid_mapping[todo["issueUuid"]]
        if "dependencyTasks" in todo:
            updates["dependencyTasks"] = [
                todo_uuid_mapping[dep] if dep in todo_uuid_mapping else dep
                for dep in todo["dependencyTasks"]
            ]

        if updates:
            db.todos.update_one({"_id": todo["_id"]}, {"$set": updates})
            print(f"Updated todo {todo.get('title')}: {updates}")

    # Update prompts
    print("\nUpdating prompts...")
    for prompt in prompts:
        if "bountyId" in prompt:
            old_bounty_id = prompt["bountyId"]
            new_bounty_id = bounty_id_mapping[old_bounty_id]
            print(f"Updating prompt bountyId from {old_bounty_id} to {new_bounty_id}")

            # Create a new document with the updated bountyId
            updated_prompt = prompt.copy()
            updated_prompt["bountyId"] = new_bounty_id

            # Replace the entire document
            result = db.systemprompts.replace_one(
                {"_id": prompt["_id"]}, updated_prompt
            )
            print(
                f"Update result - matched: {result.matched_count}, modified: {result.modified_count}"
            )

            # Verify the update
            updated_prompt = db.systemprompts.find_one({"_id": prompt["_id"]})
            print(f"Verified prompt bountyId: {updated_prompt.get('bountyId')}")


def handle_uuids(db):
    """Post-load callback that checks for UUIDs and calls the appropriate function.

    If any issue has a UUID, assumes all UUIDs are provided and calls replace_placeholder_uuids.
    Otherwise, calls add_uuids to generate UUIDs for all issues.
    """
    print("\nStarting handle_uuids...")
    # Check if any issue has a UUID
    issues = list(db.issues.find({"taskId": runner.get("task_id")}))
    print(f"Found {len(issues)} issues")
    if not issues:
        print("No issues found, returning")
        return

    # Check if the first issue has a UUID
    print(f"First issue UUID: {issues[0].get('uuid')}")
    if "uuid" in issues[0]:
        print("UUID found, calling replace_placeholder_uuids")
        replace_placeholder_uuids(db)
    else:
        print("No UUID found, calling add_uuids")
        add_uuids(db)


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
        config_overrides={"post_load_callback": handle_uuids},
    )

    # Run test sequence
    runner.run(force_reset=args.reset)


if __name__ == "__main__":
    main()
