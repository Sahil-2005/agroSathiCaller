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
        # action="/voice/answer?step=-1",  # 👈 IMPORTANT
        action="/voice/answer?step=0&retry=0",  # 👈 IMPORTANT
        language="hi-IN",
        timeout=3,              # Reduced from 5 - wait for input to start
        speechTimeout="auto",   # Auto-detect end of speech (faster)
        profanityFilter=False   # Skip filtering = faster response
    )

    gather.say(
        "जारी रखने के लिए कोई भी बटन दबाएँ।",
        language="hi-IN"
    )

    vr.append(gather)

    return Response(str(vr), media_type="application/xml")


@router.post("/answer")
# async def handle_answer(request: Request, step: int):
async def handle_answer(request: Request, step: int, retry: int = 0):
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
            timeout=3,              # Reduced - wait for speech to start
            speechTimeout="auto",   # Auto-detect end of speech
            profanityFilter=False,
            hints=QUESTIONS[0][0]   # Hint for better recognition
        )
        gather.say(QUESTIONS[0][1], language="hi-IN")
        vr.append(gather)

        return Response(str(vr), media_type="application/xml")

    # 🟢 Normal speech handling
    user_input = speech or digits or ""

    # if not user_input:
    #     gather = Gather(
    #         input="speech",
    #         action=f"/voice/answer?step={step}",
    #         language="hi-IN",
    #         timeout=5
    #     )
    #     gather.say("मुझे ठीक से सुनाई नहीं दिया। कृपया दोबारा बताएं।", language="hi-IN")
    #     vr.append(gather)

    #     return Response(str(vr), media_type="application/xml")

    # # ✅ Save valid answer
    # key, _ = QUESTIONS[step]
    # save_answer(call_id, key, user_input, from_number)

    # next_step = step + 1

    # if next_step >= len(QUESTIONS):
    #     vr.say("धन्यवाद। आपकी जानकारी दर्ज कर ली गई है।", language="hi-IN")
    #     vr.hangup()
    #     return Response(str(vr), media_type="application/xml")

    # gather = Gather(
    #     input="speech",
    #     action=f"/voice/answer?step={next_step}",
    #     language="hi-IN",
    #     timeout=5
    # )
    # gather.say(QUESTIONS[next_step][1], language="hi-IN")
    # vr.append(gather)

    # return Response(str(vr), media_type="application/xml")

# -------------------------
# SILENCE VALIDATION
# -------------------------
    if not user_input or len(user_input.strip()) < 2:
        if retry >= 2:
            vr.say(
                "मुझे आपकी आवाज़ समझ नहीं आ रही है। हम बाद में फिर कोशिश करेंगे। धन्यवाद।",
                language="hi-IN"
            )
            vr.hangup()
            return Response(str(vr), media_type="application/xml")

        gather = Gather(
            input="speech",
            action=f"/voice/answer?step={step}&retry={retry + 1}",
            language="hi-IN",
            timeout=5
        )
        gather.say(
            "मुझे आपकी आवाज़ ठीक से सुनाई नहीं दी। कृपया दोबारा बताइए।",
            language="hi-IN"
        )
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

    # Determine hint for next question based on expected answer type
    next_hint = QUESTIONS[next_step][0] if next_step < len(QUESTIONS) else ""

    gather = Gather(
        input="speech",
        action=f"/voice/answer?step={next_step}&retry=0",
        language="hi-IN",
        timeout=3,              # Reduced - faster response
        speechTimeout="auto",   # Auto-detect when speech ends
        profanityFilter=False,
        hints=next_hint         # Helps speech recognition
    )
    gather.say(QUESTIONS[next_step][1], language="hi-IN")
    vr.append(gather)

    return Response(str(vr), media_type="application/xml")
