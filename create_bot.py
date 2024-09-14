import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    scheduler.start() # запускает планировщик заданий. Это позволяет выполнять задачи по расписанию, например, каждый день в 10:00 он будет отправлять сообщение всем пользователям, зарегистрированным в базе данных, с уведомлением о том, что настала их регистрация.
    
    bot = Bot(token=config('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
except Exception as e:
    logger.error(f'Error in create_bot: {e}')
