from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN
from db import setup_db

from user import set_handlers_user
from admin import set_handlers_admin

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


def start():
    setup_db()
    set_handlers_user(dp)
    set_handlers_admin(dp)
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    start()
