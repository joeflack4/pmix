"""Configuration settings for PPP package."""


differ_by_id_config = {
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