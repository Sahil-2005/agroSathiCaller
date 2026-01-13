from app.database import get_database
from datetime import datetime

async def save_answer(call_id: str, key: str, value: str, phone: str = None):
    db = get_database()
    collection = db["calls"]

    update_data = {
        f"answers.{key}": value,
        "updated_at": datetime.utcnow()
    }
    
    # If phone is provided, set it (useful for the first insert)
    if phone:
        update_data["phone"] = phone

    # Upsert: Update if exists, Insert if not
    await collection.update_one(
        {"call_sid": call_id},
        {"$set": update_data},
        upsert=True
    )