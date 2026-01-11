from fastapi import APIRouter, Request, Response, Depends, Form
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.conversation.states import QUESTIONS
from app.conversation.store import save_answer
from app.security import validate_twilio_request

router = APIRouter()

@router.post("/start", dependencies=[Depends(validate_twilio_request)])
async def start_call():
    vr = VoiceResponse()
    vr.say("नमस्ते, मैं आपका एग्रोसाथी हूँ।", language="hi-IN")

    gather = Gather(
        input="speech dtmf",
        action="/voice/answer?step=0&retry=0",
        language="hi-IN",
        timeout=3,
        speechTimeout="auto",
        profanityFilter=False
    )
    gather.say("जारी रखने के लिए कोई भी बटन दबाएँ।", language="hi-IN")
    vr.append(gather)

    return Response(str(vr), media_type="application/xml")


@router.post("/answer", dependencies=[Depends(validate_twilio_request)])
async def handle_answer(request: Request, step: int, retry: int = 0):
    form = await request.form()

    speech = form.get("SpeechResult")
    digits = form.get("Digits")
    call_id = form.get("CallSid")
    from_number = form.get("To")  # For outbound calls, 'To' is the user, 'From' is us.
    # Note: If this is an INBOUND call to the server, 'From' is the user.
    # Adjust logic based on flow:
    # If YOU call THEM (Outbound): User is 'To'
    # If THEY call YOU (Inbound): User is 'From'
    # Assuming outbound based on 'trigger_call.py':
    user_phone = form.get("To") 

    vr = VoiceResponse()

    # 🟡 STEP -1: Trial keypress (Do not save)
    if step == -1:
        gather = Gather(
            input="speech",
            action="/voice/answer?step=0",
            language="hi-IN",
            timeout=3,
            hints=QUESTIONS[0][0]
        )
        gather.say(QUESTIONS[0][1], language="hi-IN")
        vr.append(gather)
        return Response(str(vr), media_type="application/xml")

    user_input = speech or digits or ""

    # 🔴 SILENCE / NO INPUT VALIDATION
    if not user_input or len(user_input.strip()) < 1:
        if retry >= 2:
            vr.say("मुझे आपकी आवाज़ समझ नहीं आ रही है। हम बाद में फिर कोशिश करेंगे। धन्यवाद।", language="hi-IN")
            vr.hangup()
            return Response(str(vr), media_type="application/xml")

        gather = Gather(
            input="speech",
            action=f"/voice/answer?step={step}&retry={retry + 1}",
            language="hi-IN",
            timeout=5
        )
        gather.say("मुझे आपकी आवाज़ ठीक से सुनाई नहीं दी। कृपया दोबारा बताइए।", language="hi-IN")
        vr.append(gather)
        return Response(str(vr), media_type="application/xml")

    # ✅ SAVE VALID ANSWER (Async)
    key, _ = QUESTIONS[step]
    
    # We pass user_phone only if we are at step 0 or if we want to ensure it's set
    await save_answer(call_id, key, user_input, phone=user_phone)

    next_step = step + 1

    # 🏁 FINISHED
    if next_step >= len(QUESTIONS):
        vr.say("धन्यवाद। आपकी जानकारी दर्ज कर ली गई है।", language="hi-IN")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    # 🟢 NEXT QUESTION
    next_hint = QUESTIONS[next_step][0]
    
    gather = Gather(
        input="speech",
        action=f"/voice/answer?step={next_step}&retry=0",
        language="hi-IN",
        timeout=3,
        speechTimeout="auto",
        profanityFilter=False,
        hints=next_hint
    )
    gather.say(QUESTIONS[next_step][1], language="hi-IN")
    vr.append(gather)

    return Response(str(vr), media_type="application/xml")