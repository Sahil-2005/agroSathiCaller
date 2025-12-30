# from fastapi import APIRouter, Request
# from twilio.twiml.voice_response import VoiceResponse, Gather
# from app.conversation.states import QUESTIONS
# from app.conversation.store import save_answer

# router = APIRouter()

# @router.post("/start")
# async def start_call():
#     vr = VoiceResponse()
#     vr.say("नमस्ते, मैं आपका एग्रोसाथी हूँ।", language="hi-IN")

#     gather = Gather(
#         input="speech dtmf",
#         action="/voice/answer?step=0",
#         language="hi-IN"
#     )
#     gather.say("आप कौन सी फसल बेच रहे हैं?", language="hi-IN")
#     vr.append(gather)
#     return str(vr)


# @router.post("/answer")
# async def handle_answer(request: Request, step: int):
#     form = await request.form()
#     speech = form.get("SpeechResult", "")
#     digits = form.get("Digits")
#     call_id = form.get("CallSid")

#     key, _ = QUESTIONS[step]
#     save_answer(call_id, key, speech)

#     next_step = step + 1
#     vr = VoiceResponse()

#     if next_step >= len(QUESTIONS):
#         vr.say("धन्यवाद। आपकी जानकारी दर्ज कर ली गई है।", language="hi-IN")
#         vr.hangup()
#         return str(vr)

#     gather = Gather(
#         input="speech dtmf",
#         action=f"/voice/answer?step={next_step}",
#         language="hi-IN"
#     )
#     gather.say(QUESTIONS[next_step][1], language="hi-IN")
#     vr.append(gather)

#     return str(vr)

from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.conversation.states import QUESTIONS
from app.conversation.store import save_answer

router = APIRouter()


@router.post("/start")
async def start_call():
    vr = VoiceResponse()

    vr.say(
        "नमस्ते, मैं आपका एग्रोसाथी हूँ।",
        language="hi-IN"
    )

    gather = Gather(
        input="speech dtmf",
        action="/voice/answer?step=-1",  # 👈 IMPORTANT
        language="hi-IN",
        timeout=5
    )

    gather.say(
        "जारी रखने के लिए कोई भी बटन दबाएँ।",
        language="hi-IN"
    )

    vr.append(gather)

    return Response(str(vr), media_type="application/xml")


@router.post("/answer")
async def handle_answer(request: Request, step: int):
    form = await request.form()

    speech = form.get("SpeechResult")
    digits = form.get("Digits")
    call_id = form.get("CallSid")
    from_number = form.get("To")   # +91XXXXXXXXXX


    vr = VoiceResponse()

    # 🟡 STEP -1 → Trial keypress, DO NOT save anything
    if step == -1:
        gather = Gather(
            input="speech",
            action="/voice/answer?step=0",
            language="hi-IN",
            timeout=5
        )
        gather.say(QUESTIONS[0][1], language="hi-IN")
        vr.append(gather)

        return Response(str(vr), media_type="application/xml")

    # 🟢 Normal speech handling
    user_input = speech or digits or ""

    if not user_input:
        gather = Gather(
            input="speech",
            action=f"/voice/answer?step={step}",
            language="hi-IN",
            timeout=5
        )
        gather.say("मुझे ठीक से सुनाई नहीं दिया। कृपया दोबारा बताएं।", language="hi-IN")
        vr.append(gather)

        return Response(str(vr), media_type="application/xml")

    # ✅ Save valid answer
    key, _ = QUESTIONS[step]
    save_answer(call_id, key, user_input, from_number)

    next_step = step + 1

    if next_step >= len(QUESTIONS):
        vr.say("धन्यवाद। आपकी जानकारी दर्ज कर ली गई है।", language="hi-IN")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    gather = Gather(
        input="speech",
        action=f"/voice/answer?step={next_step}",
        language="hi-IN",
        timeout=5
    )
    gather.say(QUESTIONS[next_step][1], language="hi-IN")
    vr.append(gather)

    return Response(str(vr), media_type="application/xml")
