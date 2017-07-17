#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A package for geographical analysis of ODK forms."""
import sys
import argparse
# from pmix.xlsform import Xlsform as Wb
from pmix.xlsform import Workbook as Wb
from pmix.geographical_analysis.gi_integrity import GiIntegrityReport
from pmix.geographical_analysis.definitions.error import GA_Exception


def cli():
    """Command line interface for package."""
    prog_desc = 'A program for geographical analysis of ODK forms.'
    parser = argparse.ArgumentParser(description=prog_desc)

    file_help = 'Path to source XLSForm.'
    parser.add_argument('file', help=file_help)

    args = parser.parse_args()

    try:
        xlsform = Wb(args.file)
        gi_data = xlsform['external_choices']
        report = GiIntegrityReport(gi_data)
        print(str(report))
    except GA_Exception as err:
        err = 'An error occurred while attempting to convert \'{}\':\n{}'\
            .format(args.file, err)
        print(err, file=sys.stderr)
        print(err)


if __name__ == '__main__':
    cli()
