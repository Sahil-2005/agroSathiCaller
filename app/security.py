import os
from fastapi import Request, HTTPException, status
from twilio.request_validator import RequestValidator

TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # Must be your public HTTPS url (e.g., ngrok or domain)

validator = RequestValidator(TWILIO_AUTH_TOKEN)

async def validate_twilio_request(request: Request):
    """
    Validates that the incoming request is actually from Twilio.
    """
    # If running locally without a public URL configured, you might want to skip this
    # OR ensure BASE_URL matches exactly what Twilio sees.
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