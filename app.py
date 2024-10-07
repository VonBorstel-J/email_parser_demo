# app.py

from flask import Flask, render_template, request
from src.email_parsing import EmailParser
import logging
from dotenv import load_dotenv
import os
import json_log_formatter  # New dependency for structured logging

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')  # Securely load secret key

# Configure structured logging
formatter = json_log_formatter.JSONFormatter()

json_handler = logging.StreamHandler()
json_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(json_handler)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture detailed logs

@app.route('/', methods=['GET', 'POST'])
def parse_email():
    parsed_data = None
    error_message = None
    selected_parser = 'rule_based'
    if request.method == 'POST':
        email_content = request.form.get('email_content', '').strip()
        selected_parser = request.form.get('parser_option', 'rule_based')
        if email_content:
            parser = EmailParser()
            try:
                parsed_data = parser.parse_email(email_content, selected_parser)
                logger.info(f"Parsing successful using {selected_parser} parser.")
            except ValueError as ve:
                logger.error(f"Validation error during parsing: {str(ve)}")
                error_message = f"Validation Error: {str(ve)}"
            except Exception as e:
                logger.error(f"An unexpected error occurred during parsing: {str(e)}")
                error_message = f"An unexpected error occurred: {str(e)}"
        else:
            error_message = "Please enter email content to parse."
    return render_template(
        'index.html',
        parsed_data=parsed_data,
        error_message=error_message,
        selected_parser=selected_parser
    )

if __name__ == '__main__':
    app.run(debug=True)
