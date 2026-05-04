import uuid


def get_random_filename(extension: str) -> str:
    """Generate a random filename using a UUID.

    Args:
        extension: File extension including the leading dot (e.g. ``.txt``, ``.png``).

    Returns:
        A random filename string in the format ``<uuid><extension>``.

    Example:
        >>> get_random_filename(".txt")
        "550e8400-e29b-41d4-a716-446655440000.txt"
    """
    return f"{uuid.uuid4()}{extension}"
