from aiogram import F, Router, types
from main import *
from datetime import datetime, timedelta

router = Router()
user_data_cache = {}
CACHE_DURATION = timedelta(minutes=10)

@router.message(F.text.startswith("https://funpay.com/users/"))
async def send_links(message: types.Message):
    user_id = message.text.split('/')[-2]
    user_data = await parse_usr_data(user_id)

    if user_data:
        await message.answer(f"""
💎 Информация о пользователе <b>{user_data.username}</b>

⭐ Количиство отзывов: <b>{user_data.reviews}</b>
⭐ Рейтинг: <b>{user_data.estimation}</b>
📅 Дата регистрации: <b>{user_data.date_reg}</b>
⚙️ Кол-во предложений (категорий): <b>{user_data.count_offers}</b>
⚙️ Кол-во лотов: <b>{user_data.lots}</b>
📐 Средняя цена: <b>{user_data.avr_price}</b>
{"🟢" if user_data.status == 'Онлайн' else "🔴"} Статус: <b>{user_data.status}</b>
🧑‍💻 Ссылка на профиль: <b>{user_data.link}</b>
🎰 Самый доролой лот: <b>{user_data.price}₽ - {user_data.link}</b>
🎃 Аватарка: <b>{user_data.avatar}</b>
🐤 Популярные игры в отзывах: <b>{user_data.games}</b>

🐵 Последний отзыв: 
{user_data.last_review}
""", parse_mode="HTML")

@router.message(F.text.startswith("/start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот для FunPay. Отправь мне ссылку на профиль, и я выведу информацию о пользователе.")


async def get_cached_user_data(user_id, parse_usr_data_func):
    if user_id in user_data_cache:
        cached_entry = user_data_cache[user_id]
        timestamp, data = cached_entry["timestamp"], cached_entry["data"]

        if datetime.now() - timestamp < CACHE_DURATION:
            return data

    user_data = await parse_usr_data_func(user_id)

    user_data_cache[user_id] = {
        "timestamp": datetime.now(),
        "data": user_data
    }

    return user_data

@router.inline_query()
async def inline_search(inline_query: types.InlineQuery):
    if not "https://funpay.com/users/" in inline_query.query:
        return
    user_id = inline_query.query.split('/')[-2]

    user_data = await get_cached_user_data(user_id, parse_usr_data)

    if user_data:
        answer = types.InlineQueryResultArticle(
            id='1',
            title=f"Информация о: {user_data.username}",
            input_message_content=types.InputTextMessageContent(
                message_text=f"""
💎 Информация о пользователе <b>{user_data.username}</b>

⭐ Количиство отзывов: <b>{user_data.reviews}</b>
⭐ Рейтинг: <b>{user_data.estimation}</b>
📅 Дата регистрации: <b>{user_data.date_reg}</b>
⚙️ Кол-во предложений (категорий): <b>{user_data.count_offers}</b>
⚙️ Кол-во лотов: <b>{user_data.lots}</b>
📐 Средняя цена: <b>{user_data.avr_price}</b>
{"🟢" if user_data.status == 'Онлайн' else "🔴"} Статус: <b>{user_data.status}</b>
🧑‍💻 Ссылка на профиль: <b>{inline_query.query}</b>
🎰 Самый дорогой лот: <b>{user_data.price}₽ - {user_data.link}</b>
🎃 Аватарка: <b>{user_data.avatar}</b>
🐤 Популярные игры в отзывах: <b>{user_data.games}</b>
🐒 Продает рублевки мансори: <b>{"Да🐷" if user_data.mansory else "Нет🤯"}</b>

Последний отзыв: 
{user_data.last_review}
""", parse_mode="HTML"
            )
        )
        await inline_query.answer([answer])