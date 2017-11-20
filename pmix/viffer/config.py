"""Configuration settings for PPP package."""


CONFIG = {
    'output': {
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
        'missing_record_token': 'N/A',
        'missing_column_token': 'N/A',
        'missing_value_token': '.',
        'which_ids': {
            1: 'all',
            2: 'shared'
        }[1],  # <- Select option here.
        'show_unchanged_rows': False,
        'make_faux_ids': True
    }
}
MISSING_COL_TOKEN = CONFIG['reporting']['missing_column_token']
MISSING_VAL_TOKEN = CONFIG['reporting']['missing_value_token']
MISSING_RECORD_TOKEN = CONFIG['reporting']['missing_record_token']
EMPTY_TOKENS = (MISSING_COL_TOKEN, MISSING_VAL_TOKEN)
SHOW_UNCHANGED = CONFIG['reporting']['show_unchanged_rows']
MAKE_FAUX_IDS = CONFIG['reporting']['make_faux_ids']
