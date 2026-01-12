import os
from fastapi import APIRouter, Request, Response, Depends
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.conversation.store import save_answer
from app.security import validate_twilio_request

router = APIRouter()

BASE_URL = os.getenv("BASE_URL") # Ensure this is set in .env

# Map steps to audio filenames
AUDIO_MAP = {
    -1: "intro.mp3",
    0: "q1.mp3", # Crop
    1: "q2.mp3", # Variety
    2: "q3.mp3", # Quantity
    3: "q4.mp3", # Sown Date
}

# Hints to help Twilio understand Hindi better
HINTS = {
    0: "गेहूँ, चावल, मक्का, बाजरा, सोयाबीन, आलू, प्याज़, टमाटर",
    1: "लोकवन, शरबती, बासमती, सोना, हाइब्रिड, देसी",
    2: "एक क्विंटल, दस किलो, पचास मन, पांच टन",
}

@router.post("/start", dependencies=[Depends(validate_twilio_request)])
async def start_call():
    vr = VoiceResponse()
    
    vr.play(f"{BASE_URL}/static/intro.mp3")

    gather = Gather(
        input="dtmf",
        # 🔴 WAS: action="/voice/answer?step=0&retry=0" (This caused the bug)
        # 🟢 CHANGE TO:
        action="/voice/answer?step=-1&retry=0", 
        timeout=4,
        numDigits=1
    )
    vr.append(gather)

    return Response(str(vr), media_type="application/xml")


@router.post("/answer", dependencies=[Depends(validate_twilio_request)])
async def handle_answer(request: Request, step: int, retry: int = 0):
    form = await request.form()
    speech = form.get("SpeechResult")
    digits = form.get("Digits")
    call_id = form.get("CallSid")
    user_phone = form.get("To") 

    vr = VoiceResponse()

    # Handle Step -1 (Intro / Trial)
    if step == -1:
        # User pressed a button to start, now ask Q1
        return await ask_question(vr, 0, 0)

    user_input = speech or digits or ""

    # VALIDATION: Check for empty input
    if not user_input or len(user_input.strip()) < 1:
        if retry >= 2:
            vr.play(f"{BASE_URL}/static/outro.mp3")
            vr.hangup()
            return Response(str(vr), media_type="application/xml")

        # Play error audio
        vr.play(f"{BASE_URL}/static/error.mp3")
        
        # Retry the same question
        return await ask_question(vr, step, retry + 1)

    # ✅ Save valid answer
    # Note: You might want to define keys list somewhere common
    keys = ["crop", "variety", "quantity", "sown_date"]
    if step < len(keys):
        await save_answer(call_id, keys[step], user_input, phone=user_phone)

    next_step = step + 1

    # Check if finished
    if next_step >= len(keys):
        vr.play(f"{BASE_URL}/static/outro.mp3")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    # Ask next question
    return await ask_question(vr, next_step, 0)


async def ask_question(vr, step, retry):
    """Helper to create the Gather verb with correct audio"""
    
    filename = AUDIO_MAP.get(step, "error.mp3")
    audio_url = f"{BASE_URL}/static/{filename}"
    
    # Get specific hints for this question to improve accuracy
    hint_text = HINTS.get(step, "")

    gather = Gather(
        input="speech",
        action=f"/voice/answer?step={step}&retry={retry}",
        language="hi-IN",
        timeout=4,
        speechTimeout="auto",
        profanityFilter=False,
        hints=hint_text,      # 👈 Critical for accuracy
        enhanced=True,        # 👈 Uses better AI model (small cost increase)
        speechModel="phone_call"
    )
    
    # Play audio INSIDE gather so input works while speaking (optional)
    # Or play before:
    gather.play(audio_url)
    
    vr.append(gather)
    return Response(str(vr), media_type="application/xml")