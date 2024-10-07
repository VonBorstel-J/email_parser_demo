#src\parsers\parser_registry.py

import logging
from src.parsers.parser_options import ParserOption
from src.parsers.rule_based_parser import RuleBasedParser
from src.parsers.local_llm_parser import LocalLLMParser  

class ParserRegistry:
    """Registry for managing parsers."""

    _registry = {}
    logger = logging.getLogger("ParserRegistry")

    @classmethod
    def register_parser(cls, option, parser_cls):
        """
        Register a parser with the given option.

        Args:
            option (ParserOption): The option to register the parser with.
            parser_cls: The parser class to register.
        """
        if not isinstance(option, ParserOption):
            cls.logger.error("Attempted to register parser with invalid option type: %s", option)
            raise TypeError("Parser option must be an instance of ParserOption Enum.")
        
        cls._registry[option] = parser_cls
        cls.logger.info("Registered parser '%s' for option '%s'.", parser_cls.__name__, option.value)

    @classmethod
    def get_parser(cls, option):
        if not isinstance(option, ParserOption):
            cls.logger.error("Attempted to get parser with invalid option type: %s", option)
            raise TypeError("Parser option must be an instance of ParserOption Enum.")
        
        parser_cls = cls._registry.get(option)
        if not parser_cls:
            cls.logger.error("Parser not registered for option: %s", option)
            raise ValueError(f"Parser not registered for option: {option.value}")
        
        cls.logger.info("Retrieving parser '%s' for option '%s'.", parser_cls.__name__, option.value)
        return parser_cls()

# Configure logging for ParserRegistry
logging.basicConfig(level=logging.INFO)
ParserRegistry.logger.setLevel(logging.INFO)

# Register parsers after defining the ParserRegistry class
ParserRegistry.register_parser(ParserOption.RULE_BASED, RuleBasedParser)
ParserRegistry.register_parser(ParserOption.LOCAL_LLM, LocalLLMParser)
