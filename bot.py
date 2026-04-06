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
start_builder.row(InlineKeyboardButton(text="Основная🚀", callback_data="main_key"), InlineKeyboardButton(text="🆘 Аварийная", callback_data="emergency_key"), InlineKeyboardButton(text="ℹ️ Инструкция", callback_data="instruction"), width=2)
back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
instructions_builder = InlineKeyboardBuilder()
instructions_builder.row(back_button, InlineKeyboardButton(text="Android", callback_data="android_instruction"), 
                         InlineKeyboardButton(text="iOS", callback_data="ios_instruction"), 
                         InlineKeyboardButton(text="Windows", callback_data="windows_instruction"), 
                         InlineKeyboardButton(text="MacOS", callback_data="macos_instruction"), width=2)
menu_builder = InlineKeyboardBuilder()
menu_builder.row(back_button)


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



@dp.callback_query(F.data == "main_key")
async def get_key(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        name = callback_query.from_user.username or callback_query.from_user.first_name
        link = vpn_service.get_user_config(str(callback_query.from_user.id), name)
        text = (
            "<b>Вот ваша основная ссылка для подключения к VPN.</b>\n\n"
            f"<code>{link}</code>\n\n"
        )
        await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=menu_builder.as_markup())
    except Exception as e:
        logger.error(f"Error occurred while fetching VPN config: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}")

@dp.callback_query(F.data == "emergency_key")
async def get_emergency_key(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        name = callback_query.from_user.username or callback_query.from_user.first_name
        link = vpn_service.get_user_config(str(callback_query.from_user.id), name, inbound_index=1)
        text = (
            "<b>Вот ваша аварийная ссылка для подключения к VPN.</b>\n\n"
            f"<code>{link}</code>\n\n"
        )
        await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=menu_builder.as_markup())
    except Exception as e:
        logger.error(f"Error occurred while fetching emergency VPN config: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}")



@dp.callback_query(F.data == "instruction")
async def show_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("Выберите вашу операционную систему:", reply_markup=instructions_builder.as_markup())


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("Вы находитесь в главном меню.", reply_markup=start_builder.as_markup())

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    if str(message.from_user.id) == os.getenv("ADMIN_TELEGRAM_ID"):
        try:
            daily_usage = vpn_service.vnstat_daily_usage()
            monthly_usage = vpn_service.vnstat_monthly_usage()
            await message.answer(f"За сегодня использовано {daily_usage} Гб\nЗа этот месяц использовано {monthly_usage} Гб\n\nОстаток трафика: {1000 - int(monthly_usage)} Гб")
        except Exception as e:
            logger.error(f"Error occurred while fetching vnstat data: {str(e)}")
            await message.answer(f"Error: {str(e)}")
    else:
        await message.answer("У вас нет доступа к этой команде.")

@dp.callback_query(F.data == "android_instruction")
async def android_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("""Инструкция для Android: \n 
                                           1. Скачайте и установите приложение XrayR из Google Play Store. \n 
                                           2. Откройте приложение и нажмите на кнопку 'Добавить конфигурацию'. \n 
                                           3. Выберите 'Импортировать из ссылки' и вставьте ваш VPN ключ, который вы получили от бота. \n 
                                           4. Сохраните конфигурацию и активируйте её.""", reply_markup=instructions_builder.as_markup())
@dp.callback_query(F.data == "ios_instruction")
async def ios_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("""Инструкция для iOS: \n 
                                           1. Скачайте и установите приложение ShadowRay из App Store. \n 
                                           2. Откройте приложение и нажмите на кнопку 'Добавить конфигурацию'. \n 
                                           3. Выберите 'Импортировать из ссылки' и вставьте ваш VPN ключ, который вы получили от бота. \n 
                                           4. Сохраните конфигурацию и активируйте её.""", reply_markup=instructions_builder.as_markup())
@dp.callback_query(F.data == "windows_instruction")
async def windows_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("""Инструкция для Windows: \n 
                                           1. Скачайте и установите приложение XrayR для Windows с официального сайта. \n 
                                           2. Откройте приложение и нажмите на кнопку 'Добавить конфигурацию'. \n 
                                           3. Выберите 'Импортировать из ссылки' и вставьте ваш VPN ключ, который вы получили от бота. \n 
                                           4. Сохраните конфигурацию и активируйте её.""", reply_markup=instructions_builder.as_markup())
@dp.callback_query(F.data == "macos_instruction")
async def macos_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("""Инструкция для MacOS: \n 
                                           1. Скачайте и установите приложение ShadowRay для MacOS с официального сайта. \n 
                                           2. Откройте приложение и нажмите на кнопку 'Добавить конфигурацию'. \n 
                                           3. Выберите 'Импортировать из ссылки' и вставьте ваш VPN ключ, который вы получили от бота. \n 
                                           4. Сохраните конфигурацию и активируйте её.""", reply_markup=instructions_builder.as_markup())

if __name__ == '__main__':
    from asyncio import run
    run(dp.start_polling(bot))
