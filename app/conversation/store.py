from app.database import get_database
from datetime import datetime

async def save_answer(call_id: str, key: str, value: str, phone: str = None):
    db = get_database()
    if db is None:
        print("⚠️ Database not connected!")
        return

    collection = db["calls"]

    update_data = {
        f"answers.{key}": value,
        "updated_at": datetime.utcnow()
    }
    
    if phone:
        update_data["phone"] = phone

    # Upsert: Create if new, update if exists
    await collection.update_one(
        {"call_sid": call_id},
        {"$set": update_data},
        upsert=True
    )