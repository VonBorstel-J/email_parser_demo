"""Module containing the RuleBasedParser class for parsing emails using a rule-based approach."""

import os
import logging
import re
from datetime import datetime

import spacy
from spacy.cli import download as spacy_download
from spacy.util import is_package
import yaml

from src.parsers.base_parser import BaseParser
from src.utils.validation import validate_json

# Constants for repeated strings
REQUESTING_PARTY = "Requesting Party"
INSURED_INFORMATION = "Insured Information"
ADJUSTER_INFORMATION = "Adjuster Information"
ASSIGNMENT_INFORMATION = "Assignment Information"
ASSIGNMENT_TYPE = "Assignment Type"
ADDITIONAL_DETAILS = "Additional details/Special Instructions"
ATTACHMENTS = "Attachment(s)"
CARRIER_CLAIM_NUMBER = "Carrier Claim Number"
OWNER_OR_TENANT = "Owner or Tenant"
ADJUSTER_PHONE_NUMBER = "Adjuster Phone Number"
ADJUSTER_EMAIL = "Adjuster Email"
POLICY_NUMBER = "Policy #"
DATE_OF_LOSS = "Date of Loss/Occurrence"
RESIDENCE_OCCUPIED_DURING_LOSS = "Residence Occupied During Loss"
WAS_SOMEONE_HOME = "Was Someone home at time of damage"

# Constants for log messages
FOUND_MESSAGE = "Found %s: %s"
FOUND_ADDITIONAL_PATTERN_MESSAGE = "Found %s using additional pattern: %s"
NOT_FOUND_MESSAGE = "%s not found, set to 'N/A'"


class RuleBasedParser(BaseParser):
    """An improved and enhanced rule-based parser for comprehensive email parsing."""

    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ensure_spacy_model()
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.logger.info("spaCy model 'en_core_web_sm' loaded successfully.")
        except OSError as e:
            self.logger.error("Failed to load spaCy model: %s", e)
            raise

        # Load configuration for patterns if provided
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
            self.logger.info("Loaded parser configuration from %s.", config_path)
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

    def ensure_spacy_model(self):
        """
        Ensures that the spaCy model 'en_core_web_sm' is installed.
        Downloads the model if it's not present.
        """
        model_name = "en_core_web_sm"
        if not is_package(model_name):
            self.logger.warning(
                "spaCy model '%s' not found. Downloading...", model_name
            )
            try:
                spacy_download(model_name)
                self.logger.info(
                    "Successfully downloaded spaCy model '%s'.", model_name
                )
            except OSError as e:
                self.logger.error(
                    "Failed to download spaCy model '%s': %s", model_name, e
                )
                raise

    def default_config(self):
        """Provides the default configuration for the parser."""
        return {
            "section_headers": [
                REQUESTING_PARTY,
                INSURED_INFORMATION,
                ADJUSTER_INFORMATION,
                ASSIGNMENT_INFORMATION,
                ASSIGNMENT_TYPE,
                ADDITIONAL_DETAILS,
                ATTACHMENTS,
            ],
            "patterns": {
                REQUESTING_PARTY: {
                    "Insurance Company": r"Insurance Company\s*:\s*(.*)",
                    "Handler": r"Handler\s*:\s*(.*)",
                    CARRIER_CLAIM_NUMBER: r"Carrier Claim Number\s*:\s*(.*)",
                },
                INSURED_INFORMATION: {
                    "Name": r"Name\s*:\s*(.*)",
                    "Contact #": r"Contact #\s*:\s*(.*)",
                    "Loss Address": r"Loss Address\s*:\s*(.*)",
                    "Public Adjuster": r"Public Adjuster\s*:\s*(.*)",
                    OWNER_OR_TENANT: (
                        r"Is the insured an Owner or a Tenant of the loss location\?\s*"
                        r"(Yes|No|Owner|Tenant)"
                    ),
                },
                ADJUSTER_INFORMATION: {
                    "Adjuster Name": r"Adjuster Name\s*:\s*(.*)",
                    ADJUSTER_PHONE_NUMBER: r"Adjuster Phone Number\s*:\s*(\+?\d[\d\s\-().]{7,}\d)",
                    ADJUSTER_EMAIL: r"Adjuster Email\s*:\s*([\w\.-]+@[\w\.-]+\.\w+)",
                    "Job Title": r"Job Title\s*:\s*(.*)",
                    "Address": r"Address\s*:\s*(.*)",
                    POLICY_NUMBER: r"Policy #\s*:\s*(\w+)",
                },
                ASSIGNMENT_INFORMATION: {
                    DATE_OF_LOSS: (
                        r"Date of Loss/Occurrence\s*:\s*"
                        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
                    ),
                    "Cause of loss": r"Cause of loss\s*:\s*(.*)",
                    "Facts of Loss": r"Facts of Loss\s*:\s*(.*)",
                    "Loss Description": r"Loss Description\s*:\s*(.*)",
                    RESIDENCE_OCCUPIED_DURING_LOSS: (
                        r"Residence Occupied During Loss\s*:\s*(Yes|No)"
                    ),
                    WAS_SOMEONE_HOME: (
                        r"Was Someone home at time of damage\s*:\s*(Yes|No)"
                    ),
                    "Repair or Mitigation Progress": r"Repair or Mitigation Progress\s*:\s*(.*)",
                    "Type": r"Type\s*:\s*(.*)",
                    "Inspection type": r"Inspection type\s*:\s*(.*)",
                },
                ASSIGNMENT_TYPE: {
                    "Wind": r"Wind\s*\[\s*([xX])\s*\]",
                    "Structural": r"Structural\s*\[\s*([xX])\s*\]",
                    "Hail": r"Hail\s*\[\s*([xX])\s*\]",
                    "Foundation": r"Foundation\s*\[\s*([xX])\s*\]",
                    "Other": r"Other\s*\[\s*([xX])\s*\]\s*-\s*provide details\s*:\s*(.*)",
                },
                ADDITIONAL_DETAILS: {
                    ADDITIONAL_DETAILS: r"Additional details/Special Instructions\s*:\s*(.*)"
                },
                ATTACHMENTS: {ATTACHMENTS: r"Attachment\(s\)\s*:\s*(.*)"},
            },
            "additional_patterns": {
                REQUESTING_PARTY: {
                    POLICY_NUMBER: r"Policy\s*Number\s*:\s*(\w+)",
                    CARRIER_CLAIM_NUMBER: r"Claim\s*Number\s*:\s*(.*)",
                },
                ASSIGNMENT_INFORMATION: {
                    DATE_OF_LOSS: (
                        r"Date of Loss(?:/Occurrence)?\s*:\s*"
                        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
                    )
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
        extracted_data = {}

        # Extract sections based on the assignment schema
        sections = self.split_into_sections(email_content)

        # Extract data from each section
        for section, content in sections.items():
            extract_method = getattr(self, f"extract_{self.snake_case(section)}", None)
            if extract_method:
                try:
                    data = extract_method(content)
                    extracted_data.update(data)
                except Exception as e:
                    self.logger.error("Error extracting section '%s': %s", section, e)
                    extracted_data.update(self.default_section_data(section))
            else:
                self.logger.warning(
                    "No extraction method found for section: %s", section
                )
                extracted_data.update(self.default_section_data(section))

        # Ensure 'Additional details/Special Instructions' is always present
        if ADDITIONAL_DETAILS not in extracted_data:
            extracted_data.update(self.default_section_data(ADDITIONAL_DETAILS))

        # Extract entities using NLP
        entities = self.extract_entities(email_content)
        extracted_data["Entities"] = entities

        # Validate the extracted data against the JSON schema
        is_valid, error_message = validate_json(extracted_data)
        if not is_valid:
            self.logger.error("JSON Schema Validation Error: %s", error_message)
            raise ValueError(f"JSON Schema Validation Error: {error_message}")

        self.logger.debug("Extracted Data: %s", extracted_data)
        self.logger.info("Successfully parsed email with RuleBasedParser.")
        return extracted_data

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
        sections = {}
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
                    sections[current_section] = "\n".join(content_buffer).strip()
                    content_buffer = []
                current_section = header_match.group(1)
                sections[current_section] = ""
                self.logger.debug("Detected section header: %s", current_section)
            elif current_section:
                content_buffer.append(line)

        # Add the last section
        if current_section and content_buffer:
            sections[current_section] = "\n".join(content_buffer).strip()

        # Handle additional patterns for missing sections
        for section in self.section_headers:
            if section not in sections:
                self.logger.warning("Section '%s' not found in email content.", section)
                sections[section] = ""

        self.logger.debug("Sections Found: %s", list(sections.keys()))
        return sections

    def default_section_data(self, section: str) -> dict:
        """
        Provides default data structure for missing sections.

        Args:
            section (str): The name of the section.

        Returns:
            dict: Default data for the section.
        """
        default_data = {}
        if section == REQUESTING_PARTY:
            default_data[REQUESTING_PARTY] = {
                "Insurance Company": "N/A",
                "Handler": "N/A",
                CARRIER_CLAIM_NUMBER: "N/A",
            }
        elif section == INSURED_INFORMATION:
            default_data[INSURED_INFORMATION] = {
                "Name": "N/A",
                "Contact #": "N/A",
                "Loss Address": "N/A",
                "Public Adjuster": "N/A",
                OWNER_OR_TENANT: "N/A",
            }
        elif section == ADJUSTER_INFORMATION:
            default_data[ADJUSTER_INFORMATION] = {
                "Adjuster Name": "N/A",
                ADJUSTER_PHONE_NUMBER: "N/A",
                ADJUSTER_EMAIL: "N/A",
                "Job Title": "N/A",
                "Address": "N/A",
                POLICY_NUMBER: "N/A",
            }
        elif section == ASSIGNMENT_INFORMATION:
            default_data[ASSIGNMENT_INFORMATION] = {
                DATE_OF_LOSS: "N/A",
                "Cause of loss": "N/A",
                "Facts of Loss": "N/A",
                "Loss Description": "N/A",
                RESIDENCE_OCCUPIED_DURING_LOSS: "N/A",
                WAS_SOMEONE_HOME: "N/A",
                "Repair or Mitigation Progress": "N/A",
                "Type": "N/A",
                "Inspection type": "N/A",
            }
        elif section == ASSIGNMENT_TYPE:
            default_data[ASSIGNMENT_TYPE] = {
                "Wind": False,
                "Structural": False,
                "Hail": False,
                "Foundation": False,
                "Other": {"Checked": False, "Details": "N/A"},
            }
        elif section == ADDITIONAL_DETAILS:
            default_data[ADDITIONAL_DETAILS] = "N/A"
        elif section == ATTACHMENTS:
            default_data[ATTACHMENTS] = []
        return default_data

    def extract_requesting_party(self, text: str):
        """
        Extracts data from the 'Requesting Party' section.

        Args:
            text (str): Content of the 'Requesting Party' section.

        Returns:
            dict: Extracted 'Requesting Party' data.
        """
        self.logger.debug("Extracting Requesting Party information.")
        data = {}
        for key, pattern in self.patterns[REQUESTING_PARTY].items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                # Handle alternative patterns
                if not value and key in self.additional_patterns.get(
                    REQUESTING_PARTY, {}
                ):
                    alt_pattern = self.additional_patterns[REQUESTING_PARTY][key]
                    alt_match = alt_pattern.search(text)
                    value = alt_match.group(1).strip() if alt_match else "N/A"
                data[key] = value if value else "N/A"
                self.logger.debug(FOUND_MESSAGE, key, value)
            else:
                # Attempt to find using additional patterns if applicable
                if key in self.additional_patterns.get(REQUESTING_PARTY, {}):
                    alt_pattern = self.additional_patterns[REQUESTING_PARTY][key]
                    alt_match = alt_pattern.search(text)
                    value = alt_match.group(1).strip() if alt_match else "N/A"
                    data[key] = value if value else "N/A"
                    if value != "N/A":
                        self.logger.debug(FOUND_ADDITIONAL_PATTERN_MESSAGE, key, value)
                    else:
                        self.logger.debug(NOT_FOUND_MESSAGE, key)
                else:
                    data[key] = "N/A"
                    self.logger.debug(NOT_FOUND_MESSAGE, key)
        return {REQUESTING_PARTY: data}

    def extract_insured_information(self, text: str):
        """
        Extracts data from the 'Insured Information' section.

        Args:
            text (str): Content of the 'Insured Information' section.

        Returns:
            dict: Extracted 'Insured Information' data.
        """
        self.logger.debug("Extracting Insured Information.")
        data = {}
        for key, pattern in self.patterns[INSURED_INFORMATION].items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                if key == OWNER_OR_TENANT:
                    value = (
                        value.capitalize()
                        if value.lower() in ["yes", "no", "owner", "tenant"]
                        else "N/A"
                    )
                data[key] = value if value else "N/A"
                self.logger.debug(FOUND_MESSAGE, key, value)
            else:
                # Attempt to find using additional patterns if applicable
                if key in self.additional_patterns.get(INSURED_INFORMATION, {}):
                    alt_pattern = self.additional_patterns[INSURED_INFORMATION][key]
                    alt_match = alt_pattern.search(text)
                    value = alt_match.group(1).strip() if alt_match else "N/A"
                    data[key] = value if value else "N/A"
                    if value != "N/A":
                        self.logger.debug(FOUND_ADDITIONAL_PATTERN_MESSAGE, key, value)
                    else:
                        self.logger.debug(NOT_FOUND_MESSAGE, key)
                else:
                    data[key] = "N/A"
                    self.logger.debug(NOT_FOUND_MESSAGE, key)
        return {INSURED_INFORMATION: data}

    def extract_adjuster_information(self, text: str):
        """
        Extracts data from the 'Adjuster Information' section.

        Args:
            text (str): Content of the 'Adjuster Information' section.

        Returns:
            dict: Extracted 'Adjuster Information' data.
        """
        self.logger.debug("Extracting Adjuster Information.")
        data = {}
        for key, pattern in self.patterns[ADJUSTER_INFORMATION].items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                # Specific handling for phone numbers and emails
                if key == ADJUSTER_PHONE_NUMBER:
                    value = self.format_phone_number(value)
                elif key == ADJUSTER_EMAIL:
                    value = value.lower()
                data[key] = value if value else "N/A"
                self.logger.debug(FOUND_MESSAGE, key, value)
            else:
                # Attempt to find using additional patterns if applicable
                if key in self.additional_patterns.get(ADJUSTER_INFORMATION, {}):
                    alt_pattern = self.additional_patterns[ADJUSTER_INFORMATION][key]
                    alt_match = alt_pattern.search(text)
                    value = alt_match.group(1).strip() if alt_match else "N/A"
                    data[key] = value if value else "N/A"
                    if value != "N/A":
                        self.logger.debug(FOUND_ADDITIONAL_PATTERN_MESSAGE, key, value)
                    else:
                        self.logger.debug(NOT_FOUND_MESSAGE, key)
                else:
                    data[key] = "N/A"
                    self.logger.debug(NOT_FOUND_MESSAGE, key)
        return {ADJUSTER_INFORMATION: data}

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
            self.logger.warning("Unexpected phone number format: %s", phone)
            return phone  # Return as is if format is unexpected

    def extract_assignment_information(self, text: str):
        """
        Extracts data from the 'Assignment Information' section.

        Args:
            text (str): Content of the 'Assignment Information' section.

        Returns:
            dict: Extracted 'Assignment Information' data.
        """
        self.logger.debug("Extracting Assignment Information.")
        data = {}
        for key, pattern in self.patterns[ASSIGNMENT_INFORMATION].items():
            match = pattern.search(text)
            if match:
                value = match.group(1).strip()
                # Specific handling for dates
                if key == DATE_OF_LOSS:
                    value = self.parse_date(value)
                elif key in [
                    RESIDENCE_OCCUPIED_DURING_LOSS,
                    WAS_SOMEONE_HOME,
                ]:
                    value = (
                        value.capitalize() if value.lower() in ["yes", "no"] else "N/A"
                    )
                data[key] = value if value else "N/A"
                self.logger.debug(FOUND_MESSAGE, key, value)
            else:
                # Attempt to find using additional patterns if applicable
                if key in self.additional_patterns.get(ASSIGNMENT_INFORMATION, {}):
                    alt_pattern = self.additional_patterns[ASSIGNMENT_INFORMATION][key]
                    alt_match = alt_pattern.search(text)
                    value = alt_match.group(1).strip() if alt_match else "N/A"
                    if value:
                        if key == DATE_OF_LOSS:
                            value = self.parse_date(value)
                        elif key in [
                            RESIDENCE_OCCUPIED_DURING_LOSS,
                            WAS_SOMEONE_HOME,
                        ]:
                            value = (
                                value.capitalize()
                                if value.lower() in ["yes", "no"]
                                else "N/A"
                            )
                        data[key] = value
                        self.logger.debug(FOUND_ADDITIONAL_PATTERN_MESSAGE, key, value)
                    else:
                        data[key] = "N/A"
                        self.logger.debug(NOT_FOUND_MESSAGE, key)
                else:
                    data[key] = "N/A"
                    self.logger.debug(NOT_FOUND_MESSAGE, key)
        return {ASSIGNMENT_INFORMATION: data}

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
                standardized_date = date_obj.strftime("%Y-%m-%d")
                self.logger.debug(
                    "Parsed date '%s' as '%s' using format '%s'.",
                    date_str,
                    standardized_date,
                    fmt,
                )
                return standardized_date
            except ValueError:
                continue
        self.logger.warning("Unable to parse date: %s", date_str)
        return date_str  # Return as is if parsing fails

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

        for key, pattern in self.patterns[ASSIGNMENT_TYPE].items():
            match = pattern.search(text)
            if key != "Other":
                if match:
                    data[key] = True
                    self.logger.debug("Assignment Type '%s' checked.", key)
            else:
                if match:
                    data["Other"]["Checked"] = True
                    details = match.group(2).strip() if match.lastindex >= 2 else "N/A"
                    data["Other"]["Details"] = details if details else "N/A"
                    self.logger.debug(
                        "Assignment Type 'Other' checked with details: %s", details
                    )
        return {ASSIGNMENT_TYPE: data}

    def extract_additional_details_special_instructions(self, text: str):
        """
        Extracts additional details or special instructions.

        Args:
            text (str): Content of the 'Additional details/Special Instructions' section.

        Returns:
            dict: Extracted additional details.
        """
        self.logger.debug("Extracting Additional Details/Special Instructions.")
        data = {}
        pattern = self.patterns[ADDITIONAL_DETAILS][ADDITIONAL_DETAILS]
        match = pattern.search(text)
        if match:
            value = match.group(1).strip()
            data[ADDITIONAL_DETAILS] = value if value else "N/A"
            self.logger.debug(
                "Found Additional details/Special Instructions: %s", value
            )
        else:
            data[ADDITIONAL_DETAILS] = "N/A"
            self.logger.debug(
                "Additional details/Special Instructions not found, set to 'N/A'"
            )
        return data

    def extract_attachments(self, text: str):
        """
        Extracts attachment information.

        Args:
            text (str): Content of the 'Attachment(s)' section.

        Returns:
            dict: Extracted attachment details.
        """
        self.logger.debug("Extracting Attachment(s).")
        data = {}
        pattern = self.patterns[ATTACHMENTS][ATTACHMENTS]
        match = pattern.search(text)
        if match:
            attachments = match.group(1).strip()
            if attachments.lower() != "n/a" and attachments:
                # Split by multiple delimiters
                attachment_list = re.split(r",|;|\n|•|–|-", attachments)
                # Further filter and validate attachment entries
                attachment_list = [
                    att.strip()
                    for att in attachment_list
                    if att.strip()
                    and (
                        self.is_valid_attachment(att.strip())
                        or self.is_valid_url(att.strip())
                    )
                ]
                data[ATTACHMENTS] = attachment_list if attachment_list else []
                self.logger.debug("Found Attachments: %s", attachment_list)
            else:
                data[ATTACHMENTS] = []
                self.logger.debug("Attachments marked as 'N/A' or empty.")
        else:
            data[ATTACHMENTS] = []
            self.logger.debug("Attachment(s) not found, set to empty list")
        return data

    def is_valid_attachment(self, attachment: str) -> bool:
        """Simple validation for file extensions."""
        valid_extensions = [".pdf", ".docx", ".xlsx", ".zip", ".png", ".jpg"]
        return any(attachment.lower().endswith(ext) for ext in valid_extensions)

    def is_valid_url(self, attachment: str) -> bool:
        """Simple URL validation."""
        url_pattern = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:\S+(?::\S*)?@)?"  # user:pass@
            r"(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])\."  # IP...
            r"(?:1?\d{1,2}|2[0-4]\d|25[0-5])\."
            r"(?:1?\d{1,2}|2[0-4]\d|25[0-5])\."
            r"(?:1?\d{1,2}|2[0-4]\d|25[0-5]))|"  # ...or
            r"(?:(?:[a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))"  # domain...
            r"(?::\d{2,5})?"  # optional port
            r"(?:/\S*)?$",
            re.IGNORECASE,
        )
        return re.match(url_pattern, attachment) is not None

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
        self.logger.debug("Extracted Entities: %s", entities)
        return entities

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
        from src.parsers.local_llm_parser import LocalLLMParser  # pylint: disable=C0415

        self.logger.info("Falling back to LocalLLMParser for parsing.")
        llm_parser = LocalLLMParser()
        return llm_parser.parse(email_content)
