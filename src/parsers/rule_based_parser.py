import logging
import re
import spacy
from src.parsers.base_parser import BaseParser

class RuleBasedParser(BaseParser):
    """An improved rule-based parser for comprehensive email parsing."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.nlp = spacy.load('en_core_web_sm')
            self.logger.info("spaCy model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load spaCy model: {e}")
            raise

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
        extracted_data.update(self.extract_requesting_party(sections.get('Requesting Party', '')))
        extracted_data.update(self.extract_insured_information(sections.get('Insured Information', '')))
        extracted_data.update(self.extract_adjuster_information(sections.get('Adjuster Information', '')))
        extracted_data.update(self.extract_assignment_information(sections.get('Assignment Information', '')))
        extracted_data.update(self.extract_assignment_type(sections.get('Assignment Type', '')))
        extracted_data.update(self.extract_additional_details(sections.get('Additional details/Special Instructions', '')))
        extracted_data.update(self.extract_attachments(sections.get('Attachment(s)', '')))

        # Extract entities using NLP
        entities = self.extract_entities(email_content)
        extracted_data['Entities'] = entities

        self.logger.debug(f"Extracted Data: {extracted_data}")
        self.logger.info("Successfully parsed email with RuleBasedParser.")
        return extracted_data

    def split_into_sections(self, email_content: str):
        """
        Splits the email content into sections based on the assignment schema headers.

        Args:
            email_content (str): The raw email content.

        Returns:
            dict: Sections of the email mapped to their content.
        """
        self.logger.debug("Splitting email content into sections.")
        section_headers = [
            'Requesting Party',
            'Insured Information',
            'Adjuster Information',
            'Assignment Information',
            'Assignment Type',
            'Additional details/Special Instructions',
            'Attachment(s)'
        ]

        sections = {}
        current_section = None
        for line in email_content.splitlines():
            line = line.strip()
            if line in section_headers:
                current_section = line
                sections[current_section] = ''
            elif current_section:
                sections[current_section] += line + '\n'

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
        data = {}
        patterns = {
            'Insurance Company': r'Insurance Company:\s*(.*)',
            'Handler': r'Handler:\s*(.*)',
            'Carrier Claim Number': r'Carrier Claim Number:\s*(.*)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            data[key] = match.group(1).strip() if match else 'N/A'

        self.logger.debug(f"Requesting Party Extracted: {data}")
        return data

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
        patterns = {
            'Name': r'Name:\s*(.*)',
            'Contact #': r'Contact #:\s*(.*)',
            'Loss Address': r'Loss Address:\s*(.*)',
            'Public Adjuster': r'Public Adjuster:\s*(.*)',
            'Owner or Tenant': r'Is the insured an Owner or a Tenant of the loss location\?\s*(.*)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            data[key] = match.group(1).strip() if match else 'N/A'

        self.logger.debug(f"Insured Information Extracted: {data}")
        return data

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
        patterns = {
            'Adjuster Name': r'Adjuster Name:\s*(.*)',
            'Adjuster Phone Number': r'Adjuster Phone Number:\s*(.*)',
            'Adjuster Email': r'Adjuster Email:\s*(.*)',
            'Job Title': r'Job Title:\s*(.*)',
            'Address': r'Address:\s*(.*)',
            'Policy #': r'Policy #:\s*(.*)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            data[key] = match.group(1).strip() if match else 'N/A'

        self.logger.debug(f"Adjuster Information Extracted: {data}")
        return data

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
        patterns = {
            'Date of Loss/Occurrence': r'Date of Loss/Occurrence:\s*(.*)',
            'Cause of loss': r'Cause of loss:\s*(.*)',
            'Facts of Loss': r'Facts of Loss:\s*(.*)',
            'Loss Description': r'Loss Description:\s*(.*)',
            'Residence Occupied During Loss': r'Residence Occupied During Loss:\s*(.*)',
            'Was Someone home at time of damage': r'Was Someone home at time of damage:\s*(.*)',
            'Repair or Mitigation Progress': r'Repair or Mitigation Progress:\s*(.*)',
            'Type': r'Type:\s*(.*)',
            'Inspection type': r'Inspection type:\s*(.*)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            data[key] = match.group(1).strip() if match else 'N/A'

        self.logger.debug(f"Assignment Information Extracted: {data}")
        return data

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
            'Wind': False,
            'Structural': False,
            'Hail': False,
            'Foundation': False,
            'Other': {
                'Checked': False,
                'Details': ''
            }
        }

        patterns = {
            'Wind': r'Wind\s*\[([xX ])\]',
            'Structural': r'Structural\s*\[([xX ])\]',
            'Hail': r'Hail\s*\[([xX ])\]',
            'Foundation': r'Foundation\s*\[([xX ])\]',
            'Other': r'Other\s*\[\s*\]\s*-\s*provide details:\s*(.*)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if key != 'Other':
                if match:
                    data[key] = True if match.group(1).strip().upper() == 'X' else False
            else:
                if match:
                    data['Other']['Checked'] = True
                    data['Other']['Details'] = match.group(1).strip() if match.group(1).strip() else 'N/A'

        self.logger.debug(f"Assignment Type Extracted: {data}")
        return data

    def extract_additional_details(self, text: str):
        """
        Extracts additional details or special instructions.

        Args:
            text (str): Content of the 'Additional details/Special Instructions' section.

        Returns:
            dict: Extracted additional details.
        """
        self.logger.debug("Extracting Additional Details/Special Instructions.")
        data = {}
        pattern = r'Additional details/Special Instructions:\s*(.*)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        data['Additional details/Special Instructions'] = match.group(1).strip() if match else 'N/A'

        self.logger.debug(f"Additional Details Extracted: {data}")
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
        pattern = r'Attachment\(s\):\s*(.*)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        attachments = match.group(1).strip() if match else 'N/A'

        if attachments != 'N/A':
            # Assuming attachments are listed separated by commas or semicolons
            attachment_list = re.split(r',|;', attachments)
            attachment_list = [att.strip() for att in attachment_list if att.strip()]
            data['Attachment(s)'] = attachment_list
        else:
            data['Attachment(s)'] = 'N/A'

        self.logger.debug(f"Attachment(s) Extracted: {data}")
        return data

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
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)

        self.logger.debug(f"Extracted Entities: {entities}")
        return entities
