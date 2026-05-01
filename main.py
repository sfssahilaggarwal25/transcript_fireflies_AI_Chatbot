from fastapi import FastAPI, Request
from app.handlers.webhook_handler import handle_fireflies_webhook

app = FastAPI()

@app.post("/webhook/fireflies")
async def fireflies_webhook(request: Request):
    payload = await request.json()

    # delegate to service layer
    await handle_fireflies_webhook(payload)

    return {"status": "ok"}