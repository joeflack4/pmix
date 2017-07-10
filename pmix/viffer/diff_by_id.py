#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff by ID - Report on differences between XLSForms by ID comparison."""
from sys import stderr, stdout
from datetime import datetime
from json import dumps as json_dumps
from argparse import ArgumentParser
from pmix.viffer.config import differ_by_id_config as config
from pmix.viffer.definitions.constants import RELEVANT_WORKSHEETS, \
    MANDATORY_REPORT_FIELDS
from pmix.viffer.definitions.errors import VifferError
from pmix.viffer.definitions.abstractions import intersect, non_empties, union, \
    exclusive, pruned, prune_by_n_required_children
from pmix.viffer.state_mgmt import assign, the, print_state_history, \
    current_state
# from pmix.viffer.state_mgmt import assign, the, print_state_history, \
#     current_state, data, state
# from collections import OrderedDict
from pmix.xlsform import Xlsform

data_schema = {
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
common_xlsform_elements_schema = {'<id>': {'<field>': {'new': '', 'old': ''}}}
data = {}
p_sh = config['output']['state_history']
p_wrn = config['output']['warnings']
valid_id = config['validation']['id']
valid_id_msg = '  * Type: {}\n  * Length: {}\n  * Null character: {}'\
    .format(valid_id['type'], valid_id['length'], valid_id['null_character'])
warnings = {
    'invalid_id': {
        'value': False,
        'message': 'One or more IDs were malformed. Valid IDs are as follows.'
                   '\n' + valid_id_msg
    },
    'invalid_id_length_warning': {
        'value': False,
        'message': 'One or more ID with an invalid length was found. Valid IDs'
                   ' are as follows.\n' + valid_id_msg
    },
    'inconsistent_worksheet_headers': {
        'value': False,
        'message': 'Worksheet \'{}\' has inconsistent fields. The following '
                   'fields were only found in 1 out of 2 worksheets: {}.'
    }
}

def get_ws_ids(ws):
    """Get all component IDs in worksheet."""
    ids = []
    id_index = ws.header.index('id')
    for row in ws.data[1:]:
        val = row[id_index].value
        if not isinstance(val, valid_id['type']) \
                and val is not valid_id['null_character']:
            warnings['invalid_id']['value'] = True
        if isinstance(val, valid_id['type']):
            ids.append(val)
            if len(str(val)) is not valid_id['length']:
                warnings['invalid_id_length_warning']['value'] = True
    return sorted(ids)


def get_ws_data_by_id(ws, ids):
    """Get worksheet data, indexed by ID."""
    old_id_index = ws.header.index('id')
    # 1. Schema {'<id>': [cell1, cell2...]}
    ws_by_id = {str(row[old_id_index].value):
                               [cell.value for cell in row]
                           for row in ws.data if row[old_id_index].value in ids}
    # 2. Schema {'<id>': {field1: cell1, field2: cell2...}}
    for key, val in ws_by_id.items():
        hdr = ws.header
        ws_by_id[key] = {field: val[hdr.index(field)]
                             for field in hdr if val[hdr.index(field)]}
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
        id: {
            field: {
                'new': new[id][field] if field in new[id] else '',
                'old': old[id][field] if field in old[id] else ''
            } for field in headers
        } for id in sorted([str(i) for i in ids])
    }

    return common_xlsform_elements


def empty_mandatory_fields_removed(dictionary):
    """Return XlsForm elements dict with empty mandatories removed."""
    # TODO: This will cause an error if there is only 1 field to compare.
    return prune_by_n_required_children(dictionary, 2)


def get_xlsform_element_changes_by_id(elements):
    """Get common XlsForm elements, indexed by ID.

    Returns:
        dict: Of schema {'<id>': {'<field>': {'+': '', '-': ''}}}
    """
    # Create data structure.
    MRF = MANDATORY_REPORT_FIELDS
    xec = pruned({
        id: {
            field: {
                '+': field_data['new'],
                '-': field_data['old']
            } if field_data['new'] else {
                '-': field_data['old']
            } for field, field_data in row_data.items()
            if field_data['new'] != field_data['old']
               or field in MRF
        } for id, row_data in elements.items()
    })

    # Remove ID's were listed just because 'name' was forced.
    return empty_mandatory_fields_removed(xec)


def get_xlsform_element_changes_by_name(elements_by_id):
    """Get common XlsForm elements, incexed by name."""
    MRF = 'name'
    xec = pruned({
        row_data['name']['+']: {
            key: val for key, val in row_data.items()
            # if key != 'name' or key == 'name' and val['+'] != val['-']
            if key not in MRF or key in MRF and val['+'] != val['-']
        } for id, row_data in elements_by_id.items()
    })

    # TODO: Add ID field to all elements.

    # TODO: Add option of want to include old var name instead of new.

    # Remove ID's were listed just because 'list_name' was forced.
    return empty_mandatory_fields_removed(xec)


def compare_by_worksheet(old_ws, new_ws):
    """Compare changes by worksheet."""
    # common_ids = sorted([str(i) for i in intersect(old_ws_ids, new_ws_ids)]
    common_ids = intersect(get_ws_ids(old_ws), get_ws_ids(new_ws))

    common_xlsform_elements = get_common_xlsform_elements(
        ids=common_ids, old_ws=old_ws, new_ws=new_ws)

    xec = get_xlsform_element_changes_by_id(
        common_xlsform_elements)

    xlsform_element_changes = \
        get_xlsform_element_changes_by_name(elements_by_id=xec)

    return xlsform_element_changes


def get_worksheets_by_name(ws_name, original_form, new_form):
    """Get worksheets."""
    original_form_ws = original_form[ws_name]
    new_form_ws = new_form[ws_name]
    return original_form_ws, new_form_ws


def get_worksheet_lists_with_ids(original_form, new_form):
    """Get worksheet lists."""
    original_form_list = [ws.name for ws in original_form.data
                          if 'id' in ws.header]
    new_form_list = [ws.name for ws in new_form.data if 'id' in ws.header]
    return list(set(original_form_list) & set(new_form_list))


def compare_worksheets():
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
        ws_report[ws] = data_schema['worksheets']['<worksheet>'].copy() \
            if ws not in ws_report else ws_report[ws]
        old_ws, new_ws = \
            get_worksheets_by_name(ws_name=ws,
                                   original_form=the('original_form'),
                                   new_form=the('new_form'))
        ws_report[ws] = compare_by_worksheet(old_ws=old_ws, new_ws=new_ws)
    assign('data', data)

    report = {
        'changes': {
            'metadata': {
                'source_files': {
                    'new': the('new_form').settings['form_title'],
                    'old': the('original_form').settings['form_title']
                },
                'date': str(datetime.now())[:-7] # Remove milliseconds.
            },
            'data': the('data')
        }
    }

    assign('report', report)

    # print(current_state())  # DEBUG
    return the('report')



def diff_by_id(files):
    """Summarize differences of two forms by comparing IDs of components."""
    if 'data' not in current_state():
        assign('data', {})
    assign('xlsforms', [Xlsform(file) for file in files])
    assign('original_form', the('xlsforms')[0])
    assign('new_form', the('xlsforms')[1])
    out = compare_worksheets()
    return out


def print_warnings(toggle=True, output_stream='stdout'):
    """Print warnings."""
    stream = stdout if output_stream is 'stdout' \
        else stderr if output_stream is 'stderr' else stdout
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
        result = diff_by_id(files=the('args').files)
        result = json_dumps(result, indent=4)
        print(result)
    except VifferError as err:
        print('VifferError: ' + str(err))


def log():
    """Log output."""
    print_state_history(output_stream=p_sh['stream'], toggle=p_sh['value'])
    print_warnings(output_stream=p_wrn['stream'], toggle=p_wrn['value'])

if __name__ == '__main__':
    run()
    log()
