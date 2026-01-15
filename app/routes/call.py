from fastapi import APIRouter
from app.twilio_client import make_call

router = APIRouter()

@router.post("/call")
def trigger_call(phone: str, script: str = "agrosathi"):
    """
    Trigger a call. Default script is 'agrosathi'.
    """
    sid = make_call(phone, script)
    return {"status": "calling", "sid": sid, "script": script}