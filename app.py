from flask import Flask, render_template, request, jsonify, send_file
from src.email_parsing import EmailParser  # Ensure this path is correct
from src.utils.quickbase_schema import QUICKBASE_SCHEMA
import logging
from dotenv import load_dotenv
import os
import json_log_formatter
import pandas as pd
import io

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "your_secret_key"
)  # Securely load secret key

# Configure structured logging
formatter = json_log_formatter.JSONFormatter()

json_handler = logging.StreamHandler()
json_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(json_handler)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture detailed logs


@app.route("/", methods=["GET", "POST"])
def parse_email():
    if request.method == "POST":
        accept_header = request.headers.get("Accept")
        logger.debug(f"Accept header: {accept_header}")  # Added for debugging
        email_content = request.form.get("email_content", "").strip()
        selected_parser = request.form.get("parser_option", "rule_based")
        logger.debug(f"Received email_content: {email_content}")
        logger.debug(f"Selected parser: {selected_parser}")
        if email_content:
            parser = EmailParser()
            try:
                parsed_data = parser.parse_email(email_content, selected_parser)
                logger.info(f"Parsing successful using {selected_parser} parser.")

                # Convert parsed_data to CSV
                csv_buffer = generate_csv(parsed_data)
                csv_filename = "parsed_data.csv"

                # If the request expects JSON, return JSON with a link to download CSV
                if accept_header == "application/json":
                    # Encode CSV in base64 or provide a separate endpoint
                    # Here, we'll provide a download link with a unique identifier
                    # For simplicity, we'll generate CSV on the fly
                    # In production, consider storing the CSV temporarily
                    csv_bytes = csv_buffer.getvalue()
                    # Encode CSV as base64 to include in JSON (not ideal for large files)
                    import base64

                    csv_base64 = base64.b64encode(csv_bytes).decode("utf-8")
                    return (
                        jsonify(
                            {
                                "parsed_data": parsed_data,
                                "csv_data": csv_base64,
                                "csv_filename": csv_filename,
                            }
                        ),
                        200,
                    )
                else:
                    return render_template(
                        "index.html",
                        parsed_data=parsed_data,
                        selected_parser=selected_parser,
                    )
            except ValueError as ve:
                logger.error(f"Validation error during parsing: {str(ve)}")
                error_message = f"Validation Error: {str(ve)}"
                if accept_header == "application/json":
                    return jsonify({"error_message": error_message}), 400
                else:
                    return render_template(
                        "index.html",
                        error_message=error_message,
                        selected_parser=selected_parser,
                    )
            except Exception as e:
                logger.error(f"An unexpected error occurred during parsing: {str(e)}")
                error_message = f"An unexpected error occurred: {str(e)}"
                if accept_header == "application/json":
                    return jsonify({"error_message": error_message}), 500
                else:
                    return render_template(
                        "index.html",
                        error_message=error_message,
                        selected_parser=selected_parser,
                    )
        else:
            error_message = "Please enter email content to parse."
            if accept_header == "application/json":
                return jsonify({"error_message": error_message}), 400
            else:
                return render_template(
                    "index.html",
                    error_message=error_message,
                    selected_parser=selected_parser,
                )
    else:
        return render_template("index.html")


def generate_csv(parsed_data):
    """
    Generate a CSV file from parsed_data based on QUICKBASE_SCHEMA.
    """
    data_flat = flatten_parsed_data(parsed_data)
    # Map the parsed data to QuickBase field IDs
    csv_data = {}
    for section, fields in QUICKBASE_SCHEMA.items():
        for field_name, field_id in fields.items():
            key = f"{section}.{field_name}"
            value = data_flat.get(key, "N/A")
            csv_data[field_id] = value

    # Create a DataFrame
    df = pd.DataFrame([csv_data])
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return csv_buffer


def flatten_parsed_data(parsed_data, parent_key="", sep="."):
    """
    Flatten nested dictionaries.
    """
    items = {}
    for k, v in parsed_data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_parsed_data(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


@app.route("/download_csv", methods=["POST"])
def download_csv():
    """
    Endpoint to download CSV from base64 encoded data.
    Expects JSON with 'csv_data' and 'csv_filename'.
    """
    data = request.get_json()
    csv_base64 = data.get("csv_data")
    csv_filename = data.get("csv_filename", "parsed_data.csv")
    if not csv_base64:
        return jsonify({"error_message": "No CSV data provided."}), 400
    try:
        csv_bytes = base64.b64decode(csv_base64)
        return send_file(
            io.BytesIO(csv_bytes),
            mimetype="text/csv",
            as_attachment=True,
            attachment_filename=csv_filename,
        )
    except Exception as e:
        logger.error(f"Error decoding CSV data: {str(e)}")
        return jsonify({"error_message": "Failed to decode CSV data."}), 500


if __name__ == "__main__":
    app.run(debug=True)
