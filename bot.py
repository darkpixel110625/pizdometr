import asyncio
import random
import time
import os
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from flask import Flask
from threading import Thread

# Берем токен из скрытых настроек Render
TOKEN = os.environ.get("API_TOKEN")
DB_NAME = "pizdometr.db"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- Часть с базой данных ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                size INTEGER,
                last_time INTEGER
            )
        """)
        await db.commit()

# --- Часть с логикой бота ---
@dp.message(Command("pizda"))
async def cmd_pizda(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    now = int(time.time())

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT size, last_time FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()

        if row:
            size, last_time = row
            if now - last_time < 3600:
                wait = int((3600 - (now - last_time)) / 60)
                await message.answer(f"@{username}, куда так спешишь? Подожди еще {wait} мин. (Ты её так сотрешь, Алишер).")
                return

            growth = random.randint(1, 10)
            new_size = size + growth
            await db.execute("UPDATE users SET size = ?, last_time = ?, username = ? WHERE user_id = ?",
                             (new_size, now, username, user_id))
        else:
            growth = random.randint(1, 10)
            new_size = growth
            await db.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, username, new_size, now))

        await db.commit()
        await message.answer(f"@{username}, ваша пизда выросла на {growth} см. Теперь её размер составляет {new_size} см. Мрак какой-то...")

# --- Часть с веб-заглушкой ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Бот в сети, отвали, Render!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- Запуск ---
async def main():
    await init_db()
    # Запускаем Flask в отдельном потоке
    Thread(target=run_flask).start()
    print("Бот и заглушка запущены...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
