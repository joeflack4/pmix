#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for Viffer (Variable diff(erentiator)) package."""
import unittest

import re
from os import path as os_path, listdir

# from pmix.workbook import Workbook
from pmix.viffer.__main__ import to_csv

TEST_FORMS_DIRECTORY = os_path.dirname(os_path.realpath(__file__))


# pylint: disable=too-few-public-methods
# PyLint check not apply? - http://pylint-messages.wikidot.com/messages:r0903
class VifferTest:
    """Base class for Viffer package tests."""
    REF_FILE_NAME_PATTERN = r'[A-Za-z]{2}-ref-v?[0-9]{0,3}'  # Ex: FQ-ref-v13

    def __init__(self):
        self.test_forms = self.get_test_forms()
        self.test_ref_forms = self.get_test_ref_forms(self.test_forms)

    @staticmethod
    def get_test_forms():
        """Gets a list of all teset forms in test directory.
        Returns:
            list: Test forms.
        """
        xls_form_present = False
        test_forms = []
        for form in listdir(TEST_FORMS_DIRECTORY):
            if form.endswith('.xls'):
                xls_form_present = True
            elif form.endswith('.xlsx'):
                test_forms.append(form)
        if xls_form_present:
            print('WARNING: File(s) with \'.xls\' extension found in test '
                  'directory \'{}\'. XlsForms of \'.xls\' extension have been '
                  'deprecated according to PMA2020 ODK standards. It is '
                  'recommended to use \'.xlsx\'.'.format(TEST_FORMS_DIRECTORY))
        return test_forms

    @staticmethod
    def get_test_ref_forms(test_forms):
        """Gets a list of all forms in test directory matching ref pattern.
        Args:
            test_forms (list): A list of test forms.
        Returns:
            list: Reference template test forms.
        """
        test_ref_forms = []
        for form in test_forms:
            if re.match(VifferTest.REF_FILE_NAME_PATTERN, form):
                test_ref_forms.append(form)
        return test_ref_forms


class VifferMainTest(unittest.TestCase, VifferTest):
    """Unit tests for the viffer.__main__."""
    def __init__(self, *args, **kwargs):
        super(VifferMainTest, self).__init__(*args, **kwargs)
        VifferTest.__init__(self)


    def test_csv_report_accuracy(self):
        """Test that output CSV file is reporting correctly."""
        from argparse import Namespace
        import pandas as pd
        from io import StringIO
        mock_cli = Namespace(files=['test/files/viffer/generic/001/1.xlsx',
                                    'test/files/viffer/generic/001/2.xlsx'],
                             format='csv')
        output = StringIO(to_csv(mock_cli))
        df = pd.read_csv(output)

        # TODO: (2017/11/14 jef) The 'ins' variable is only necessary right now
        #   because the order of test_df is changing every time. Not sure where
        #   I need to fix this in order to make sure consistent ordering.
        # test_df = pd.DataFrame([['noneed']], columns=['new'])
        ins = ('15001', '.', 'noneed', 'Not sick/did not need care')
        self.assertIn(df.iloc[0]['new'], ins)


if __name__ == '__main__':
    # unittest.main()
    import doctest
    # from pmix.viffer.__main__ import analyze
    doctest.testfile(TEST_FORMS_DIRECTORY + "/../" + "pmix/viffer/__main__.py")
