"""
Common Validators for SSH MCP Remote Exec

Shared validation functions used across multiple layers and Pydantic models.
"""


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
