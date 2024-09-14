import asyncio
from create_bot import bot, dp
import logging
from tgbot import router

logger = logging.getLogger(__name__)

async def main():
    try:
        dp.include_router(router)

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(e)

if __name__ == "__main__":
    asyncio.run(main())