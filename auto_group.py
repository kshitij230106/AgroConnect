import pandas as pd

df = pd.read_excel("Request and Response of failures.xlsx")

categories = {
    "timeout_issue": [
        "timed out",
        "session timeout",
        "request expired"
    ],

    "otp_issue": [
        "otp",
        "invalid otp"
    ],

    "dealer_issue": [
        "dealer"
    ],

    "biometric_issue": [
        "biometric",
        "uid_authentication_failed",
        "fingerprint"
    ],

    "aadhaar_issue": [
        "aadhaar"
    ],

    "transaction_issue": [
        "transaction"
    ],

    "price_issue": [
        "mrp",
        "price"
    ],

    "stock_issue": [
        "stock",
        "qty"
    ],

    "device_issue": [
        "device"
    ],

    "qr_issue": [
        "qr"
    ],
    "validation_issue": [
    "invalid",
    "acknowledged",
    "attribute",
    "dd number",
    "request"
]

}

for desc in df["description"].dropna().unique():

    desc_lower = str(desc).lower()

    found = False

    for category, keywords in categories.items():

        if any(keyword in desc_lower for keyword in keywords):
            print(f"{category} -> {desc}")
            found = True
            break

    if not found:
        print(f"UNMAPPED -> {desc}")