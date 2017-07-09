#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entry point for Viffer (Variable diff(erentiator)) package."""
import argparse

# from pmix.workbook import Workbook
# from pmix.xlsform import Xlsform
from pmix.viffer.definitions.errors import VifferError


def cli():
    """Command line interface for package.

    Returns:
        dict: Args parsed from the command line.
    """
    prog_desc = 'Get variable differences between two ODK XlsForms.'
    parser = argparse.ArgumentParser(description=prog_desc)

    file_help = 'One or more paths to files ODK XlsForms.'
    parser.add_argument('xlsxfiles', nargs='+', help=file_help)

    format_help = 'The format to generate. Default is \'text\'.'
    parser.add_argument('-f', '--format', choices=('html', 'text'), nargs='?',
                        const='text', default='text', help=format_help)

    out_help = ('Path to write output. If this argument is not supplied, then '
                'STDOUT is used.')
    parser.add_argument('-o', '--outpath', help=out_help)

    return vars(parser.parse_args())


def output(pending_output, output_format):
    """Generate output.

    Args:
        pending_output (dict): An analysis of variable differences.
        output_format (str): The format to output.

    Possible Side Effects:
        to_html(): Renders html output.
        to_text(): Renders text output.
    """
    def to_html(data):  # TODO
        """Generate output in html format.

        Args:
            data (dict): An analysis of variable differences.

        Side Effects:
            print(): Prints analysis.
        """
        print(data)

    def to_text(data):
        """Generate output in a text format.

        Args:
            data (dict): An analysis of variable differences.

        Side Effects:
            print(): Prints analysis.
        """
        print(data)

    if output_format is 'html':
        to_html(pending_output)
    elif output_format is 'text' or not output_format:
        to_text(pending_output)


def analyze(forms):
    """Run variable differ.

    Will analyze variable difference between two ODK XlsForms. Differences
    include (1) removed variables, (2) new variables, & (3) changed variables.
    The difference between 2 and 3 is more difficult than it might seem, as ODK
    variables do not otherwise have unique identifiers otherwise. So an
    a Levenshtein Distance analysis (https://en.wikibooks.org/wiki/
    Algorithm_Implementation/Strings/Levenshtein_distance#Python) is done to
    assess the similarities accross different dimensions.

    Args:
        forms (list): A list of form objects.

    Returns:
        dict: An analysis of variable differences.
    """
    analysis = {}

    return analysis


def render_form_objects(files):
    """Create ODK form objects based on ODK XlsForms.

    Args:
        files (list): A list of file paths.

    Returns:
        list: A list of form objects.

    Raises:
        VifferError: Must select two and only two files to diff.
    """
    if len(files) is not 2:
        msg = 'VifferError: Must select two and only two files to diff.'
        raise VifferError(msg)
    form_objects = []
    return form_objects


if __name__ == '__main__':
    try:
        USER_INPUT = cli()
        FORMS = render_form_objects(USER_INPUT['xlsxfiles'])
        ANALYSIS = analyze(FORMS)
        output(ANALYSIS, USER_INPUT['format'])
    except VifferError as err:
        print(err)
