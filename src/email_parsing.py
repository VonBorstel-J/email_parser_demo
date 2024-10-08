# src/email_parsing.py

from src.parsers.parser_registry import ParserRegistry
from src.parsers.parser_options import ParserOption
from src.utils.validation import validate_json

class EmailParser:
    """
    EmailParser handles the selection and usage of different parsing strategies.
    """

    def __init__(self):
        pass  # Initialization logic if needed

    def parse_email(self, email_content: str, parser_option: str) -> dict:
        """
        Parse the email content using the specified parser option.

        Args:
            email_content (str): The raw email content to parse.
            parser_option (str): The parser option to use ('rule_based', 'local_llm', 'llm').

        Returns:
            dict: Parsed data as a dictionary.
        """
        parser_class = ParserRegistry.get_parser(parser_option)
        if not parser_class:
            raise ValueError(f"Invalid parser option selected: '{parser_option}'")
        
        parser_instance = parser_class()
        parsed_data = parser_instance.parse(email_content)

        # Optionally, you can add CSV conversion here if needed - This would be server side processing instead of client - probs not gonna be necessary.
        # For example:
        # csv_data, csv_filename = self.convert_to_csv(parsed_data)
        # parsed_data["csv_data"] = csv_data
        # parsed_data["csv_filename"] = csv_filename

        # Validate the parsed data against a JSON schema
        is_valid, error_message = validate_json(parsed_data)
        if not is_valid:
            raise ValueError(f"Parsed data validation failed: {error_message}")

        return parsed_data

    # Optional: Implement CSV conversion if required
    # def convert_to_csv(self, parsed_data: dict) -> Tuple[str, str]:
    #     # Conversion logic here
    #     pass
