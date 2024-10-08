# src/utils/quickbase_schema.py

# Mapping of parsed data keys to QuickBase field IDs
QUICKBASE_SCHEMA = {
    "Requesting Party": {
        "Insurance Company": "field_1",
        "Handler": "field_2",
        "Carrier Claim Number": "field_3"
    },
    "Insured Information": {
        "Name": "field_4",
        "Contact #": "field_5",
        "Loss Address": "field_6",
        "Public Adjuster": "field_7",
        "Owner or Tenant": "field_8"
    },
    "Adjuster Information": {
        "Adjuster Name": "field_9",
        "Adjuster Phone Number": "field_10",
        "Adjuster Email": "field_11",
        "Job Title": "field_12",
        "Address": "field_13",
        "Policy #": "field_14"
    },
    "Assignment Information": {
        "Date of Loss/Occurrence": "field_15",
        "Cause of loss": "field_16",
        "Facts of Loss": "field_17",
        "Loss Description": "field_18",
        "Residence Occupied During Loss": "field_19",
        "Was Someone Home at Time of Damage": "field_20",
        "Repair or Mitigation Progress": "field_21",
        "Type": "field_22",
        "Inspection type": "field_23",
        "Assignment Type": "field_24",
        "Additional details/Special Instructions": "field_25",
        "Attachment(s)": "field_26"
    }
}
