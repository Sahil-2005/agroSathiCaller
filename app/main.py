from fastapi import FastAPI
from app.routes.voice import router

app = FastAPI()
app.include_router(router, prefix="/voice")
