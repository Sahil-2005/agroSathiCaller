import os
from dotenv import load_dotenv  # 👈 Import this
from motor.motor_asyncio import AsyncIOMotorClient

# 👈 Load env vars BEFORE reading them
load_dotenv()

# Now this will correctly get your Atlas URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "agrosathi")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    # This print was misleading before because Motor is lazy.
    # Now it will use the correct URI.
    db.client = AsyncIOMotorClient(MONGO_URI)
    db.db = db.client[DB_NAME]
    print(f"✅ Connecting to MongoDB at: {MONGO_URI.split('@')[-1]}") # Prints host (hides password)

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("❌ Disconnected from MongoDB")

def get_database():
    return db.db
