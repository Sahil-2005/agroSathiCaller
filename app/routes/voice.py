import os
import json
import glob
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.conversation.store import save_answer
from app.security import validate_twilio_request

router = APIRouter()
BASE_URL = os.getenv("BASE_URL")

# --- CACHE SCRIPTS IN MEMORY ---
# Structure: { "agrosathi": [list of steps], "survey": [...] }
SCRIPTS_CACHE = {}

def load_scripts():
    """Loads all scripts from app/scripts/ directory into memory"""
    files = glob.glob("app/scripts/*.json")
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                slug = data.get("slug")
                if slug:
                    # Determine questions (items where is_question is True)
                    questions = [item for item in data.get("flow", []) if item.get("is_question")]
                    # Store both the full flow and just the questions for easy access
                    SCRIPTS_CACHE[slug] = {
                        "full_flow": data.get("flow", []),
                        "questions": questions
                    }
                    print(f"✅ Loaded script: {slug}")
        except Exception as e:
            print(f"❌ Error loading {file}: {e}")

# Load on startup (or you can call this inside a startup event in main.py)
load_scripts() 

@router.post("/start", dependencies=[Depends(validate_twilio_request)])
async def start_call(request: Request):
    # Get the script slug from query params (default to agrosathi if missing)
    script_slug = request.query_params.get("script", "agrosathi")
    
    if script_slug not in SCRIPTS_CACHE:
         # Reload scripts if not found (in case a new file was added)
        load_scripts()
        if script_slug not in SCRIPTS_CACHE:
            vr = VoiceResponse()
            vr.say("System error. Script not found.")
            vr.hangup()
            return Response(str(vr), media_type="application/xml")

    vr = VoiceResponse()
    
    # Play Intro: Note the dynamic path /static/{script_slug}/intro.mp3
    vr.play(f"{BASE_URL}/static/{script_slug}/intro.mp3")

    # Start Flow
    # ⚠️ We must pass script={script_slug} to the next step
    gather = Gather(
        input="dtmf",
        action=f"/voice/answer?step=-1&retry=0&script={script_slug}", 
        timeout=4,
        numDigits=1
    )
    vr.append(gather)

    return Response(str(vr), media_type="application/xml")


@router.post("/answer", dependencies=[Depends(validate_twilio_request)])
async def handle_answer(request: Request, step: int, retry: int = 0, script: str = "agrosathi"):
    form = await request.form()
    speech = form.get("SpeechResult")
    digits = form.get("Digits")
    call_id = form.get("CallSid")
    user_phone = form.get("To")

    # Retrieve specific script data
    if script not in SCRIPTS_CACHE:
        load_scripts() # Try reload
    
    script_data = SCRIPTS_CACHE.get(script)
    if not script_data:
        return Response(str(VoiceResponse().hangup()), media_type="application/xml")

    QUESTIONS = script_data["questions"]
    
    vr = VoiceResponse()

    # --- HANDLE START ---
    if step == -1:
        return await ask_question(vr, 0, 0, script, QUESTIONS)

    # --- PROCESS INPUT ---
    user_input = speech or digits or ""

    if not user_input or len(user_input.strip()) < 1:
        if retry >= 2:
            vr.play(f"{BASE_URL}/static/{script}/outro.mp3")
            vr.hangup()
            return Response(str(vr), media_type="application/xml")

        vr.play(f"{BASE_URL}/static/{script}/error.mp3")
        return await ask_question(vr, step, retry + 1, script, QUESTIONS)

    # ✅ Save Answer (Include script name in DB to differentiate campaigns)
    if 0 <= step < len(QUESTIONS):
        current_q = QUESTIONS[step]
        db_key = f"{script}_{current_q['key']}" # e.g. "agrosathi_crop" or just "crop"
        
        # We save it with the specific key defined in JSON
        await save_answer(call_id, current_q['key'], user_input, phone=user_phone)

    # --- NEXT STEP ---
    next_step = step + 1
    if next_step >= len(QUESTIONS):
        vr.play(f"{BASE_URL}/static/{script}/outro.mp3")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    return await ask_question(vr, next_step, 0, script, QUESTIONS)


async def ask_question(vr, step_index, retry, script_slug, questions_list):
    """
    Asks question using audio from the specific script folder.
    """
    question_data = questions_list[step_index]
    key = question_data["key"]
    
    # 🟢 DYNAMIC AUDIO PATH
    audio_url = f"{BASE_URL}/static/{script_slug}/{key}.mp3"
    hint_text = question_data.get("hints", "")

    gather = Gather(
        input="speech",
        # ⚠️ Propagate the script slug in the action URL
        action=f"/voice/answer?step={step_index}&retry={retry}&script={script_slug}",
        language="hi-IN",
        timeout=4,
        hints=hint_text,      
        enhanced=True,        
        speechModel="phone_call"
    )
    
    gather.play(audio_url)
    vr.append(gather)
    return Response(str(vr), media_type="application/xml")