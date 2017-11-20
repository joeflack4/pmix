"""Abstract functions and classes."""


# # Functions
def non_empties(*args):
    """Get set of all non-empty elements in iterables."""
    args = args[0] if len(args) is 1 and isinstance(args[0], list) else args
    return [ne_set(i) for i in args]


def non_empty_pair(*args):
    """Get set of all non-empty elements in iterables."""
    return ne_set(args[0]), ne_set(args[1])


def ne_set(x):
    """Get set of all non-empty elements in iterable."""
    return set(i for i in x if i)


def de_list_pair(x, y=None):
    """De-list pair."""
    if isinstance(x, list) and not y:
        return x[0], x[1]
    return x, y


def intersect(x, y=None):
    """Get sorted list of elements in common between two iterables."""
    x, y = de_list_pair(x, y)
    return sorted(list(set(x) & set(y)))


def ne_intersect(x, y):
    """Get sorted list of elements in common in two iterables, sans empties."""
    return intersect(ne_set(x), ne_set(y))


def union(x, y=None):
    """Get sorted list of elements combined for two iterables."""
    x, y = de_list_pair(x, y)
    return sorted(list(set(x) | set(y)))


def ne_union(x, y):
    """Get sorted list of elements for two iterables, sans empties."""
    return union(ne_set(x), ne_set(y))


def exclusive(x, y=None):
    """Get sorted list of uncommon elements in two iterables."""
    x, y = de_list_pair(x, y)
    return sorted(list(set(x) ^ set(y)))


def ne_dict(dictionary):
    """Prune dictionary of empty key-value pairs."""
    return {k: v for k, v in dictionary.items() if v}


def pruned(dictionary):
    """Prune dictionary of empty key-value pairs."""
    return ne_dict(dictionary)


def prune_by_n_required_children(dictionary, n=1):
    """Return with only key value pairs that meet required n children."""
    return {key: val for key, val in dictionary.items() if len(val) >= n}

def prune_rows_by_missing_field_value(ws, index):
    """Remove rows without any id."""
    return [row for row in ws if row[index] is not None]