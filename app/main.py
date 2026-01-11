from fastapi import FastAPI
from app.routes import voice, call
from app.database import connect_to_mongo, close_mongo_connection

app = FastAPI()

# Database connection events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(voice.router, prefix="/voice")
app.include_router(call.router)