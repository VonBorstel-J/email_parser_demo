from flask import Flask, render_template, request
from src.email_parsing import EmailParser
import logging
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')  # Securely load secret key

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            except Exception as e:
                logger.error(f"An error occurred during parsing: {str(e)}")
                error_message = f"An error occurred during parsing: {str(e)}"
        else:
            error_message = "Please enter email content to parse."
    return render_template('index.html', parsed_data=parsed_data, error_message=error_message, selected_parser=selected_parser)

if __name__ == '__main__':
    app.run(debug=True)
