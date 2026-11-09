import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from openai import OpenAI

# Загружаем переменные окружения из файла .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")

# Проверка наличия токена
if not BOT_TOKEN:
    raise ValueError("Не найден BOT_TOKEN в переменных окружения!")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка клиента OpenRouter (используем базовый URL OpenRouter)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENAI_API_KEY,
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  """Обработчик команды /start"""
  await message.answer(
      "Привет! Я твой бот на базе Llama 3.3 (OpenRouter). Напиши мне что-нибудь!"
  )


@dp.message()
async def handle_message(message: types.Message):
  """Обработка текстовых сообщений и отправка запроса в OpenRouter"""
  user_text = message.text

  try:
    # Отправляем запрос к модели через OpenRouter API
    response = client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct",
        messages=[{
            "role": "system",
            "content": "Ты полезный и вежливый AI-ассистент.",
        }, {"role": "user", "content": user_text}],
    )

    answer = response.choices[0].message.content
    await message.answer(answer)

  except Exception as e:
    logging.__(f"Ошибка при обращении к OpenRouter: {e}")
    await message.answer("Произошла ошибка при обращении к нейросети.")


async def main():
  print("Запуск бота Alto...")
  await dp.start_polling(bot)


if __name__ == "__main__":
  import asyncio

  asyncio.run(main())