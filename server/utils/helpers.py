def sanitize_input(value, max_length=500):
    """Basic input sanitization.

    Args:
        value (str): The input value to sanitize
        max_length (int): Maximum allowed length for the input

    Returns:
        str: The sanitized input value
    """
    if value is None:
        return None

    # Remove any non-printable characters
    value = "".join(char for char in value if char.isprintable())

    # Limit length
    return value[:max_length]
