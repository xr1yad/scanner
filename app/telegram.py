import os
import aiohttp

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT  = os.getenv("TELEGRAM_CHAT_ID", "")

async def send_telegram(text: str):
    if not TG_TOKEN or not TG_CHAT:
        print("Telegram not configured.")
        return

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT, "text": text, "disable_web_page_preview": True}

    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=20)) as r:
            if r.status >= 400:
                body = await r.text()
                raise RuntimeError(f"Telegram error {r.status}: {body}")
