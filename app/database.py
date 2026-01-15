import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "agrosathi")

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    try:
        db.client = AsyncIOMotorClient(MONGO_URI)
        db.db = db.client[DB_NAME]
        print(f"✅ Connected to MongoDB Atlas: {DB_NAME}")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("❌ Disconnected from MongoDB")

def get_database():
    return db.db