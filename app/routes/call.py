from fastapi import APIRouter
from app.twilio_client import make_call

router = APIRouter()

@router.post("/call")
def trigger_call(phone: str):
    sid = make_call(phone)
    return {"status": "calling", "sid": sid}
