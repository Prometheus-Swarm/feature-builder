"""Entry point for task workflow."""

from src.workflows.task.execution import TaskExecution
import dotenv
import uuid
from prometheus_swarm.utils.logging import configure_logging, swarm_bounty_id_var
from src.server.logging_setup import setup_remote_logging

dotenv.load_dotenv()


def main():
    """Run the task workflow."""
    # Configure logging
    configure_logging()
    setup_remote_logging()

    # Generate a test bounty ID
    test_bounty_id = str(uuid.uuid4())
    swarm_bounty_id_var.set(test_bounty_id)

    execution = TaskExecution()
    execution.start(
        leader_token_env_var="LEADER_GITHUB_TOKEN",
        leader_username_env_var="LEADER_GITHUB_USERNAME",
        worker_token_env_var="WORKER1_GITHUB_TOKEN",
        worker_username_env_var="WORKER1_GITHUB_USERNAME",
    )


if __name__ == "__main__":
    main()
