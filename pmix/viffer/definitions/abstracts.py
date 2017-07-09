"""Functions."""


def in_common(x, y):
    """Get list of elements in common between two iterables."""
    return list(set(x) & set(y))
