import os
from fastapi import FastAPI, Request
from app.handlers.webhook_handler import handle_fireflies_webhook
from app.config import Config
from app.logger import get_logger

log = get_logger("main")

app = FastAPI()


@app.on_event("startup")
async def startup():
    mode = "DEVELOPMENT" if Config.DEVELOPMENT_MODE else "PRODUCTION"
    chroma_path = os.path.abspath("chroma_db")

    log.info("=" * 55)
    log.info("  Fireflies AI Meeting Intelligence — Starting up")
    log.info("=" * 55)
    log.info(f"  Mode          : {mode}")
    log.info(f"  API key set   : {'YES' if Config.API_KEY else 'NO  ← set FIREFLIES_API_KEY in .env'}")
    log.info(f"  ChromaDB path : {chroma_path}")
    log.info(f"  Endpoint      : POST /webhook/fireflies")
    log.info("=" * 55)

    if Config.DEVELOPMENT_MODE:
        log.warning("DEVELOPMENT MODE ON — using hardcoded transcript, no real API calls")


@app.post("/webhook/fireflies")
async def fireflies_webhook(request: Request):
    log.info("─" * 55)
    log.info("POST /webhook/fireflies — request received")
    payload = await request.json()
    log.info(f"Payload keys: {list(payload.keys())}")

    await handle_fireflies_webhook(payload)

    return {"status": "ok"}
