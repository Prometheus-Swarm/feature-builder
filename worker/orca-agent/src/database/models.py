"""Database models."""

from sqlmodel import SQLModel, Field
from typing import Optional


class Submission(SQLModel, table=True):
    """Task submission model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    bounty_id: str = Field(index=True)
    task_id: str = Field(index=True)
    round_number: int
    status: str = "pending"
    pr_url: Optional[str] = None
    username: Optional[str] = None
    repo_owner: str
    repo_name: str
    uuid: Optional[str] = None  # UUID of the issue/todo
    node_type: str = "worker"  # Either "worker" or "leader"
