# src/parsers/parser_options.py

from enum import Enum

class ParserOption(Enum):
    """
    Enumeration of available parser options.

    Attributes:
        RULE_BASED (str): Identifier for the rule-based parser.
        LOCAL_LLM (str): Identifier for the local LLM parser.
    """
    RULE_BASED = 'rule_based'
    LOCAL_LLM = 'local_llm'
