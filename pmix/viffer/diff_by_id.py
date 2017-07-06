#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diff by ID - Report on differences between XLSForms by ID comparison."""
from argparse import ArgumentParser
from pmix.viffer.error import VifferError
from pmix.viffer.constants import RELEVANT_WORKSHEETS
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


def compare_by_worksheet(ws_name, old_ws, new_ws):
    """Compare changes by worksheet."""
    old_header = old_ws.header
    new_header = new_ws.header
    return ''


def get_worksheets_by_name(ws_name, original_form, new_form):
    """Get worksheets."""
    original_form_ws = original_form[ws_name]
    new_form_ws = new_form[ws_name]
    return original_form_ws, new_form_ws


def get_worksheet_lists(original_form, new_form):
    """Get worksheet lists."""
    original_form_list = [ws.name for ws in original_form.data]
    new_form_list = [ws.name for ws in new_form.data]
    return list(set(original_form_list) & set(new_form_list))


def get_common_relevant_ws_list(actual_set, total_possible_set):
    """Get common relevant worksheet list."""
    return list(set(actual_set) & set(total_possible_set))


def compare_worksheets():
    """Compare worksheets."""
    # TODO Carry on with state experiment when ready.
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
    wss = data['worksheets']
    ws_lists = get_worksheet_lists(original_form=the('original_form'),
                                   new_form=the('new_form'))
    common_relevant_ws_list = \
        get_common_relevant_ws_list(actual_set=ws_lists,
                                    total_possible_set=RELEVANT_WORKSHEETS)
    for ws in common_relevant_ws_list:
        wss[ws] = data_schema['worksheets']['<worksheet>'].copy() \
            if ws not in wss else wss[ws]
        old_ws, new_ws = \
            get_worksheets_by_name(ws_name=ws,
                                   original_form=the('original_form'),
                                   new_form=the('new_form'))
        new_data = compare_by_worksheet(ws_name=ws, old_ws=old_ws,
                                        new_ws=new_ws)

    return ''


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


if __name__ == '__main__':
    run()
    print_state_history(output_stream='stdout', toggle=False)
