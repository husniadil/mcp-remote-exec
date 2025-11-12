"""
Presentation Layer Validators

Re-exports common validators for backward compatibility.
New code should import directly from mcp_remote_exec.common.validators.
"""

from mcp_remote_exec.common.validators import validate_octal_permissions

__all__ = ["validate_octal_permissions"]
