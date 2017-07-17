#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests geographical analysis sub-package."""
import unittest
import doctest
import os
from argparse import ArgumentParser

TEST_PACKAGES = ['pmix.geographical_analysis', 'test']
TEST_DIR = os.path.dirname(os.path.realpath(__file__)) + '/'
TEST_FILES_DIR = TEST_DIR + 'files/'


# # Unit Tests
class GeographicalAnalysis(unittest.TestCase):  # TODO: Add real tests.
    """Unit tests geographical analysis sub-package."""

    def test_1(self):
        self.assertTrue(1 == 1)  # Placeholder.


# # Helper Functions
def get_args():
    """CLI for test runner."""
    desc = 'Run tests.'
    parser = ArgumentParser(description=desc)
    doctests_only_help = 'Specifies whether to run doctests only, as ' \
                         'opposed to doctests with unittests. Default is' \
                         ' False.'
    parser.add_argument('-d', '--doctests-only', action='store_true',
                        help=doctests_only_help)
    args = parser.parse_args()
    return args


def get_test_modules(test_package):
    """Get files to test.

    Args:
        test_package (str): The package containing modules to test.

    Returns:
        list: List of all python modules in package.

    """
    if test_package == 'pmix.geographical_analysis':  # TODO: Make dynamic.
        root_dir = TEST_DIR + "../" + "pmix/geographical_analysis"
    elif test_package == 'test':
        root_dir = TEST_DIR
    else:
        raise Exception('Test package not found.')

    test_modules = []
    for dummy, dummy, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith('.py'):
                file = file[:-3]
                test_module = test_package + '.' + file
                test_modules.append(test_module)
    return test_modules


def get_test_suite(test_packages):
    """Get suite to test.

    Returns:
        TestSuite: Suite to test.

    """
    suite = unittest.TestSuite()
    for package in test_packages:
        pkg_modules = get_test_modules(test_package=package)
        for pkg_module in pkg_modules:
            suite.addTest(doctest.DocTestSuite(pkg_module))
    return suite


if __name__ == '__main__':
    PARAMS = get_args()
    TEST_SUITE = get_test_suite(TEST_PACKAGES)
    unittest.TextTestRunner(verbosity=1).run(TEST_SUITE)

    if not PARAMS.doctests_only:
        unittest.main()
