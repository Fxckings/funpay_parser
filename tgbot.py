from aiogram import F, Router, types
from parser_fp import Parser
from datetime import datetime, timedelta
import re
from loguru import logger
import json
from enums.enums import Data
import asyncio
import aiofiles

logger.add("tgbot.log", format="{time} | {level} | {message}", level="INFO")

router = Router()
user_data_cache = {}
user_data_cache_lock = asyncio.Lock()
CACHE_DURATION = timedelta(minutes=10)

async def load_db():
    try:
        async with aiofiles.open('database/users.json', 'r', encoding='utf-8') as f:
            content = await f.read()
        return json.loads(content)
    except FileNotFoundError:
        return []

@router.message(F.text.startswith("/start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот для FunPay.")

async def get_cached_user_data(user_id, parse_usr_data_func):
    async with user_data_cache_lock:
        if user_id in user_data_cache:
            cached_entry = user_data_cache[user_id]
            timestamp, data = cached_entry["timestamp"], cached_entry["data"]

            if datetime.now() - timestamp < CACHE_DURATION:
                return data

        # Загружаем только минимальную информацию для кэширования
        user_data = await parse_usr_data_func(user_id)
        user_data_cache[user_id] = {
            "timestamp": datetime.now(),
            "data": user_data
        }

        return user_data

@router.inline_query()
async def inline_search(inline_query: types.InlineQuery):
    users = await load_db()
    user_id = None
    message = inline_query.query.lower()

    if len(message.split('/')) > 1 and message.split('/')[-2].isdigit():
        user_id = message.split('/')[-2]
    else:
        for user in users:
            if user["username"].lower() == message.split('/')[-1].lower():
                user_id = re.search(r'\d+', user["link"]).group(0)
                break

    prsr = Parser()
    
    # Получаем минимальные данные для быстрого ответа
    user_data = await get_cached_user_data(user_id, prsr.parse_usr_data)
    
    if user_data:
        if user_data.avatar_link == "/img/layout/avatar.png":
            user_data.avatar_link = None
        if user_data.estimation == "?":
            user_data.estimation = "Еще не определено (?)"

        status = user_data.status.replace(' ', '').replace('\n', '')

        sanclist_text = "\n".join(f"{name} - {rating}" for rating, name in user_data.sanclist)
        answers = [
            types.InlineQueryResultArticle(
                id='1',
                title=f"🐒 Полная информация: {user_data.username}",
                description=f"⭐ Отзывов: {user_data.reviews_count}\n⭐ Оценка: {user_data.estimation}",
                thumbnail_url=user_data.avatar_link if user_data.avatar_link else "https://funpay.com/img/layout/avatar.png",
                input_message_content=types.InputTextMessageContent(
                    message_text=f"""
💎 <b>Полная</b> информация о пользователе <b>{user_data.username}</b>

⭐ Количество отзывов: <b>{user_data.reviews_count}</b>
⭐ Рейтинг: <b>{user_data.estimation}</b>
📅 Дата регистрации: <b>{user_data.date_reg}</b>
⚙️ Количество предложений (категорий): <b>{user_data.count_offers}</b>
⚙️ Количество лотов: <b>{user_data.lots}</b>
📐 Средняя цена: <b>{user_data.average_price}</b> (основано на {user_data.lots} лотах)
{"🟢" if status == 'Онлайн' else "🔴"} Статус: <b>{status}</b>
🧑‍💻 Ссылка на профиль: <b>{user_data.userlink}</b>
🎰 Самый дорогой лот: <b>{user_data.max_price}₽ - {user_data.link_to_max_price}</b>
🐤 Популярные игры в отзывах:
<b>{user_data.games_in_reviews}</b>
🐒 Рублевки мансори: <b>{"Да🐷" if user_data.havemansory else "Нет🤯"}</b>
🪙 Лотов с автовыдачей: <b>{user_data.autolots}</b>

{f"🌶️ Ограничения рейтинга:\n<b>{sanclist_text}</b>" if user_data.sanclist else f"🌶️ Не нашел лоты с ограничением"}
✅ Проверка на основе 30 катогорий
""", parse_mode="HTML", disable_web_page_preview=False
                )
            ),
            types.InlineQueryResultArticle(
                id='2',
                title=f"👀 Краткая информация: {user_data.username}",
                description=f"⭐ Отзывов: {user_data.reviews_count}\n⭐ Оценка: {user_data.estimation}",
                thumbnail_url=user_data.avatar_link if user_data.avatar_link else "https://funpay.com/img/layout/avatar.png",
                input_message_content=types.InputTextMessageContent(
                    message_text=f"""
💎 <b>Краткая</b> информация о пользователе <b>{user_data.username}</b>

⭐ Количество отзывов: <b>{user_data.reviews_count}</b>
⭐ Рейтинг: <b>{user_data.estimation}</b>
📅 Дата регистрации: <b>{user_data.date_reg}</b>
⚙️ Количество предложений (категорий): <b>{user_data.count_offers}</b>
⚙️ Количество лотов: <b>{user_data.lots}</b>
🎃 Аватарка: <b>{user_data.avatar_link if user_data.avatar_link else "https://funpay.com/img/layout/avatar.png"}</b>
                    """, parse_mode="HTML", disable_web_page_preview=False
                )
            )
        ]

        await inline_query.answer(answers, cache_time=1, is_personal=True)
        await save_data_to_db(user_data)

async def save_data_to_db(user_data: Data):
    try:
        async with aiofiles.open("database/users.json", "r", encoding="utf-8") as file:
            content = await file.read()
            users = json.loads(content)
            logger.info(f"База данных загружена. Найдено {len(users)} пользователей.")

        if not any(user["username"] == user_data.username and user["link"] == user_data.userlink for user in users):
            users.append({"username": user_data.username, "link": user_data.userlink})
            logger.info(f"Добавлен новый пользователь: {user_data.username} | {user_data.userlink}")

        async with aiofiles.open("database/users.json", "w", encoding="utf-8") as file:
            await file.write(json.dumps(users, indent=4, ensure_ascii=False))

    except FileNotFoundError:
        async with aiofiles.open("database/users.json", "w", encoding="utf-8") as file:
            await file.write(json.dumps([{"username": user_data.username, "link": user_data.userlink}], indent=4, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в базу данных: {e}")
