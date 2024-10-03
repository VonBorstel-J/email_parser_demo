# src/parsers/parser_factory.py

import logging
from src.parsers.rule_based_parser import RuleBasedParser
from src.parsers.llm_parser import LLMParser
from src.parsers.local_llm_parser import LocalLLMParser

class ParserFactory:
    """Factory class to instantiate the appropriate parser."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_parser(self, parser_option: str):
        """
        Returns the parser based on the user's selection.
        """
        self.logger.info("Selecting parser based on user option: %s", parser_option)
        if parser_option == 'rule_based':
            parser = RuleBasedParser()
        elif parser_option == 'llm':
            parser = LLMParser()
        elif parser_option == 'local_llm':
            parser = LocalLLMParser()
        else:
            self.logger.error("Invalid parser option selected: %s", parser_option)
            raise ValueError(f"Invalid parser option: {parser_option}")
        return parser
