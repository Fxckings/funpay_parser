import asyncio
from create_bot import bot, dp
from loguru import logger
from tgbot import router

logger.add("tgbot.log", format="{time} | {level} | {message}", level="INFO")

async def main():
    try:
        dp.include_router(router)

        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(e)

if __name__ == "__main__":
    asyncio.run(main())