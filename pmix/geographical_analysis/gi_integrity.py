"""Analaysis of the integrity of relationship of geographical identifiers."""
# from pmix.xlstab import Xlstab as Ws
from pmix.xlstab import Worksheet as Ws


class GiIntegrityReport:
    """Class for report of integrity of geographical identifiers."""

    def __init__(self, source_data):
        """Init."""
        self.source = self.load_data(source_data)
        self.source_body = self.source[1:]
        self.source_header = self.source[0]
        self.data = self.source

    @staticmethod
    def load_data(source_data):
        """Load data."""
        data = source_data.data.copy() if isinstance(source_data, Ws) \
            else source_data.copy()
        return [[cell.value for cell in row] for row in data]

    def to_text(self):
        """Return text."""
        return str(self.data)

    def __str__(self):
        return self.to_text()
