"""Utilities for recording PR URLs with the middle server."""

import os
import requests
from prometheus_swarm.utils.logging import log_key_value, log_error


def post_pr_url_to_middle_server(
    pr_url: str,
    signature: str,
    pub_key: str,
    staking_key: str,
    uuid: str,
    is_final: bool,
    is_issue: bool = False,
) -> bool:
    """Post PR URL to middle server.

    Args:
        pr_url: The URL of the pull request
        signature: The signature to use for authentication
        pub_key: The public key to use for authentication
        staking_key: The staking key to use for authentication
        uuid: The UUID of the todo/issue
        is_final: Whether this is the final PR or a draft
        is_issue: Whether this is an issue PR (True) or todo PR (False)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare the payload
        payload = {
            "signature": signature,
            "pubKey": pub_key,
            "stakingKey": staking_key,
            "prUrl": pr_url,
            "isFinal": is_final,
        }

        # Add UUID with correct key based on type
        if is_issue:
            payload["issueUuid"] = uuid
            endpoint = "/api/builder/add-issue-pr"
        else:
            payload["todo_uuid"] = uuid
            endpoint = "/api/builder/add-pr-to-to-do"

        # Make request to middle server
        response = requests.post(
            os.environ["MIDDLE_SERVER_URL"] + endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            log_key_value("PR URL saved to middle server", pr_url)
            return True
        else:
            log_error(
                Exception(f"Failed to save PR URL: {response.text}"),
                "Middle server request failed",
            )
            return False

    except Exception as e:
        log_error(e, "Failed to save PR URL to middle server")
        return False
