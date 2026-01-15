import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

def make_call(to_number: str, script_slug: str):
    """
    Triggers a call for a specific script slug.
    """
    # We append ?script={script_slug} to the webhook URL
    webhook_url = f"{os.getenv('BASE_URL')}/voice/start?script={script_slug}"
    
    print(f"📞 Calling {to_number} using script: {script_slug}")
    
    call = client.calls.create(
        to=to_number,
        from_=os.getenv("TWILIO_PHONE"),
        url=webhook_url
    )
    return call.sid