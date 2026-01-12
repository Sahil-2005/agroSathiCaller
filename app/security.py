import os
from dotenv import load_dotenv  # 👈 Add this import

# 👈 Load the .env file immediately
load_dotenv()

from fastapi import Request, HTTPException, status
from twilio.request_validator import RequestValidator

TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
BASE_URL = os.getenv("BASE_URL")

# Check if token exists to prevent cryptic errors later
if not TWILIO_AUTH_TOKEN:
    raise ValueError("❌ TWILIO_AUTH_TOKEN is missing. Please check your .env file.")

validator = RequestValidator(TWILIO_AUTH_TOKEN)

async def validate_twilio_request(request: Request):
    """
    Validates that the incoming request is actually from Twilio.
    """
    # Bypass validation if in development mode (optional)
    if os.getenv("ENV") == "development":
        return True

    url = str(request.url)
    
    # Twilio sends form data as POST parameters
    form_data = await request.form()
    params = dict(form_data)
    
    # The X-Twilio-Signature header
    signature = request.headers.get("X-Twilio-Signature", "")

    # Validate
    if not validator.validate(url, params, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Request not verified as coming from Twilio"
        )