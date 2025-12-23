BOT_TOKEN = "8203892263:AAEfRfXVIFVQU8xKzZ_r1A1F2z9Bq3JlMkA"
ADMIN_ID = 1400836022  # To get your ID: @userinfobot
UPI_ID = "adi.9258@ptaxis"  # Your payment UPI ID

# Customize plans as needed
PLANS = {
    "1_month": {
        "name": "1 Month Premium",
        "price": 299,  # Amount in INR
        "duration": 30,  # Days
        "description": "Access to all premium groups for 1 month"
    },

    "3_months": {
        "name": "3 Months Premium",
        "price": 799,
        "duration": 90,
        "description": "Access to all premium groups for 3 months"
    },
    "6_months": {
        "name": "6 Months Premium",
        "price": 1499,
        "duration": 180,
        "description": "Access to all premium groups for 6 months"
    }
}

# Bot Settings
LOGGING_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
CLEANUP_INTERVAL = 3600  # Seconds between cleanup tasks
PAYMENT_VERIFICATION_TIMEOUT = 1200  # 20 minutes in seconds