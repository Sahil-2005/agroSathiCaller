# from twilio.rest import Client
# import os

# client = Client(
#     os.getenv("TWILIO_ACCOUNT_SID"),
#     os.getenv("TWILIO_AUTH_TOKEN")
# )

# def make_call(to_number: str):
#     call = client.calls.create(
#         to=to_number,
#         from_=os.getenv("TWILIO_PHONE"),
#         url=f"{os.getenv('BASE_URL')}/voice/start"
#     )
#     return call.sid

import os
from twilio.rest import Client
from dotenv import load_dotenv

# 🔑 THIS LINE LOADS .env FILE
load_dotenv()

client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

def make_call(to_number: str):
    call = client.calls.create(
        to=to_number,
        from_=os.getenv("TWILIO_PHONE"),
        url=f"{os.getenv('BASE_URL')}/voice/start"
    )
    return call.sid
