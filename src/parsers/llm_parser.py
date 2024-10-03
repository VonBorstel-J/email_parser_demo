# src/parsers/llm_parser.py
import logging
import os
import json
import openai


class LLMParser:
    """Parser that uses OpenAI's GPT-3 to parse email content."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        openai.api_key = os.getenv('OPENAI_API_KEY')
        if not openai.api_key:
            raise ValueError("OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")

    def parse(self, email_content: str):
        self.logger.info("Parsing email content with LLMParser.")
        prompt = f"Extract key information from the following email and provide it in JSON format:\n\n{email_content}"
        try:
            response = openai.Completion.create(
                engine='text-davinci-003',
                prompt=prompt,
                max_tokens=500,
                temperature=0.2,
                n=1,
                stop=None,
            )
            extracted_text = response.choices[0].text.strip()
            # Try to parse the response as JSON
            extracted_data = json.loads(extracted_text)
            return extracted_data
        except Exception as e:
            self.logger.error(f"Error during LLM parsing: {str(e)}")
            raise
