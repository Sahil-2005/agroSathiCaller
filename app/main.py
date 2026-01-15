from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.routes import voice, call
from app.database import connect_to_mongo, close_mongo_connection

# 🟢 LIFESPAN context manager (Modern FastAPI)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(lifespan=lifespan)

# Mount static folder for audio files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(voice.router, prefix="/voice")
app.include_router(call.router)