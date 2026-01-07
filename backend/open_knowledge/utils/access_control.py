from typing import Any, Optional, Dict


def has_permission(
    user_id: str,
    permission_key: str,
    default_permissions: Dict[str, Any] = {}
) -> bool:
    """
    Check if a user has a specific permission by checking the group permissions
    and fall back to default permissions if not found in any group.

    Permission keys can be hierarchical and separated by dot ('.').
    """
    # TODO
    return True


def has_access(
    user_id: str,
    type: str = "write",
    access_control: Optional[dict] = None,
) -> bool:
    # TODO: Always return True, which means no permission checking now
    return True
