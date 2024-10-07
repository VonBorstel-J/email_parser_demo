import logging
import re
import spacy
from src.parsers.base_parser import BaseParser
import yaml
import os
from datetime import datetime


class RuleBasedParser(BaseParser):
    """rule-based parser for comprehensive email parsing."""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.logger.info("spaCy model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load spaCy model: {e}")
            raise

        # Load configuration for patterns if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, "r") as file:
                config = yaml.safe_load(file)
            self.logger.info(f"Loaded parser configuration from {config_path}.")
        else:
            # Default configuration
            config = self.default_config()
            self.logger.info("Loaded default parser configuration.")

        # Precompile regular expressions for performance
        self.section_headers = config["section_headers"]
        self.section_pattern = re.compile(
            rf'^({"|".join(map(re.escape, self.section_headers))}):?\s*$', re.IGNORECASE
        )

        # Define patterns for each section
        self.patterns = {}
        for section, fields in config["patterns"].items():
            self.patterns[section] = {}
            for field, pattern in fields.items():
                self.patterns[section][field] = re.compile(
                    pattern, re.IGNORECASE | re.DOTALL
                )

        # Additional patterns for common edge cases
        self.additional_patterns = {}
        for section, fields in config.get("additional_patterns", {}).items():
            self.additional_patterns[section] = {}
            for field, pattern in fields.items():
                self.additional_patterns[section][field] = re.compile(
                    pattern, re.IGNORECASE | re.DOTALL
                )

        # Load date formats and boolean values from config if available
        self.date_formats = config.get(
            "date_formats",
            [
                "%m/%d/%Y",
                "%m-%d-%Y",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y-%m-%d",
                "%Y/%m/%d",
            ],
        )
        self.boolean_values = config.get(
            "boolean_values",
            {
                "positive": [
                    "yes",
                    "y",
                    "true",
                    "t",
                    "1",
                    "x",
                    "[x]",
                    "[X]",
                    "(x)",
                    "(X)",
                ],
                "negative": [
                    "no",
                    "n",
                    "false",
                    "f",
                    "0",
                    "[ ]",
                    "()",
                    "[N/A]",
                    "(N/A)",
                ],
            },
        )

    def default_config(self):
        """Provides the default configuration for the parser."""
        return {
            "section_headers": [
                "Requesting Party",
                "Insured Information",
                "Adjuster Information",
                "Assignment Information",
                "Assignment Type",
                "Additional details/Special Instructions",
                "Attachment(s)",
            ],
            "patterns": {
                "Requesting Party": {
                    "Insurance Company": r"Insurance Company\s*:\s*(.*)",
                    "Handler": r"Handler\s*:\s*(.*)",
                    "Carrier Claim Number": r"Carrier Claim Number\s*:\s*(.*)",
                },
                "Insured Information": {
                    "Name": r"Name\s*:\s*(.*)",
                    "Contact #": r"Contact #\s*:\s*(.*)",
                    "Loss Address": r"Loss Address\s*:\s*(.*)",
                    "Public Adjuster": r"Public Adjuster\s*:\s*(.*)",
                    "Owner or Tenant": r"Is the insured an Owner or a Tenant of the loss location\?\s*(.*)",
                },
                "Adjuster Information": {
                    "Adjuster Name": r"Adjuster Name\s*:\s*(.*)",
                    "Adjuster Phone Number": r"Adjuster Phone Number\s*:\s*(\+?\d[\d\s\-().]{7,}\d)",
                    "Adjuster Email": r"Adjuster Email\s*:\s*([\w\.-]+@[\w\.-]+\.\w+)",
                    "Job Title": r"Job Title\s*:\s*(.*)",
                    "Address": r"Address\s*:\s*(.*)",
                    "Policy #": r"Policy #\s*:\s*(\w+)",
                },
                "Assignment Information": {
                    "Date of Loss/Occurrence": r"Date of Loss/Occurrence\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    "Cause of loss": r"Cause of loss\s*:\s*(.*)",
                    "Facts of Loss": r"Facts of Loss\s*:\s*(.*)",
                    "Loss Description": r"Loss Description\s*:\s*(.*)",
                    "Residence Occupied During Loss": r"Residence Occupied During Loss\s*:\s*(.*)",
                    "Was Someone home at time of damage": r"Was Someone home at time of damage\s*:\s*(.*)",
                    "Repair or Mitigation Progress": r"Repair or Mitigation Progress\s*:\s*(.*)",
                    "Type": r"Type\s*:\s*(.*)",
                    "Inspection type": r"Inspection type\s*:\s*(.*)",
                },
                "Assignment Type": {
                    "Wind": r"Wind\s*\[\s*([xX])\s*\]",
                    "Structural": r"Structural\s*\[\s*([xX])\s*\]",
                    "Hail": r"Hail\s*\[\s*([xX])\s*\]",
                    "Foundation": r"Foundation\s*\[\s*([xX])\s*\]",
                    "Other": r"Other\s*\[\s*([xX])\s*\]\s*-\s*provide details\s*:\s*(.*)",
                },
                "Additional details/Special Instructions": {
                    "Additional details/Special Instructions": r"Additional details/Special Instructions\s*:\s*(.*)"
                },
                "Attachment(s)": {"Attachment(s)": r"Attachment\(s\)\s*:\s*(.*)"},
            },
            "additional_patterns": {
                "Requesting Party": {
                    "Policy #": r"Policy\s*Number\s*:\s*(\w+)",
                    "Carrier Claim Number": r"Claim\s*Number\s*:\s*(.*)",
                },
                "Assignment Information": {
                    "Date of Loss/Occurrence": r"Date of Loss(?:/Occurrence)?\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
                },
            },
            "date_formats": [
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%B %d, %Y",
                "%b %d, %Y",
                "%d %B %Y",
                "%d %b %Y",
                "%Y/%m/%d",
                "%d-%m-%Y",
                "%Y.%m.%d",
                "%d.%m.%Y",
                "%m-%d-%Y",
                "%Y%m%d",
                "%B %-d, %Y",  # For systems supporting '-' flag
                "%b %-d, %Y",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ],
            "boolean_values": {
                "positive": [
                    "yes",
                    "y",
                    "true",
                    "t",
                    "1",
                    "x",
                    "[x]",
                    "[X]",
                    "(x)",
                    "(X)",
                ],
                "negative": [
                    "no",
                    "n",
                    "false",
                    "f",
                    "0",
                    "[ ]",
                    "()",
                    "[N/A]",
                    "(N/A)",
                ],
            },
        }

    def parse(self, email_content: str):
        """
        Parses the email content using regular expressions and NLP techniques to extract key information.

        Args:
            email_content (str): The raw email content to parse.

        Returns:
            dict: Parsed data as a dictionary.
        """
        self.logger.info("Parsing email content with RuleBasedParser.")
        extracted_data = self.initialize_default_structure()

        # Extract sections based on the assignment schema
        sections = self.split_into_sections(email_content)

        # Extract data from each section
        for section, content in sections.items():
            extract_method = getattr(self, f"extract_{self.snake_case(section)}", None)
            if extract_method:
                try:
                    data = extract_method(content)
                    self.update_extracted_data(extracted_data, data)
                except Exception as e:
                    self.logger.warning(f"Error extracting section '{section}': {e}")
            else:
                self.logger.warning(
                    f"No extraction method found for section: {section}"
                )

        # Extract entities using NLP
        try:
            entities = self.extract_entities(email_content)
            extracted_data["Entities"] = entities
        except Exception as e:
            self.logger.warning(f"Error extracting entities: {e}")
            extracted_data["Entities"] = {}

        self.logger.debug(f"Extracted Data: {extracted_data}")
        self.logger.info("Completed parsing email with RuleBasedParser.")
        return extracted_data

    def initialize_default_structure(self):
        return {
            "Requesting Party": {
                "Insurance Company": "N/A",
                "Handler": "N/A",
                "Carrier Claim Number": "N/A",
            },
            "Insured Information": {
                "Name": "N/A",
                "Contact #": "N/A",
                "Loss Address": "N/A",
                "Public Adjuster": "N/A",
                "Owner or Tenant": "N/A",
            },
            "Adjuster Information": {
                "Adjuster Name": "N/A",
                "Adjuster Phone Number": "N/A",
                "Adjuster Email": "N/A",
                "Job Title": "N/A",
                "Address": "N/A",
                "Policy #": "N/A",
            },
            "Assignment Information": {
                "Date of Loss/Occurrence": "N/A",
                "Cause of loss": "N/A",
                "Facts of Loss": "N/A",
                "Loss Description": "N/A",
                "Residence Occupied During Loss": "N/A",
                "Was Someone home at time of damage": "N/A",
                "Repair or Mitigation Progress": "N/A",
                "Type": "N/A",
                "Inspection type": "N/A",
            },
            "Assignment Type": {
                "Wind": False,
                "Structural": False,
                "Hail": False,
                "Foundation": False,
                "Other": {"Checked": False, "Details": "N/A"},
            },
            "Additional details/Special Instructions": "N/A",
            "Attachment(s)": ["N/A"],
            "Entities": {},
        }

    def update_extracted_data(self, extracted_data, new_data):
        for key, value in new_data.items():
            if isinstance(value, dict):
                extracted_data[key].update(value)
            else:
                extracted_data[key] = value

    def snake_case(self, text: str) -> str:
        """Converts text to snake_case by removing non-word characters and replacing spaces with underscores."""
        # Remove non-word characters except spaces
        text = re.sub(r"[^\w\s]", "", text)
        # Replace one or more whitespace with single underscore
        return re.sub(r"\s+", "_", text.strip().lower())

    def split_into_sections(self, email_content: str):
        """
        Splits the email content into sections based on the assignment schema headers.

        Args:
            email_content (str): The raw email content.

        Returns:
            dict: Sections of the email mapped to their content.
        """
        self.logger.debug("Splitting email content into sections.")
        sections = {header: "" for header in self.section_headers}
        current_section = None
        content_buffer = []

        lines = email_content.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            header_match = self.section_pattern.match(line)
            if header_match:
                if current_section:
                    sections[current_section] += "\n".join(content_buffer)
                    content_buffer = []
                current_section = header_match.group(1)
                self.logger.debug(f"Detected section header: {current_section}")
            elif current_section:
                content_buffer.append(line)

        # Add the last section
        if current_section and content_buffer:
            sections[current_section] += "\n".join(content_buffer)

        self.logger.debug(f"Sections Found: {list(sections.keys())}")
        return sections

    def extract_requesting_party(self, text: str):
        """
        Extracts data from the 'Requesting Party' section.

        Args:
            text (str): Content of the 'Requesting Party' section.

        Returns:
            dict: Extracted 'Requesting Party' data.
        """
        self.logger.debug("Extracting Requesting Party information.")
        data = {
            "Insurance Company": "N/A",
            "Handler": "N/A",
            "Carrier Claim Number": "N/A",
        }
        for key, pattern in self.patterns["Requesting Party"].items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                data[key] = value if value else "N/A"
                self.logger.debug(f"Found {key}: {value}")
            else:
                self.logger.debug(f"{key} not found, kept as 'N/A'")
        return {"Requesting Party": data}

    def extract_insured_information(self, text: str):
        """
        Extracts data from the 'Insured Information' section.

        Args:
            text (str): Content of the 'Insured Information' section.

        Returns:
            dict: Extracted 'Insured Information' data.
        """
        self.logger.debug("Extracting Insured Information.")
        data = {
            "Name": "N/A",
            "Contact #": "N/A",
            "Loss Address": "N/A",
            "Public Adjuster": "N/A",
            "Owner or Tenant": "N/A",
        }
        for key, pattern in self.patterns["Insured Information"].items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if key == "Owner or Tenant":
                    value = (
                        value.capitalize()
                        if value.lower() in ["owner", "tenant"]
                        else "N/A"
                    )
                data[key] = value if value else "N/A"
                self.logger.debug(f"Found {key}: {value}")
            else:
                self.logger.debug(f"{key} not found, kept as 'N/A'")
        return {"Insured Information": data}

    def extract_adjuster_information(self, text: str):
        """
        Extracts data from the 'Adjuster Information' section.

        Args:
            text (str): Content of the 'Adjuster Information' section.

        Returns:
            dict: Extracted 'Adjuster Information' data.
        """
        self.logger.debug("Extracting Adjuster Information.")
        data = {
            "Adjuster Name": "N/A",
            "Adjuster Phone Number": "N/A",
            "Adjuster Email": "N/A",
            "Job Title": "N/A",
            "Address": "N/A",
            "Policy #": "N/A",
        }
        for key, pattern in self.patterns["Adjuster Information"].items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if key == "Adjuster Phone Number":
                    value = self.format_phone_number(value)
                elif key == "Adjuster Email":
                    value = value.lower()
                data[key] = value if value else "N/A"
                self.logger.debug(f"Found {key}: {value}")
            else:
                self.logger.debug(f"{key} not found, kept as 'N/A'")
        return {"Adjuster Information": data}

    def extract_assignment_information(self, text: str):
        """
        Extracts data from the 'Assignment Information' section.

        Args:
            text (str): Content of the 'Assignment Information' section.

        Returns:
            dict: Extracted 'Assignment Information' data.
        """
        self.logger.debug("Extracting Assignment Information.")
        data = {
            "Date of Loss/Occurrence": "N/A",
            "Cause of loss": "N/A",
            "Facts of Loss": "N/A",
            "Loss Description": "N/A",
            "Residence Occupied During Loss": "N/A",
            "Was Someone home at time of damage": "N/A",
            "Repair or Mitigation Progress": "N/A",
            "Type": "N/A",
            "Inspection type": "N/A",
        }
        for key, pattern in self.patterns["Assignment Information"].items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if key == "Date of Loss/Occurrence":
                    value = self.parse_date(value)
                elif key in [
                    "Residence Occupied During Loss",
                    "Was Someone home at time of damage",
                ]:
                    value = self.parse_boolean(value)
                data[key] = value if value else "N/A"
                self.logger.debug(f"Found {key}: {value}")
            else:
                self.logger.debug(f"{key} not found, kept as 'N/A'")
        return {"Assignment Information": data}

    def extract_assignment_type(self, text: str):
        """
        Extracts the assignment type by checking the corresponding boxes.

        Args:
            text (str): Content of the 'Assignment Type' section.

        Returns:
            dict: Extracted 'Assignment Type' data.
        """
        self.logger.debug("Extracting Assignment Type.")
        data = {
            "Wind": False,
            "Structural": False,
            "Hail": False,
            "Foundation": False,
            "Other": {"Checked": False, "Details": "N/A"},
        }
        for key, pattern in self.patterns["Assignment Type"].items():
            match = pattern.search(text)
            if key != "Other":
                if match:
                    data[key] = True
                    self.logger.debug(f"Assignment Type '{key}' checked.")
            else:
                if match:
                    data["Other"]["Checked"] = True
                    details = match.group(2).strip() if match.lastindex >= 2 else "N/A"
                    data["Other"]["Details"] = details if details else "N/A"
                    self.logger.debug(
                        f"Assignment Type 'Other' checked with details: {details}"
                    )
        return {"Assignment Type": data}

    def extract_additional_details_special_instructions(self, text: str):
        """
        Extracts additional details or special instructions.

        Args:
            text (str): Content of the 'Additional details/Special Instructions' section.

        Returns:
            dict: Extracted additional details.
        """
        self.logger.debug("Extracting Additional Details/Special Instructions.")
        pattern = self.patterns["Additional details/Special Instructions"][
            "Additional details/Special Instructions"
        ]
        match = pattern.search(text)
        if match:
            value = match.group(1).strip()
            self.logger.debug(f"Found Additional details/Special Instructions: {value}")
        else:
            value = "N/A"
            self.logger.debug(
                "Additional details/Special Instructions not found, set to 'N/A'"
            )
        return {"Additional details/Special Instructions": value}

    def extract_attachments(self, text: str):
        """
        Extracts attachment information.

        Args:
            text (str): Content of the 'Attachment(s)' section.

        Returns:
            dict: Extracted attachment details.
        """
        self.logger.debug("Extracting Attachment(s).")
        pattern = self.patterns["Attachment(s)"]["Attachment(s)"]
        match = pattern.search(text)
        if match:
            attachments = match.group(1).strip()
            if attachments.lower() != "n/a" and attachments:
                attachment_list = re.split(r",|;|\n|•|–|-", attachments)
                attachment_list = [
                    att.strip() for att in attachment_list if att.strip()
                ]
                self.logger.debug(f"Found Attachments: {attachment_list}")
            else:
                attachment_list = ["N/A"]
                self.logger.debug("Attachments marked as 'N/A' or empty.")
        else:
            attachment_list = ["N/A"]
            self.logger.debug("Attachment(s) not found, set to ['N/A']")
        return {"Attachment(s)": attachment_list}

    def extract_entities(self, email_content: str):
        """
        Extracts named entities from the email content using spaCy.

        Args:
            email_content (str): The raw email content.

        Returns:
            dict: Extracted entities categorized by their labels.
        """
        self.logger.debug("Extracting Named Entities using spaCy.")
        doc = self.nlp(email_content)
        entities = {}
        relevant_labels = {"PERSON", "ORG", "GPE", "DATE", "PRODUCT"}
        for ent in doc.ents:
            if ent.label_ in relevant_labels:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)
        self.logger.debug(f"Extracted Entities: {entities}")
        return entities

    def format_phone_number(self, phone: str) -> str:
        """
        Formats the phone number to a standard format.

        Args:
            phone (str): Raw phone number.

        Returns:
            str: Formatted phone number.
        """
        digits = re.sub(r"\D", "", phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits.startswith("1"):
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            self.logger.warning(f"Unexpected phone number format: {phone}")
            return phone

    def parse_date(self, date_str: str) -> str:
        """
        Parses and standardizes date formats.

        Args:
            date_str (str): Raw date string.

        Returns:
            str: Standardized date in YYYY-MM-DD format or original string if parsing fails.
        """
        for fmt in self.date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
        self.logger.warning(f"Unable to parse date: {date_str}")
        return date_str

    def parse_boolean(self, value: str) -> str:
        """
        Parses boolean values from string.

        Args:
            value (str): String representation of a boolean value.

        Returns:
            str: 'Yes', 'No', or 'N/A' if parsing fails.
        """
        value = value.lower().strip()
        if value in self.boolean_values["positive"]:
            return "Yes"
        elif value in self.boolean_values["negative"]:
            return "No"
        else:
            self.logger.warning(f"Unable to parse boolean value: {value}")
            return "N/A"

    def enhance_logging(self):
        """
        Enhances logging by setting up structured logging and log levels.
        """
        # This method can be expanded to configure structured logging if needed
        pass

    def fallback_to_llm_parser(self, email_content: str):
        """
        Fallback mechanism to use LocalLLMParser if rule-based parsing fails.

        Args:
            email_content (str): The raw email content.

        Returns:
            dict: Parsed data from LocalLLMParser.
        """
        from src.parsers.local_llm_parser import LocalLLMParser

        self.logger.info("Falling back to LocalLLMParser for parsing.")
        llm_parser = LocalLLMParser()
        return llm_parser.parse(email_content)
