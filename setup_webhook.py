import asyncio
import os

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WORKER_URL = os.getenv("WORKER_URL", "").rstrip("/")
WORKER_API_SECRET = os.getenv("WORKER_API_SECRET")
TELEGRAM_WEBHOOK_PATH = os.getenv("TELEGRAM_WEBHOOK_PATH")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

required = {
    "BOT_TOKEN": BOT_TOKEN,
    "WORKER_URL": WORKER_URL,
    "WORKER_API_SECRET": WORKER_API_SECRET,
    "TELEGRAM_WEBHOOK_PATH": TELEGRAM_WEBHOOK_PATH,
    "TELEGRAM_WEBHOOK_SECRET": TELEGRAM_WEBHOOK_SECRET,
}
missing = [name for name, value in required.items() if not value]
if missing:
    raise ValueError(f"Не заданы переменные окружения: {', '.join(missing)}")


async def main():
    api_base = f"{WORKER_URL}/api/{WORKER_API_SECRET}"
    webhook_url = f"{WORKER_URL}/telegram-webhook/{TELEGRAM_WEBHOOK_PATH}"
    session = AiohttpSession(api=TelegramAPIServer.from_base(api_base))

    async with Bot(token=BOT_TOKEN, session=session) as bot:
        await bot.set_webhook(
            url=webhook_url,
            secret_token=TELEGRAM_WEBHOOK_SECRET,
        )
        print("Webhook зарегистрирован:", webhook_url)


if __name__ == "__main__":
    asyncio.run(main())
