from fastapi import APIRouter, Request
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.conversation.states import QUESTIONS
from app.conversation.store import save_answer

router = APIRouter()

@router.post("/start")
async def start_call():
    vr = VoiceResponse()
    vr.say("नमस्ते, मैं आपका एग्रोसाथी हूँ।", language="hi-IN")

    gather = Gather(
        input="speech dtmf",
        action="/voice/answer?step=0",
        language="hi-IN"
    )
    gather.say("आप कौन सी फसल बेच रहे हैं?", language="hi-IN")
    vr.append(gather)
    return str(vr)


@router.post("/answer")
async def handle_answer(request: Request, step: int):
    form = await request.form()
    speech = form.get("SpeechResult", "")
    digits = form.get("Digits")
    call_id = form.get("CallSid")

    key, _ = QUESTIONS[step]
    save_answer(call_id, key, speech)

    next_step = step + 1
    vr = VoiceResponse()

    if next_step >= len(QUESTIONS):
        vr.say("धन्यवाद। आपकी जानकारी दर्ज कर ली गई है।", language="hi-IN")
        vr.hangup()
        return str(vr)

    gather = Gather(
        input="speech dtmf",
        action=f"/voice/answer?step={next_step}",
        language="hi-IN"
    )
    gather.say(QUESTIONS[next_step][1], language="hi-IN")
    vr.append(gather)

    return str(vr)
