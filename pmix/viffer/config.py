"""Configuration settings for PPP package."""


DIFFER_BY_ID_CONFIG = {
    'output': {
        'state_history': {
            'stream': 'stderr',
            'value': False
        },
        'warnings': {
            'stream': 'stderr',
            'value': False
        }
    },
    'validation': {
        'id': {
            'type': int,
            'length': 5,
            'null_character': '-'
        }
    }
}
