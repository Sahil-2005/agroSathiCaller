import os
import json
import asyncio
import edge_tts

# Load script from JSON
with open("app/script.json", "r", encoding="utf-8") as f:
    SCRIPT_DATA = json.load(f)

VOICE = "hi-IN-SwaraNeural"
output_dir = "app/static"
os.makedirs(output_dir, exist_ok=True)

async def generate_mp3s():
    print(f"🚀 Generating Audio for {len(SCRIPT_DATA)} items...")
    
    for item in SCRIPT_DATA:
        key = item["key"]
        text = item["text"]
        file_path = f"{output_dir}/{key}.mp3"
        
        print(f"Generating: {key}...")
        try:
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(file_path)
            print(f"✅ Saved {file_path}")
        except Exception as e:
            print(f"❌ Failed to generate {key}: {e}")

if __name__ == "__main__":
    asyncio.run(generate_mp3s())
