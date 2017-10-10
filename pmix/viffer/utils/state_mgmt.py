"""State management module."""
from sys import stderr, stdout

state = []  # pylint: disable=invalid-name
store = {'data': {}}  # pylint: disable=invalid-name
state.append(store)
# current_state = state[-1]
current_state = lambda: state[-1]  # pylint: disable=invalid-name
DATA = current_state()['data']


def assign(var, val):
    """Assign variable in state."""
    now = state[-1].copy()
    now[var] = val
    state.append(now)


def the(var):
    """Get variable from state."""
    return state[-1][var]


def print_state_history(toggle=True, output_stream='stdout'):
    """Print state history.

    TODO: Add printout of additions ('+') and deletions ('-') beneath each
      enumerated state change.
    """
    stream = stdout if output_stream == 'stdout' \
        else stderr if output_stream == 'stderr' else stdout
    if toggle:
        # print('\n\n'.join([str(n) for n in state]), file=stream)
        for i, val in enumerate(state):
            print(str(i) + ': ' + str(val), file=stream)
