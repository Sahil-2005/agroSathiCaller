import os
import asyncio
import edge_tts

# 🟢 We use "hi-IN-SwaraNeural" for a very natural female Hindi voice.
# Options: "hi-IN-SwaraNeural" (Female), "hi-IN-MadhurNeural" (Male)
VOICE = "hi-IN-SwaraNeural"

QUESTIONS = {
    "intro": "नमस्ते, मैं आपका एग्रोसाथी हूँ। जारी रखने के लिए कोई भी बटन दबाएँ।",
    "q1": "आप कौन सी फसल बेच रहे हैं?",
    "q2": "उस फसल की किस्म क्या है?",
    "q3": "आपने कितनी मात्रा काटी है?",
    "q4": "फसल कब बोई गई थी?",
    "error": "मुझे आपकी आवाज़ ठीक से सुनाई नहीं दी। कृपया दोबारा बताइए।",
    "outro": "धन्यवाद। आपकी जानकारी दर्ज कर ली गई है।"
}

output_dir = "app/static"
os.makedirs(output_dir, exist_ok=True)

async def generate_mp3s():
    print(f"🚀 Generating High-Quality Neural Audio using {VOICE}...")
    
    for key, text in QUESTIONS.items():
        print(f"Generating: {key}...")
        file_path = f"{output_dir}/{key}.mp3"
        
        try:
            # Generate using Edge TTS
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(file_path)
            print(f"✅ Saved {file_path}")
            
        except Exception as e:
            print(f"❌ Failed to generate {key}: {e}")

if __name__ == "__main__":
    asyncio.run(generate_mp3s())