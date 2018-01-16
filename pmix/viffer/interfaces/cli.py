"""Command line interface."""
from argparse import ArgumentParser

from pmix.viffer.definitions.errors import VifferError


def cli():
    """CLI."""
    prog_desc = 'Report on differences between XLSForms by ID comparison.'
    parser = ArgumentParser(description=prog_desc)

    format_help = 'The format to generate. Default is \'csv\'.'
    parser.add_argument('-f', '--format', choices=('csv', 'json'), nargs='?',
                        const='csv', default='csv', help=format_help)

    file_help = 'Paths to two XLSForms, in the order of older to newer.'
    parser.add_argument('files', nargs='+', help=file_help)

    args = parser.parse_args()
    if len(args.files) != 2:
        raise VifferError('Must supply 2 XLSForms.')
    else:
        return args
