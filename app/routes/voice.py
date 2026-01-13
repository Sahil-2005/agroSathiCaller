import os
import json
from fastapi import APIRouter, Request, Response, Depends
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.conversation.store import save_answer
from app.security import validate_twilio_request

router = APIRouter()

BASE_URL = os.getenv("BASE_URL")

# 1. LOAD SCRIPT DYNAMICALLY
def load_script():
    with open("app/script.json", "r", encoding="utf-8") as f:
        return json.load(f)

script_data = load_script()

# Filter out only the actual questions for the flow logic
QUESTIONS = [item for item in script_data if item.get("is_question") is True]

@router.post("/start", dependencies=[Depends(validate_twilio_request)])
async def start_call():
    vr = VoiceResponse()
    
    # Play the intro audio defined in JSON with key "intro"
    vr.play(f"{BASE_URL}/static/intro.mp3")

    # Initial gather to start the flow
    gather = Gather(
        input="dtmf",
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

    # --- HANDLE START (Intro) ---
    if step == -1:
        # Start the first question (index 0)
        return await ask_question(vr, 0, 0)

    # --- CAPTURE ANSWER ---
    user_input = speech or digits or ""

    # Validation: Empty Input
    if not user_input or len(user_input.strip()) < 1:
        if retry >= 2:
            vr.play(f"{BASE_URL}/static/outro.mp3")
            vr.hangup()
            return Response(str(vr), media_type="application/xml")

        vr.play(f"{BASE_URL}/static/error.mp3")
        return await ask_question(vr, step, retry + 1)

    # ✅ Save valid answer dynamically
    # We look up the key based on the current step index in our QUESTIONS list
    if 0 <= step < len(QUESTIONS):
        current_q = QUESTIONS[step]
        db_key = current_q["key"]  # e.g., "crop", "variety"
        await save_answer(call_id, db_key, user_input, phone=user_phone)

    # --- MOVE TO NEXT STEP ---
    next_step = step + 1

    # Check if we have more questions
    if next_step >= len(QUESTIONS):
        vr.play(f"{BASE_URL}/static/outro.mp3")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    # Ask next question
    return await ask_question(vr, next_step, 0)


async def ask_question(vr, step_index, retry):
    """
    Dynamically looks up the question audio and hints from the JSON list.
    """
    if step_index >= len(QUESTIONS):
        return
    
    question_data = QUESTIONS[step_index]
    key = question_data["key"]
    
    # Audio filename matches the key (e.g., "crop.mp3")
    audio_url = f"{BASE_URL}/static/{key}.mp3"
    
    # Get hints from JSON, default to empty string
    hint_text = question_data.get("hints", "")

    gather = Gather(
        input="speech",
        action=f"/voice/answer?step={step_index}&retry={retry}",
        language="hi-IN",
        timeout=4,
        speechTimeout="auto",
        profanityFilter=False,
        hints=hint_text,      
        enhanced=True,        
        speechModel="phone_call"
    )
    
    gather.play(audio_url)
    vr.append(gather)
    
    return Response(str(vr), media_type="application/xml")