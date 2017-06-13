#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff by ID - Report on differences between XLSForms by ID comparison."""
import pandas as pd
from sys import stderr, stdout
from copy import copy
from pmix.viffer.config import CONFIG as CONFIG, MISSING_RECORD_TOKEN, \
    MISSING_COL_TOKEN, MISSING_VAL_TOKEN, EMPTY_TOKENS, SHOW_UNCHANGED, \
    MAKE_FAUX_IDS
from pmix.viffer.interfaces.cli import cli
from pmix.viffer.definitions.constants import RELEVANT_WORKSHEETS
from pmix.viffer.definitions.errors import VifferError
from pmix.viffer.definitions.abstractions import intersect, \
    prune_rows_by_missing_field_value
from pmix.viffer.utils.two_dim_array_to_csv import two_dim_arr_to_csv
from pmix.xlsform import Xlsform


HEADER = ['worksheet', 'id', 'current_name', 'current_lab', 'field', 'old',
          'new', 'different?']
PRINT_WARNINGS = CONFIG['output']['warnings']
VALID_ID = CONFIG['validation']['id']
VALID_ID_MSG = '  * Type: {}\n  * Length: {}\n  * Null character: {}'\
    .format(VALID_ID['type'] if 'type' in VALID_ID else 'Any',
            VALID_ID['length'], VALID_ID['null_character'])
warnings = {  # pylint: disable=invalid-name
    'invalid_id': {
        'value': False,
        'message': 'One or more IDs were malformed. Valid IDs are as follows.'
                   '\n' + VALID_ID_MSG
    },
    'invalid_id_length_warning': {
        'value': False,
        'message': 'One or more ID with an invalid length was found. Valid IDs'
                   ' are as follows.\n' + VALID_ID_MSG
    },
    'inconsistent_worksheet_headers': {
        'value': False,
        'message': 'Worksheet \'{}\' has inconsistent fields. The following '
                   'fields were only found in 1 out of 2 worksheets: {}.'
    }
}
data = {}  # pylint: disable=invalid-name


def to_csv(args):
    """To CSV."""
    xlsforms = [Xlsform(file) for file in args.files]
    new_form, original_form = xlsforms[1], xlsforms[0]
    report = [copy(HEADER)]

    ws_lists = get_worksheet_lists_with_ids(original_form=original_form,
                                            new_form=new_form)  # -> 1
    common_relevant_ws_list = intersect(ws_lists, RELEVANT_WORKSHEETS)

    for ws in common_relevant_ws_list:
        old_ws, new_ws = get_worksheets_by_name(ws_name=ws,  # -> 2
                                                original_form=original_form,
                                                new_form=new_form)

        # -> 2.5
        if MAKE_FAUX_IDS:
            old_ws, new_ws = make_faux_ids(old_ws), make_faux_ids(new_ws)

        old_ids, new_ids = get_ws_ids(old_ws), get_ws_ids(new_ws)  # -> 3

        id_list = []
        if CONFIG['reporting']['which_ids'] == 'all':
            id_list = sorted(set(old_ids + new_ids))
        elif CONFIG['reporting']['which_ids'] == 'shared':
            id_list = sorted(intersect(old_ids, new_ids))

        old_fields = [cell.value or None for cell in old_ws[0]]
        new_fields = [cell.value or None for cell in new_ws[0]]
        all_fields = [field for field in set(old_fields + new_fields) if field
                      is not None]

        # -> 4
        old_ws, new_ws = formatted_ws_data(old_ws), formatted_ws_data(new_ws)

        report += compare_by_worksheet(report_schema=HEADER,  # -> 5
                                       ws_name=ws,
                                       old_fields=old_fields,
                                       new_fields=new_fields,
                                       all_fields=all_fields,
                                       id_list=id_list,
                                       old_ws=old_ws,
                                       new_ws=new_ws)

    if not SHOW_UNCHANGED:  # Delete 'different?' row.
        for row in report:
            del row[-1]
    result = two_dim_arr_to_csv(report)

    return result


def get_worksheet_lists_with_ids(original_form, new_form):  # 1
    """Get worksheet lists.
    Side effects:
        validate()
    """
    original_form_list = [ws.name for ws in original_form.data
                          if 'id' in ws.header]
    new_form_list = [ws.name for ws in new_form.data if 'id' in ws.header]
    ws_lists_with_ids = list(set(original_form_list) & set(new_form_list))
    validate(validation_type='id', _data=ws_lists_with_ids)  # -> 1.a
    return ws_lists_with_ids


def validate(validation_type=None, _data=None):  # 1.a
    """Validate."""
    default_validations = {
        'id': ''
    }
    validations = {
        validation_type: _data
    }
    if not validation_type and not _data:
        validations = default_validations
    if 'id' in validations:
        err = 'Both workbooks being compared must have 1 or more worksheets ' \
              'of the same name where both worksheets have an \'id\' column.'
        if not validations['id']:
            raise VifferError(err)


def get_worksheets_by_name(ws_name, original_form, new_form):  # 2
    """Get worksheets."""
    original_form_ws = original_form[ws_name]
    new_form_ws = new_form[ws_name]
    return original_form_ws, new_form_ws


def make_faux_ids(ws):  # 2.5
    """Mkae feaux ids."""
    id_index = ws.header.index('id')
    for row in ws.data[1:]:
        if not row[id_index].value:
            if ws.name == 'survey':
                row[id_index].value = str(row[ws.header.index('name')].value)
            elif ws.name == 'choices':
                row[id_index].value = \
                    str(row[ws.header.index('list_name')].value) + ' ' \
                    + str(row[ws.header.index('name')].value)
            else:
                raise VifferError('Unhandled worksheet: {}'.format(ws.name))
    return ws


def get_ws_ids(ws):  # 3
    """Get all component IDs in worksheet.
    Side effects:
        validate()
    """
    ids = []
    id_index = ws.header.index('id')

    for row in ws.data[1:]:
        val = row[id_index].value
        if 'type' in CONFIG['validation']['id']:
            if not isinstance(val, VALID_ID['type']) \
                    and val is not VALID_ID['null_character']:
                warnings['invalid_id']['value'] = True
            if isinstance(val, VALID_ID['type']) \
                    and val is not VALID_ID['null_character']:
                ids.append(val)
        else:
            if val not in (None, VALID_ID['null_character']):
                ids.append(val)

            if len(str(val)) is not VALID_ID['length']:
                warnings['invalid_id_length_warning']['value'] = True

    return sorted([str(_id) for _id in ids])


def formatted_ws_data(ws):  # 4
    """Format worksheet."""
    formatted_ws = [[str(cell.value) for cell in row] for row in ws]
    id_col_index = formatted_ws.pop(0).index('id')
    # id_col_index = formatted_ws[0].index('id')
    filtered_ws = prune_rows_by_missing_field_value(formatted_ws, id_col_index)
    return sorted(filtered_ws, key=lambda x: x[id_col_index])


def compare_by_worksheet(report_schema, ws_name, old_fields, new_fields,
                         all_fields, id_list, old_ws, new_ws):  # 5
    """Compare changes by worksheet."""
    ws_data = []
    report_indexes = \
        {col_name: report_schema.index(col_name) for col_name in report_schema}
    old_field_indexes = \
        {col_name: old_fields.index(col_name) for col_name in old_fields}
    new_field_indexes = \
        {col_name: new_fields.index(col_name) for col_name in new_fields}

    old_ws_array, new_ws_array = pd.DataFrame(old_ws), pd.DataFrame(new_ws)

    for _id in id_list:

        for field in all_fields:

            row = [col_name for col_name in report_schema]

            # TODO: Make a config, and set it to ignore by default rows that
            # have not changed.
            # TODO: Intersect instead of set() in all_fields ?
            # TODO: On top of returning "N/A", also print out a report/warning
            #  for fields that are in one file but not in the other.
            old_record = old_ws_array.loc[
                old_ws_array[old_field_indexes['id']] == str(_id)]

            # TODO: Bug. Somewhere below here, issue is occurring where after
            # missing 15002, 15003 which is in common shows "N/A" as original
            # value for all fields.

            try:
                old_row_num = old_record.index[0]
                if field in old_field_indexes:
                    old_field_val = \
                        old_record[old_field_indexes[field]].get(old_row_num)
                    # If no value
                    old_field_val = \
                        old_field_val.replace('None', MISSING_VAL_TOKEN)
                else:  # If column doesn't exist
                    old_field_val = MISSING_COL_TOKEN
            except IndexError:  # If id not in worksheet
                old_field_val = MISSING_RECORD_TOKEN

            new_record = new_ws_array.loc[
                new_ws_array[new_field_indexes['id']] == str(_id)]

            try:
                new_row_num = new_record.index[0]
                if field in new_field_indexes:
                    new_field_val = \
                        new_record[new_field_indexes[field]].get(new_row_num)
                    # If no value
                    new_field_val = \
                        new_field_val.replace('None', MISSING_VAL_TOKEN)
                else:  # If column doesn't exist
                    new_field_val = MISSING_COL_TOKEN
            except IndexError:  # If id not in worksheet
                new_row_num, new_field_val = None, MISSING_RECORD_TOKEN

            # TODO: Change "label::English" to default language.
            row[report_indexes['worksheet']] = ws_name
            row[report_indexes['id']] = str(_id)
            row[report_indexes['current_name']] = \
                new_record[new_field_indexes['name']] \
                .get(new_row_num) if new_row_num is not None \
                else MISSING_RECORD_TOKEN
            row[report_indexes['current_lab']] = \
                new_record[new_field_indexes['label::English']] \
                .get(new_row_num) if new_row_num is not None \
                else MISSING_RECORD_TOKEN
            row[report_indexes['field']] = field
            row[report_indexes['old']] = \
                old = old_field_val if old_field_val else MISSING_VAL_TOKEN
            row[report_indexes['new']] = \
                new = new_field_val if new_field_val else MISSING_VAL_TOKEN
            row[report_indexes['different?']] = is_diff = \
                str(False) if old in EMPTY_TOKENS and new in EMPTY_TOKENS \
                else str(old != new)

            if is_diff == str(True) \
                    or is_diff == str(False) and SHOW_UNCHANGED:
                ws_data.append(row)

    return ws_data


def print_warnings(toggle=True, output_stream='stdout'):
    """Print warnings."""
    stream = stdout if output_stream == 'stdout' \
        else stderr if output_stream == 'stderr' else stdout
    warnings_to_print = []
    for key, val in warnings.items():
        if val['value'] is True:
            warnings_to_print.append('* {}: {}'.format(key, val['message']))
    if toggle and warnings_to_print:
        print('Warnings: ')
        print('\n'.join(warnings_to_print), file=stream)


def log():
    """Log output."""
    print_warnings(output_stream=PRINT_WARNINGS['stream'],
                   toggle=PRINT_WARNINGS['value'])


def run():
    """Run module."""
    try:
        result = to_csv(cli())
        print(result)
    except VifferError as err:
        print('VifferError: ' + str(err))


if __name__ == '__main__':
    run()
    log()