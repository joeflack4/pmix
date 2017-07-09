#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff by ID - Report on differences between XLSForms by ID comparison."""
from argparse import ArgumentParser
from sys import stderr, stdout

from pmix.viffer.config import differ_by_id_config as config
from pmix.viffer.definitions.constants import RELEVANT_WORKSHEETS
from pmix.viffer.definitions.errors import VifferError
from pmix.viffer.definitions.functions import in_common
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
        'value': True,
        'message': 'One or more ID with an invalid length was found. Valid IDs'
                   ' are as follows.\n' + valid_id_msg
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
    # TODO: Get IDs in common.
    # print(ws.name)  # DEBUG
    # print(ids)  # DEBUG
    return ids


def compare_by_worksheet(schema, ws_name, old_ws, new_ws):
    """Compare changes by worksheet."""
    old_header = old_ws.header
    new_header = new_ws.header
    old_ws_ids = get_ws_ids(old_ws)
    new_ws_ids =get_ws_ids(new_ws)
    common_ids = in_common(old_ws_ids, new_ws_ids)
    print(ws_name)
    print(common_ids)
    # print(ws_name)
    # print(old_ws_ids)
    # print(new_ws_ids)
    # print(schema)
    return schema


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
    schema = data_schema['worksheets']['<worksheet>'].copy()
    data['worksheets'] = {} if 'worksheets' not in data else data['worksheets']
    ws_report = data['worksheets']
    ws_lists = get_worksheet_lists_with_ids(original_form=the('original_form'),
                                            new_form=the('new_form'))
    common_relevant_ws_list = in_common(ws_lists, RELEVANT_WORKSHEETS)
    for ws in common_relevant_ws_list:
        ws_report[ws] = data_schema['worksheets']['<worksheet>'].copy() \
            if ws not in ws_report else ws_report[ws]
        old_ws, new_ws = \
            get_worksheets_by_name(ws_name=ws,
                                   original_form=the('original_form'),
                                   new_form=the('new_form'))
        ws_report[ws] = compare_by_worksheet(schema=schema, ws_name=ws,
                                       old_ws=old_ws, new_ws=new_ws)
    assign('data', data)

    return '' # TODO


def diff_by_id(files):
    """Summarize differences of two forms by comparing IDs of components."""
    if 'data' not in current_state():
        assign('data', {})
    assign('xlsforms', [Xlsform(file) for file in files])
    assign('original_form', the('xlsforms')[0])
    assign('new_form', the('xlsforms')[1])
    out = compare_worksheets()

    # out = ''
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
        # files = ['test/files/viffer/1.xlsx', 'test/files/viffer/2.xlsx']
        # result = diff_by_id(files=files)  # Temporarily for development.
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
