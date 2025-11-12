"""
Common Validators for SSH MCP Remote Exec

Shared validation functions used across multiple layers and Pydantic models.
"""

from typing import Any


def validate_octal_permissions(v: int | None) -> int | None:
    """
    Validate that permissions value contains only octal digits (0-7).

    File permissions should be specified as decimal integer representing
    octal notation. For example:
    - 644 (rw-r--r--)
    - 755 (rwxr-xr-x)
    - 600 (rw-------)
    - 700 (rwx------)

    Args:
        v: Permission value to validate (or None)

    Returns:
        The validated permission value

    Raises:
        ValueError: If any digit is > 7 (invalid octal)
    """
    if v is None:
        return v

    # Check each digit is valid octal (0-7)
    for digit in str(v):
        if int(digit) > 7:
            raise ValueError(
                f"Invalid octal permission value: {v}. "
                "Each digit must be 0-7. Common values: 644 (rw-r--r--), "
                "755 (rwxr-xr-x), 600 (rw-------), 700 (rwx------)"
            )
    return v


def pydantic_permissions_field_validator(cls: Any, v: int | None) -> int | None:
    """
    Pydantic-compatible field validator for octal permissions.

    This is a reusable field validator that can be used with Pydantic's
    @field_validator decorator to validate permissions fields across models.

    Usage:
        from mcp_remote_exec.common.validators import pydantic_permissions_field_validator

        class MyModel(BaseModel):
            permissions: int | None = None

            # Use as field validator
            validate_permissions = field_validator("permissions")(
                pydantic_permissions_field_validator
            )

    Args:
        cls: Pydantic model class (automatically provided by decorator)
        v: Permission value to validate

    Returns:
        The validated permission value

    Raises:
        ValueError: If any digit is > 7 (invalid octal)
    """
    return validate_octal_permissions(v)
