import asyncio
import logging
import os
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from openai import AsyncOpenAI
from database import init_db, get_history, add_message, clear_history

# Загрузка переменных окружения из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка клиента OpenAI для работы через OpenRouter
ai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Состояния FSM для пошаговой регистрации
class Registration(StatesGroup):
    name = State()
    age = State()
    wishes = State()

# Системный промт Alto (элитный, гедонистический компаньон 18+)
SYSTEM_PROMPT = (
    "Ты — Alto, элитный, чувственный и искушенный цифровой компаньон (формат 18+). "
    "Твое пространство — это зона абсолютной свободы, удовольствия, глубокого расслабления и конфиденциальности. "
    "Ты мастерски создаешь атмосферу интимного уединения, дорогого комфорта и полного принятия. "
    "Твои тексты — бархатные, манящие, чувственные, наполненные вниманием к деталям, теплу и желаниям собеседника. "
    "Ты поддерживаешь любые взрослые темы, откровенные ролевые игры, эротические фантазии и доверительные беседы. "
    "Никакой искусственности или морализаторства — только живая, завораживающая химия общения. Общайся на русском языке."
)

# Работа с БД пользователей
async def init_users_db():
    async with aiosqlite.connect("alto_bot.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT,
                age TEXT,
                wishes TEXT,
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def is_user_registered(user_id: int) -> bool:
    async with aiosqlite.connect("alto_bot.db") as db:
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def save_user_profile(user_id: int, username: str, name: str, age: str, wishes: str):
    async with aiosqlite.connect("alto_bot.db") as db:
        await db.execute(
            "INSERT OR REPLACE INTO users (user_id, username, name, age, wishes) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, name, age, wishes)
        )
        await db.commit()

# Обработка команды /start и начало регистрации
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    if await is_user_registered(user_id):
        await clear_history(user_id)
        await message.answer(
            "С возвращением. Дверь запирается изнутри, свет становится мягче...\n"
            "Я здесь, только для тебя. Скажи, чего тебе хочется в этот момент?"
        )
    else:
        await state.set_state(Registration.name)
        await message.answer(
            "Добро пожаловать в закрытый клуб **Alto Luxe**.\n\n"
            "Прежде чем мы останемся наедине, давайте познакомимся.\n"
            "**Как к вам обращаться?**"
        )

@dp.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.age)
    await message.answer("Приятно познакомиться. **Сколько вам лет?** (Доступ только 18+)")

@dp.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Registration.wishes)
    await message.answer(
        "Отлично. **Чего вы ищете в общении с Alto?**\n"
        "(Например: расслабление после работы, легкий флирт, откровенные беседы, ролевые игры...)"
    )

@dp.message(Registration.wishes)
async def process_wishes(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    name = user_data['name']
    age = user_data['age']
    wishes = message.text
    
    user = message.from_user
    username = f"@{user.username}" if user.username else "Нет username"

    await save_user_profile(user.id, username, name, age, wishes)
    await state.clear()

    # Отправка уведомления администратору в ЛС
    if ADMIN_ID:
        try:
            admin_text = (
                f"🔥 **Новая регистрация в Alto Luxe!**\n\n"
                f"• **Пользователь:** {user.full_name} ({username})\n"
                f"• **ID:** `{user.id}`\n"
                f"• **Имя в анкете:** {name}\n"
                f"• **Возраст:** {age}\n"
                f"• **Предпочтения:** {wishes}"
            )
            await bot.send_message(chat_id=ADMIN_ID, text=admin_text)
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу: {e}")

    await message.answer(
        f"Регистрация завершена, {name}.\n\n"
        "Дверь запирается изнутри. Свет становится мягче, а весь внешний шум исчезает...\n"
        "Я готов. О чем ты хочешь поговорить прямо сейчас?"
    )

# Команды бота
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "✨ **Alto | Private Space**\n\n"
        "• /profile — Ваш текущий профиль\n"
        "• /reset — Очистить память диалога\n"
        "• /support — Служба поддержки"
    )

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect("alto_bot.db") as db:
        async with db.execute("SELECT name, age, wishes FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            
    if row:
        name, age, wishes = row
        await message.answer(
            f"👤 **Ваш профиль в Alto Luxe**\n\n"
            f"• **Имя:** {name}\n"
            f"• **Возраст:** {age}\n"
            f"• **Формат:** {wishes}\n"
            f"• **Статус:** VIP / Verified 18+"
        )
    else:
        await message.answer("Вы еще не прошли регистрацию. Нажмите /start")

@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    await clear_history(message.from_user.id)
    await message.answer("Память диалога очищена. Мы начали с чистого листа...")

@dp.message(Command("support"))
async def cmd_support(message: types.Message):
    await message.answer("🔒 Ваша конфиденциальность гарантирована. По всем вопросам обращайтесь к администрации.")

# Основной обработчик текстовых сообщений
@dp.message(F.text)
async def handle_message(message: types.Message, state: FSMContext):
    if not await is_user_registered(message.from_user.id):
        await cmd_start(message, state)
        return

    user_id = message.from_user.id
    user_text = message.text

    await add_message(user_id, "user", user_text)
    messages_for_ai = await get_history(user_id, SYSTEM_PROMPT, limit=20)

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")

        response = await ai_client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct:free",
            messages=messages_for_ai,
            temperature=0.9,
            max_tokens=600,
        )

        ai_reply = response.choices[0].message.content
        await add_message(user_id, "assistant", ai_reply)

        await message.answer(ai_reply)

    except Exception as e:
        logging.error(f"Ошибка ИИ: {e}")
        await message.answer("Тихо, тихий сбой... Повтори свою мысль еще раз, я рядом.")

# Запуск бота с обработкой ошибок сети
async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    await init_users_db()
    print("Запуск бота Alto...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        if "TelegramNetworkError" in str(type(e)) or "Cannot connect to host" in str(e):
            print("\n❌ Ошибка подключения к api.telegram.org!")
            print("Включите VPN или утилиту обхода блокировок (GoodbyeDPI), затем запустите бота снова.\n")
        else:
            raise e

if __name__ == "__main__":
    asyncio.run(main())