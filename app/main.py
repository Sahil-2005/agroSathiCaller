from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles  # 👈 Import this
from app.routes import voice, call
from app.database import connect_to_mongo, close_mongo_connection

app = FastAPI()

# Database events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# 👈 MOUNT THE STATIC FOLDER
# This makes http://your-url/static/q1.mp3 accessible
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(voice.router, prefix="/voice")
app.include_router(call.router)