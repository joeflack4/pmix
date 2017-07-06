"""State management module."""
from sys import stderr

state = []
store = {
    'data': {}
}
state.append(store)
# current_state = state[-1]
current_state = lambda: state[-1]
data = current_state()['data']


def assign(var, val):
    """Assign variable in state."""
    now = state[-1].copy()
    now[var] = val
    state.append(now)


def the(var):
    """Get variable from state."""
    return state[-1][var]


def print_state_history(toggle, output_stream='stdout'):
    """Print state history."""
    if toggle:
        if output_stream is 'stdout':
            print('\n\n'.join([str(n) for n in state]))
        elif output_stream is 'stderr':
            print('\n\n'.join([str(n) for n in state]), file=stderr)
