# src/utils/validation.py

import jsonschema

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
        jsonschema.validate(instance=parsed_data, schema=assignment_schema)
        return True, ""
    except jsonschema.exceptions.ValidationError as err:
        return False, err.message
