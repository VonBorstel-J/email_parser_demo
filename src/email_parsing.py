# src/email_parsing.py

import logging
from src.parsers.parser_options import ParserOption
from src.parsers.parser_registry import ParserRegistry

class EmailParser:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

    def parse_email(self, email_content: str, parser_option: str):
        try:
            parser_option_enum = ParserOption(parser_option)
        except ValueError:
            self.logger.error(f"Unknown parser option: {parser_option}")
            raise ValueError(f"Unknown parser option: {parser_option}")

        self.logger.info(f"Parsing email using {parser_option_enum.value} parser.")
        try:
            parser = ParserRegistry.get_parser(parser_option_enum)
            parsed_data = parser.parse(email_content)
            self.logger.info(f"Successfully parsed email using {parser_option_enum.value} parser.")
            return parsed_data
        except Exception as e:
            self.logger.error(f"Error while parsing email: {e}")
            raise
