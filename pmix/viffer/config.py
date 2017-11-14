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
            # - Uncomment to add type checking.
            # 'type': int,
            'length': 5,
            'null_character': '-'
        }
    },
    'reporting': {
        'missing_column_token': 'N/A',
        'missing_value_token': '.',
    }
}
MISSING_COL_TOKEN = DIFFER_BY_ID_CONFIG['reporting']['missing_column_token']
MISSING_VAL_TOKEN = DIFFER_BY_ID_CONFIG['reporting']['missing_value_token']
EMPTY_TOKENS = (MISSING_COL_TOKEN, MISSING_VAL_TOKEN)
