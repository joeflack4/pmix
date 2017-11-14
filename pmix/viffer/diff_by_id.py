#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff by ID - Report on differences between XLSForms by ID comparison."""
import pandas as pd
from io import StringIO
from sys import stderr, stdout
from copy import copy
from datetime import datetime
from json import dumps as json_dumps
from argparse import ArgumentParser
from pmix.viffer.config import DIFFER_BY_ID_CONFIG as CONFIG, \
    MISSING_COL_TOKEN, MISSING_VAL_TOKEN, EMPTY_TOKENS
from pmix.viffer.definitions.constants import RELEVANT_WORKSHEETS, \
    MANDATORY_REPORT_FIELDS
from pmix.viffer.definitions.errors import VifferError
from pmix.viffer.definitions.abstractions import intersect, non_empties, \
    union, exclusive, pruned, prune_by_n_required_children
from pmix.viffer.utils.state_mgmt import assign, the, print_state_history, \
    current_state
# from pmix.viffer.state_mgmt import assign, the, print_state_history, \
#     current_state, DATA, state
# from collections import OrderedDict
from pmix.xlsform import Xlsform


# To JSON
DATA_SCHEMA = {  # TODO: Account for choices being sortable by list_name.
    'worksheets': {
        '<worksheet>': {
            # 'additions': '',
            # 'deletions': '',
            'changes': {
                '<id>': {
                    '<field>': {
                        '+': '',
                        '-': ''
                    }
                }
            }
        }
    }
}
data = {}  # pylint: disable=invalid-name


def validate(validation_type=None, _data=None):
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


def get_ws_ids(ws):
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

    return sorted(ids)


def get_ws_data_by_id(ws, ids):
    """Get worksheet data, indexed by ID."""
    old_id_index = ws.header.index('id')
    # 1. Schema {'<id>': [cell1, cell2...]}
    ws_by_id = {
        str(row[old_id_index].value):
            [cell.value for cell in row]
        for row in ws.data if row[old_id_index].value in ids
    }
    # 2. Schema {'<id>': {field1: cell1, field2: cell2...}}
    for key, val in ws_by_id.items():
        hdr = ws.header
        ws_by_id[key] = {
            field:
                val[hdr.index(field)]
            for field in hdr if val[hdr.index(field)]
        }
    return ws_by_id


def get_common_ws_headers(worksheets):
    """Get common worksheet headers."""
    headers = [ws.header for ws in worksheets]
    header_intersect = intersect(non_empties(headers))
    header_union = union(non_empties(headers))
    missing = exclusive(header_union, header_intersect)
    if missing:
        warn = warnings['inconsistent_worksheet_headers']
        warn['value'] = True
        warn['message'] = warn['message'].format(worksheets[0].name, missing)
    return header_intersect


def get_common_xlsform_elements(ids, old_ws, new_ws):
    """Get common XlsForm elements.

    Returns:
        dict: Of schema {'<id>': {'<field>': {'new': '', 'old': ''}}}
    """
    headers = get_common_ws_headers([old_ws, new_ws])
    old = get_ws_data_by_id(ws=old_ws, ids=ids)
    new = get_ws_data_by_id(ws=new_ws, ids=ids)
    common_xlsform_elements = {
        ID: {
            field: {
                'new': new[ID][field] if field in new[ID] else '',
                'old': old[ID][field] if field in old[ID] else ''
            } for field in headers
        } for ID in sorted([str(i) for i in ids])
    }

    return common_xlsform_elements


def empty_mandatory_fields_removed(dictionary):
    """Return XlsForm elements dict with empty mandatories removed."""
    # TODO: This will cause an error if there is only 1 field to compare.
    return prune_by_n_required_children(dictionary, 2)


def xlsform_element_changes_by_id(elements):
    """Get common XlsForm elements, indexed by ID.

    Returns:
        dict: Of schema {'<id>': {'<field>': {'+': '', '-': ''}}}
    """
    # Create data structure.
    mrf = MANDATORY_REPORT_FIELDS
    xec = pruned({
        ID: {
            field: {
                '+': field_data['new'],
                '-': field_data['old']
            } if field_data['new'] else {
                '-': field_data['old']
            } for field, field_data in row_data.items()
            if field_data['new'] != field_data['old'] or field in mrf
        } for ID, row_data in elements.items()
    })

    # Remove ID's were listed just because 'name' was forced.
    return empty_mandatory_fields_removed(xec)


def xlsform_element_changes_by_name(elements_by_id):
    """Get common XlsForm elements, incexed by name."""
    mrf = 'name'
    xec = pruned({
        row_data['name']['+']: {
            key: val for key, val in row_data.items()
            # if key != 'name' or key == 'name' and val['+'] != val['-']
            if key not in mrf or key in mrf and val['+'] != val['-']
        } for dummy, row_data in elements_by_id.items()
    })

    # TODO: Add ID field to all elements.

    # TODO: Add option of want to include old var name instead of new.

    # Remove ID's were listed just because 'list_name' was forced.
    return empty_mandatory_fields_removed(xec)


def _json_compare_by_worksheet(old_ws, new_ws):
    """Compare changes by worksheet."""
    # common_ids = sorted([str(i) for i in intersect(old_ws_ids, new_ws_ids)]
    common_ids = intersect(get_ws_ids(old_ws), get_ws_ids(new_ws))
    common_xlsform_elements = get_common_xlsform_elements(
        ids=common_ids, old_ws=old_ws, new_ws=new_ws)

    xec_by_id = xlsform_element_changes_by_id(common_xlsform_elements)
    xec_by_name = xlsform_element_changes_by_name(elements_by_id=xec_by_id)

    return xec_by_name


def get_worksheets_by_name(ws_name, original_form, new_form):
    """Get worksheets."""
    original_form_ws = original_form[ws_name]
    new_form_ws = new_form[ws_name]
    return original_form_ws, new_form_ws


def get_worksheet_lists_with_ids(original_form, new_form):
    """Get worksheet lists.

    Side effects:
        validate()
    """
    original_form_list = [ws.name for ws in original_form.data
                          if 'id' in ws.header]
    new_form_list = [ws.name for ws in new_form.data if 'id' in ws.header]

    ws_lists_with_ids = list(set(original_form_list) & set(new_form_list))

    validate(validation_type='id', _data=ws_lists_with_ids)

    return ws_lists_with_ids


def _json_compare_worksheets():
    """Compare worksheets."""
    # TODO: Carry on with experiment of exclusive state usage pattern.
    # if 'worksheets' not in data:
    #     # assign(data['worksheets'], {})
    #     print(current_state())
    #     assign(current_state(), 'worksheets')
    # for ws in RELEVANT_WORKSHEETS:
    #     # assign(data['worksheets'], ws)
    #     assign(data['worksheets'][ws],
    #            data_schema['worksheets']['<worksheet>'].copy())
    #     assign(data['worksheets'][ws],
    #           compare_by_worksheet(ws=ws, original_form=the('original_form'),
    #                                 new_form=the('new_form')))
    data['worksheets'] = {} if 'worksheets' not in data else data['worksheets']
    ws_report = data['worksheets']
    ws_lists = get_worksheet_lists_with_ids(original_form=the('original_form'),
                                            new_form=the('new_form'))
    common_relevant_ws_list = intersect(ws_lists, RELEVANT_WORKSHEETS)
    for ws in common_relevant_ws_list:
        ws_report[ws] = DATA_SCHEMA['worksheets']['<worksheet>'].copy() \
            if ws not in ws_report else ws_report[ws]
        old_ws, new_ws = \
            get_worksheets_by_name(ws_name=ws,
                                   original_form=the('original_form'),
                                   new_form=the('new_form'))
        ws_report[ws] = _json_compare_by_worksheet(old_ws=old_ws,
                                                   new_ws=new_ws)
    assign('data', data)

    report = {
        'changes': {
            'metadata': {
                'source_files': {
                    'new': the('new_form').settings['form_title'],
                    'old': the('original_form').settings['form_title']
                },
                'date': str(datetime.now())[:-7]  # Remove milliseconds.
            },
            'data': the('data')
        }
    }

    assign('report', report)

    return the('report')  # print(current_state())  # DEBUG


def to_json(args):
    """To JSON.

    Summarize differences of two forms by comparing IDs of components.
    """
    if 'data' not in current_state():
        assign('data', {})
    assign('xlsforms', [Xlsform(file) for file in args.files])
    assign('original_form', the('xlsforms')[0])
    assign('new_form', the('xlsforms')[1])

    result = _json_compare_worksheets()
    result = json_dumps(result, indent=4)

    return result


# To CSV
HEADER = ['worksheet', 'id', 'current_name', 'current_lab', 'field', 'old',
          'new', 'different?']


def _csv_compare_by_worksheet(report_schema, ws_name, old_fields, new_fields, 
                              all_fields, common_ids, old_ws, new_ws):
    """Compare changes by worksheet."""
    ws_data = []
    report_indexes = \
        {col_name: report_schema.index(col_name) for col_name in report_schema}
    old_field_indexes = \
        {col_name: old_fields.index(col_name) for col_name in old_fields}
    new_field_indexes = \
        {col_name: new_fields.index(col_name) for col_name in new_fields}

    old_ws_array, new_ws_array = pd.DataFrame(old_ws), pd.DataFrame(new_ws)

    for _id in common_ids:

        for field in all_fields:

            row = [col_name for col_name in report_schema]

            # TODO: Make a config, and set it to ignore by default rows that
            # have not changed.
            # TODO: Intersect instead of set() in all_fields arround line ~400
            # TODO: On top of returning "N/A", also print out a report/warning
            #  for fields that are in one file but not in the other.
            old_record = old_ws_array.loc[
                old_ws_array[old_field_indexes['id']] == str(_id)]
            old_row_num = old_record.index[0]
            if field in old_field_indexes:
                old_field_val = \
                    old_record[old_field_indexes[field]].get(old_row_num)
                old_field_val = \
                    old_field_val.replace('None', MISSING_VAL_TOKEN)
            else:
                old_field_val = MISSING_COL_TOKEN

            new_record = new_ws_array.loc[
                new_ws_array[new_field_indexes['id']] == str(_id)]
            new_row_num = new_record.index[0]
            if field in new_field_indexes:
                new_field_val = \
                    new_record[new_field_indexes[field]].get(new_row_num)
                new_field_val = \
                    new_field_val.replace('None', MISSING_VAL_TOKEN)
            else:
                new_field_val = MISSING_COL_TOKEN

            # TODO: Change "label::English" to default language.
            row[report_indexes['worksheet']] = ws_name
            row[report_indexes['id']] = str(_id)
            row[report_indexes['current_name']] = \
                new_record[new_field_indexes['name']].get(new_row_num)
            row[report_indexes['current_lab']] = \
                new_record[new_field_indexes['label::English']]\
                .get(new_row_num)
            row[report_indexes['field']] = field
            row[report_indexes['old']] = \
                old = old_field_val if old_field_val else MISSING_VAL_TOKEN
            row[report_indexes['new']] = \
                new = new_field_val if new_field_val else MISSING_VAL_TOKEN
            row[report_indexes['different?']] = \
                str(False) if old in EMPTY_TOKENS and new in EMPTY_TOKENS \
                else str(old != new)

            ws_data.append(row)

    return ws_data


def _2d_arr_to_csv(_2d_array):
    """2d array to csv."""
    df = pd.DataFrame(_2d_array[1:], columns=_2d_array[0])
    csv_str_io = StringIO()
    df.to_csv(csv_str_io)
    csv_str = csv_str_io.getvalue()
    return csv_str


def prune_rows_by_missing_field_value(ws, index):
    """Remove rows without any id."""
    # return [row for row in ws if row[index] is not None]
    # from sys import stderr
    # rowz = [row for row in ws if row[index] is not None]
    # idz = [row[index] for row in rowz]
    # print(idz, file=stderr)
    return [row for row in ws if row[index] is not None]


def formatted_ws_data(ws):
    """Format worksheet."""
    formatted_ws = [[str(cell.value) for cell in row] for row in ws]
    id_col_index = formatted_ws.pop(0).index('id')
    # id_col_index = formatted_ws[0].index('id')
    filtered_ws = prune_rows_by_missing_field_value(formatted_ws, id_col_index)
    return sorted(filtered_ws, key=lambda x: x[id_col_index])


def to_csv(args):
    """To CSV."""
    xlsforms = [Xlsform(file) for file in args.files]
    new_form, original_form = xlsforms[1], xlsforms[0]
    report = [copy(HEADER)]

    ws_lists = get_worksheet_lists_with_ids(original_form=original_form,
                                            new_form=new_form)
    common_relevant_ws_list = intersect(ws_lists, RELEVANT_WORKSHEETS)

    for ws in common_relevant_ws_list:
        old_ws, new_ws = get_worksheets_by_name(ws_name=ws,
                                                original_form=original_form,
                                                new_form=new_form)

        common_ids = intersect(get_ws_ids(old_ws), get_ws_ids(new_ws))
        old_fields = [cell.value or None for cell in old_ws[0]]
        new_fields = [cell.value or None for cell in new_ws[0]]
        all_fields = [field for field in set(old_fields + new_fields) if field
                      is not None]
        old_ws, new_ws = formatted_ws_data(old_ws), formatted_ws_data(new_ws)

        report += _csv_compare_by_worksheet(report_schema=HEADER,
                                            ws_name=ws,
                                            old_fields=old_fields,
                                            new_fields=new_fields,
                                            all_fields=all_fields,
                                            common_ids=common_ids,
                                            old_ws=old_ws,
                                            new_ws=new_ws)

    result = _2d_arr_to_csv(report)

    return result


# General
P_SH = CONFIG['output']['state_history']
P_WRN = CONFIG['output']['warnings']
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


def cli():
    """CLI."""
    prog_desc = 'Report on differences between XLSForms by ID comparison.'
    parser = ArgumentParser(description=prog_desc)

    format_help = 'The format to generate. Default is \'csv\'.'
    parser.add_argument('-f', '--format', choices=('csv', 'json'), nargs='?',
                        const='csv', default='csv', help=format_help)

    file_help = 'Paths to two XLSForms in the order of older to newer.'
    parser.add_argument('files', nargs='+', help=file_help)

    args = parser.parse_args()
    if len(args.files) != 2:
        raise VifferError('Must supply 2 XLSForms.')
    else:
        return args


def run():
    """Run module."""
    try:
        assign('args', cli())
        func = to_json if the('args').format == 'json' else to_csv
        result = func(the('args'))
        print(result)
    except VifferError as err:
        print('VifferError: ' + str(err))


def log():
    """Log output."""
    print_state_history(output_stream=P_SH['stream'], toggle=P_SH['value'])
    print_warnings(output_stream=P_WRN['stream'], toggle=P_WRN['value'])


if __name__ == '__main__':
    # try:
    run()
    log()
    # except:
    #     from pdb import set_trace; set_trace()
