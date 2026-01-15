import os
import json
import glob
from fastapi import APIRouter, Request, Response, Depends
from twilio.twiml.voice_response import VoiceResponse, Gather
from app.conversation.store import save_answer
from app.security import validate_twilio_request

router = APIRouter()
BASE_URL = os.getenv("BASE_URL")

# --- CACHE SCRIPTS IN MEMORY ---
SCRIPTS_CACHE = {}

def load_scripts():
    files = glob.glob("app/scripts/*.json")
    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                slug = data.get("slug")
                if slug:
                    questions = [item for item in data.get("flow", []) if item.get("is_question")]
                    SCRIPTS_CACHE[slug] = {
                        "full_flow": data.get("flow", []),
                        "questions": questions
                    }
                    print(f"✅ Loaded script: {slug}")
        except Exception as e:
            print(f"❌ Error loading {file}: {e}")

load_scripts() 

@router.post("/start", dependencies=[Depends(validate_twilio_request)])
async def start_call(request: Request):
    script_slug = request.query_params.get("script", "agrosathi")
    
    if script_slug not in SCRIPTS_CACHE:
        load_scripts()
        
    if script_slug not in SCRIPTS_CACHE:
        vr = VoiceResponse()
        vr.say("System error. Script not found.")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    vr = VoiceResponse()
    
    # Play Intro
    vr.play(f"{BASE_URL}/static/{script_slug}/intro.mp3")

    # Wait for button press to start
    gather = Gather(
        input="dtmf",
        action=f"/voice/answer?step=-1&retry=0&script={script_slug}", 
        timeout=10, 
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

    if script not in SCRIPTS_CACHE:
        load_scripts()
    
    script_data = SCRIPTS_CACHE.get(script)
    if not script_data:
        return Response(str(VoiceResponse().hangup()), media_type="application/xml")

    QUESTIONS = script_data["questions"]
    vr = VoiceResponse()

    # --- HANDLE START ---
    if step == -1:
        # User pressed start button. Move immediately to Q1 (Index 0)
        return await ask_question(vr, 0, 0, script, QUESTIONS)

    # --- VALIDATE INPUT ---
    user_input = speech or digits or ""

    if not user_input or len(user_input.strip()) < 1:
        if retry >= 2:
            # Failed 3 times, play outro and hangup
            vr.play(f"{BASE_URL}/static/{script}/outro.mp3")
            vr.hangup()
            return Response(str(vr), media_type="application/xml")

        # Play error and ask SAME question again
        vr.play(f"{BASE_URL}/static/{script}/error.mp3")
        return await ask_question(vr, step, retry + 1, script, QUESTIONS)

    # ✅ SAVE ANSWER TO DB
    if 0 <= step < len(QUESTIONS):
        current_q = QUESTIONS[step]
        print(f"✅ Saving: {current_q['key']} = {user_input}")
        # Note: We append the script name to the key if needed, or keep it simple
        await save_answer(call_id, current_q['key'], user_input, phone=user_phone)

    # --- NEXT STEP ---
    next_step = step + 1

    if next_step >= len(QUESTIONS):
        # END OF CONVERSATION
        vr.play(f"{BASE_URL}/static/{script}/outro.mp3")
        vr.hangup()
        return Response(str(vr), media_type="application/xml")

    return await ask_question(vr, next_step, 0, script, QUESTIONS)


async def ask_question(vr, step_index, retry, script_slug, questions_list):
    question_data = questions_list[step_index]
    key = question_data["key"]
    
    audio_url = f"{BASE_URL}/static/{script_slug}/{key}.mp3"
    hint_text = question_data.get("hints", "")

    # 🟢 FIX: Play audio BEFORE gather. 
    # This prevents the "skip" caused by immediate noise detection.
    vr.play(audio_url)

    gather = Gather(
        input="dtmf speech",
        action=f"/voice/answer?step={step_index}&retry={retry}&script={script_slug}",
        language="hi-IN",
        timeout=4,
        hints=hint_text,      
        enhanced=True,        
        speechModel="phone_call"
    )
    
    vr.append(gather)
    return Response(str(vr), media_type="application/xml")