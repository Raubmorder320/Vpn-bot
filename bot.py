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
builder = InlineKeyboardBuilder()
builder.row(InlineKeyboardButton(text="Получить VPN 🚀", callback_data="get_config"))
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
                    )
logger = logging.getLogger(__name__)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Welcome to the VPN Bot! Use /getconfig to get your VPN configuration.", reply_markup=builder.as_markup())



@dp.callback_query(F.data == "get_config")
async def get_config(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        link = vpn_service.get_user_config(str(callback_query.from_user.id))
        await callback_query.message.answer(f"Your VPN configuration link: {link}")
    except Exception as e:
        logger.error(f"Error occurred while fetching VPN config: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}")

if __name__ == '__main__':
    from asyncio import run
    run(dp.start_polling(bot))
