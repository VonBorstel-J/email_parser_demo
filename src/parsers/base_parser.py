#src\parsers\base_parser.py

from abc import ABC, abstractmethod

class BaseParser(ABC):
    """Abstract base class for all parsers."""

    @abstractmethod
    def parse(self, email_content: str):
        """
        Parse the given email content.

        Args:
            email_content (str): The raw email content to parse.

        Returns:
            dict: Parsed data as a dictionary.
        """
        pass
