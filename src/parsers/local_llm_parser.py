
# src/parsers/local_llm_parser.py

import logging
import json
import re
import os
import requests
import time
from requests.exceptions import RequestException
from src.parsers.base_parser import BaseParser
from dotenv import load_dotenv
from src.utils.validation import validate_json  
import jsonschema
import validators  # New dependency for URL validation


# Load environment variables from .env
load_dotenv()

# Define the JSON schema based on the assignment schema
assignment_schema = {
    "type": "object",
    "properties": {
        "Requesting Party": {
            "type": "object",
            "properties": {
                "Insurance Company": {"type": "string"},
                "Handler": {"type": "string"},
                "Carrier Claim Number": {"type": "string"},
            },
            "required": ["Insurance Company", "Handler", "Carrier Claim Number"],
        },
        "Insured Information": {
            "type": "object",
            "properties": {
                "Name": {"type": "string"},
                "Contact #": {"type": "string"},
                "Loss Address": {"type": "string"},
                "Public Adjuster": {"type": "string"},
                "Owner or Tenant": {"type": "string"},
            },
            "required": [
                "Name",
                "Contact #",
                "Loss Address",
                "Public Adjuster",
                "Owner or Tenant",
            ],
        },
        "Adjuster Information": {
            "type": "object",
            "properties": {
                "Adjuster Name": {"type": "string"},
                "Adjuster Phone Number": {"type": "string"},
                "Adjuster Email": {"type": "string"},
                "Job Title": {"type": "string"},
                "Address": {"type": "string"},
                "Policy #": {"type": "string"},
            },
            "required": [
                "Adjuster Name",
                "Adjuster Phone Number",
                "Adjuster Email",
                "Job Title",
                "Address",
                "Policy #",
            ],
        },
        "Assignment Information": {
            "type": "object",
            "properties": {
                "Date of Loss/Occurrence": {"type": "string"},
                "Cause of loss": {"type": "string"},
                "Facts of Loss": {"type": "string"},
                "Loss Description": {"type": "string"},
                "Residence Occupied During Loss": {"type": "string"},
                "Was Someone home at time of damage": {"type": "string"},
                "Repair or Mitigation Progress": {"type": "string"},
                "Type": {"type": "string"},
                "Inspection type": {"type": "string"},
            },
            "required": [
                "Date of Loss/Occurrence",
                "Cause of loss",
                "Facts of Loss",
                "Loss Description",
                "Residence Occupied During Loss",
                "Was Someone home at time of damage",
                "Repair or Mitigation Progress",
                "Type",
                "Inspection type",
            ],
        },
        "Assignment Type": {
            "type": "object",
            "properties": {
                "Wind": {"type": "boolean"},
                "Structural": {"type": "boolean"},
                "Hail": {"type": "boolean"},
                "Foundation": {"type": "boolean"},
                "Other": {
                    "type": "object",
                    "properties": {
                        "Checked": {"type": "boolean"},
                        "Details": {"type": "string"},
                    },
                    "required": ["Checked", "Details"],
                },
            },
            "required": ["Wind", "Structural", "Hail", "Foundation", "Other"],
        },
        "Additional details/Special Instructions": {"type": "string"},
        "Attachment(s)": {"type": "array", "items": {"type": "string"}},
        "Entities": {
            "type": "object",
            "additionalProperties": {"type": "array", "items": {"type": "string"}},
        },
    },
    "required": [
        "Requesting Party",
        "Insured Information",
        "Adjuster Information",
        "Assignment Information",
        "Assignment Type",
        "Additional details/Special Instructions",
        "Attachment(s)",
        "Entities",
    ],
}


def validate_json(parsed_data):
    try:
        validate(instance=parsed_data, schema=assignment_schema)
        return True, ""
    except jsonschema.exceptions.ValidationError as err:
        return False, err.message


class LocalLLMParser(BaseParser):
    """Parser that uses a Local LLM hosted on LLM Studio to parse email content."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_endpoint = os.getenv("LOCAL_LLM_API_ENDPOINT")
        self.api_key = os.getenv("LOCAL_LLM_API_KEY")  # If your API requires a key

        if not self.api_endpoint:
            self.logger.error(
                "LOCAL_LLM_API_ENDPOINT not set in environment variables."
            )
            raise ValueError("LOCAL_LLM_API_ENDPOINT is required.")

        self.headers = {"Content-Type": "application/json"}

        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        # Verify that the API is reachable
        try:
            response = requests.get(self.api_endpoint, headers=self.headers, timeout=10)
            if response.status_code == 200:
                self.logger.info("Connected to LLM Studio successfully.")
            else:
                self.logger.error(
                    f"Failed to connect to LLM Studio. Status Code: {response.status_code}"
                )
                raise ConnectionError(
                    f"Failed to connect to LLM Studio. Status Code: {response.status_code}"
                )
        except Exception as e:
            self.logger.error(f"Error connecting to LLM Studio: {e}")
            raise

    def parse(self, email_content: str):
        self.logger.info("Parsing email content with LocalLLMParser.")
        prompt = (
            "You are an assistant specialized in extracting information from insurance claim emails. "
            "Please extract the following information from the email content and provide it in pure JSON format without any markdown, code blocks, or additional text. "
            "Ensure that the JSON strictly follows the given schema. Do not include any explanations or comments.\n\n"
            "Assignment Schema:\n"
            "{\n"
            '  "Requesting Party": {\n'
            '    "Insurance Company": "",\n'
            '    "Handler": "",\n'
            '    "Carrier Claim Number": ""\n'
            "  },\n"
            '  "Insured Information": {\n'
            '    "Name": "",\n'
            '    "Contact #": "",\n'
            '    "Loss Address": "",\n'
            '    "Public Adjuster": "",\n'
            '    "Owner or Tenant": ""\n'
            "  },\n"
            '  "Adjuster Information": {\n'
            '    "Adjuster Name": "",\n'
            '    "Adjuster Phone Number": "",\n'
            '    "Adjuster Email": "",\n'
            '    "Job Title": "",\n'
            '    "Address": "",\n'
            '    "Policy #": ""\n'
            "  },\n"
            '  "Assignment Information": {\n'
            '    "Date of Loss/Occurrence": "",\n'
            '    "Cause of loss": "",\n'
            '    "Facts of Loss": "",\n'
            '    "Loss Description": "",\n'
            '    "Residence Occupied During Loss": "",\n'
            '    "Was Someone home at time of damage": "",\n'
            '    "Repair or Mitigation Progress": "",\n'
            '    "Type": "",\n'
            '    "Inspection type": ""\n'
            "  },\n"
            '  "Assignment Type": {\n'
            '    "Wind": false,\n'
            '    "Structural": false,\n'
            '    "Hail": false,\n'
            '    "Foundation": false,\n'
            '    "Other": {\n'
            '      "Checked": false,\n'
            '      "Details": ""\n'
            "    }\n"
            "  },\n"
            '  "Additional details/Special Instructions": "",\n'
            '  "Attachment(s)": []\n'
            "}\n\n"
            "Email Content:\n"
            f"{email_content}\n\n"
            "Please provide the extracted information strictly in the JSON format as shown above."
        )
        try:
            response = self.generate(prompt)
            self.logger.debug(f"Raw LLM response: {response}")

            # Clean the response by removing any code blocks or markdown
            cleaned_response = self._clean_response(response)
            self.logger.debug(f"Cleaned LLM response: {cleaned_response}")

            # Parse the cleaned response as JSON
            extracted_data = json.loads(cleaned_response)

            # Validate the JSON against the schema
            is_valid, error_message = validate_json(extracted_data)
            if not is_valid:
                self.logger.error(f"JSON Schema Validation Error: {error_message}")
                raise ValueError(f"JSON Schema Validation Error: {error_message}")

            self.logger.info(
                "Successfully parsed and validated email using LocalLLMParser."
            )
            return extracted_data
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from Local LLM response: {str(e)}")
            self.logger.error(f"Response Text: ```\n{response}\n```")
            raise ValueError(
                "The Local LLM did not return valid JSON. Please check the response and adjust the prompt if necessary."
            ) from e
        except Exception as e:
            self.logger.error(f"Error during Local LLM parsing: {str(e)}")
            raise

    def generate(self, prompt: str) -> str:
        """
        Generate text using the local LLM via LLM Studio's API.

        Args:
            prompt (str): The prompt to send to the LLM.

        Returns:
            str: The generated text from the LLM.
        """
        payload = {
            "prompt": prompt,
            "max_tokens": 1500,  # Adjusted from 131072 to 1500 for practical limits
            "temperature": 0.2,  # Lower temperature for deterministic output
            "n": 1,  # Number of completions to generate
            "stop": ["}"],  # Stop after the closing brace
        }

        retries = 3
        backoff_factor = 2

        for attempt in range(1, retries + 1):
            try:
                self.logger.info("Sending request to Local LLM API.")
                response = requests.post(
                    self.api_endpoint, headers=self.headers, json=payload, timeout=60
                )  # Reduced timeout

                if response.status_code != 200:
                    self.logger.error(
                        f"LLM API responded with status code {response.status_code}: {response.text}"
                    )
                    raise ConnectionError(
                        f"LLM API error: {response.status_code} - {response.text}"
                    )

                response_json = response.json()

                # Adjust based on LLM Studio's API response structure
                # Assuming LLM Studio's API returns a similar structure to OpenAI's
                generated_text = (
                    response_json.get("choices", [{}])[0].get("text", "").strip()
                )
                if not generated_text:
                    self.logger.error("LLM API returned empty response.")
                    raise ValueError("LLM API returned empty response.")

                self.logger.info("Received response from Local LLM API.")
                return generated_text
            except (RequestException, ConnectionError) as e:
                self.logger.error(
                    f"Attempt {attempt} - HTTP request to LLM API failed: {str(e)}"
                )
                if attempt < retries:
                    sleep_time = backoff_factor**attempt
                    self.logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    self.logger.error("Max retries exceeded.")
                    raise
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"Failed to decode JSON from LLM API response: {str(e)}"
                )
                raise ValueError("Invalid JSON response from LLM API.") from e

    def _clean_response(self, response: str) -> str:
        """
        Cleans the LLM response by removing markdown code blocks and any extraneous text.

        Args:
            response (str): The raw response from the LLM.

        Returns:
            str: Cleaned JSON string.
        """
        # Remove markdown code blocks if present
        response = re.sub(r'```(?:json)?\s*', '', response)
        # Remove any trailing or leading whitespace
        response = response.strip()

        # Extract the JSON part using regex
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        else:
            self.logger.warning("No JSON object found in the LLM response.")
            # Optionally, raise an error or handle it accordingly
            raise ValueError("No JSON object found in the LLM response.")

        # Ensure that the JSON string ends properly
        if not response.endswith('}'):
            response += '}'

        return response
