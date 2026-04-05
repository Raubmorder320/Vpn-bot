from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram import F
from aiogram.client.session.aiohttp import AiohttpSession
from core import VpnService 
import logging
from dotenv import load_dotenv
import os


load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
vpn_service = VpnService(os.getenv("CONFIG_PATH"), os.getenv("DB_PATH"))
start_builder = InlineKeyboardBuilder()
start_builder.row(InlineKeyboardButton(text="🔑Мой ключ", callback_data="get_key"), InlineKeyboardButton(text="ℹ️ Инструкция", callback_data="instruction"))
menu_builder = InlineKeyboardBuilder()
menu_builder.row(InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu"))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
                    )
logger = logging.getLogger(__name__)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_info = vpn_service.get_user_info(str(message.from_user.id))
    if user_info is None:
        await message.answer("Привет! Добро пожаловать в бот! Похоже, вы новый пользователь. Нажмите кнопку ниже, чтобы получить свой VPN ключ.", reply_markup=start_builder.as_markup())
    else:
        await message.answer(f"""Привет! Добро пожаловать в бот! Информация о пользователе:\n 
                         Имя: {user_info['username']} \n
                         ID: {user_info['telegram_id']}\n
                        Дата регистрации: {user_info['created_at']} \n
                    """, reply_markup=start_builder.as_markup())



@dp.callback_query(F.data == "get_key")
async def get_key(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        link = vpn_service.get_user_config(str(callback_query.from_user.id))
        await callback_query.message.edit_text(f"Your VPN configuration link: {link}", reply_markup=menu_builder.as_markup())
    except Exception as e:
        logger.error(f"Error occurred while fetching VPN config: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}")


@dp.callback_query(F.data == "instruction")
async def show_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("Here is how to use the VPN configuration.", reply_markup=menu_builder.as_markup())


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("Вы находитесь в главном меню.", reply_markup=start_builder.as_markup())

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    await message.answer(message.from_user.id)
    if str(message.from_user.id) == os.getenv("ADMIN_TELEGRAM_ID"):
        try:
            daily_usage = vpn_service.vnstat_daily_usage()
            await message.answer(f"За сегодня использовано {daily_usage} Гб")
        except Exception as e:
            logger.error(f"Error occurred while fetching vnstat data: {str(e)}")
            await message.answer(f"Error: {str(e)}")
    else:
        await message.answer("У вас нет доступа к этой команде.")

if __name__ == '__main__':
    from asyncio import run
    run(dp.start_polling(bot))
