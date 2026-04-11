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
start_builder.row(InlineKeyboardButton(text="🚀Основная", callback_data="main_key"), 
                  InlineKeyboardButton(text="🆘 Дополнительная", callback_data="emergency_key"),
                  InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
                  InlineKeyboardButton(text="ℹ️ Инструкция", callback_data="instruction"), width=2)
back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
instructions_builder = InlineKeyboardBuilder()
instructions_builder.row(back_button, InlineKeyboardButton(text="Android", callback_data="android_instruction"), 
                         InlineKeyboardButton(text="iOS", callback_data="ios_instruction"), 
                         InlineKeyboardButton(text="Windows", callback_data="windows_instruction"), 
                         InlineKeyboardButton(text="MacOS", callback_data="macos_instruction"), width=2)
menu_builder = InlineKeyboardBuilder()
menu_builder.row(back_button)

admin_builder = InlineKeyboardBuilder()
admin_builder.row(InlineKeyboardButton(text=" 📊 Общий трафик", callback_data="show_stats"), 
                  InlineKeyboardButton(text="➕ Создать инвайт", callback_data="create_invite"), 
                  InlineKeyboardButton(text=" 👥 Список юзеров", callback_data="show_users"), 
                  InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"), width=2)

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
        text = (f"Привет! Добро пожаловать в бот! Информация о пользователе:\n\n" 
                         f"Имя: {user_info['username']}\n"
                         f"ID: {user_info['telegram_id']}\n"
                         f"Дата регистрации: {user_info['created_at']}\n"
                    )
        await message.answer(text, parse_mode="HTML", reply_markup=start_builder.as_markup())



@dp.callback_query(F.data == "main_key")
async def get_key(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        name = callback_query.from_user.username or callback_query.from_user.first_name
        link = vpn_service.get_user_config(str(callback_query.from_user.id), name)
        text = (
            "<b>Вот ваша основная ссылка для подключения к VPN.</b>\nДля копирования нажмите на неё.\n\n"
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
    await callback_query.message.edit_text("Выберите вашу операционную систему:", parse_mode="HTML", reply_markup=instructions_builder.as_markup())


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("Вы находитесь в главном меню.", parse_mode="HTML", reply_markup=start_builder.as_markup())

@dp.callback_query(F.data == "profile")
async def show_profile(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        user_info = vpn_service.get_user_info(str(callback_query.from_user.id))
        if user_info is None:
            await callback_query.message.answer("Пользователь не найден. Пожалуйста, нажмите кнопку 'Основная', чтобы создать профиль.", parse_mode="HTML")
            return
        text = (f"👤 Имя: {user_info['username']}\n"
                         f"🌐 IP сервера: {vpn_service.server_ip}\n"
                         f"🔋 Статус: {user_info['is_active']}\n"
                         f"⏳ Срок действия: Бессрочно\n"
                    )
        await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=menu_builder.as_markup())
    except Exception as e:
        logger.error(f"Error occurred while fetching user profile: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}", parse_mode="HTML")

@dp.message(Command("admin"))
async def show_stats(message: types.Message):
    if str(message.from_user.id) == os.getenv("ADMIN_TELEGRAM_ID"):
        try:
            await message.answer("Добро пожаловать, Хозяин. Что желаете?", parse_mode="HTML", reply_markup=admin_builder.as_markup())
        except Exception as e:
            logger.error(f"Error occurred while fetching vnstat data: {str(e)}")
            await message.answer(f"Error: {str(e)}", parse_mode="HTML")
    else:
        await message.answer("У вас нет доступа к этой команде.", parse_mode="HTML")

@dp.callback_query(F.data == "show_stats")
async def show_stats(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        daily_usage = vpn_service.vnstat_daily_usage()
        monthly_usage = vpn_service.vnstat_monthly_usage()
        await callback_query.message.answer(f"За сегодня использовано {daily_usage} Гб\nЗа этот месяц использовано {monthly_usage} Гб\n\nОстаток трафика: {1000 - float(monthly_usage)} Гб", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error occurred while fetching vnstat data: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}", parse_mode="HTML")
@dp.callback_query(F.data == "show_users")
async def show_users(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        users = vpn_service.get_all_users()
        if not users:
            await callback_query.message.answer("Пользователей не найдено.", parse_mode="HTML")
            return
        text = "<b>Список пользователей:</b>\n\n"
        for user in users:
            text += f"ID: {user['telegram_id']}, Имя: {user['username']}, Дата регистрации: {user['created_at']}\n"
        await callback_query.message.answer(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error occurred while fetching users: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}", parse_mode="HTML")

# @dp.callback_query(F.data == "create_invite")
# async def create_invite(callback_query: CallbackQuery):

@dp.callback_query(F.data == "android_instruction")
async def android_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    text = (f"Инструкция для Android: \n "
            f"1. Скачайте и установите приложение XrayR из Google Play Store. \n "
            f"2. Откройте приложение и нажмите на кнопку 'Добавить конфигурацию'. \n "
            f"3. Выберите 'Импортировать из ссылки' и вставьте ваш VPN ключ, который вы получили от бота. \n "
            f"4. Сохраните конфигурацию и активируйте её.")
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=instructions_builder.as_markup())
@dp.callback_query(F.data == "ios_instruction")
async def ios_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    text = (f"Инструкция для iOS: \n "
            f"1. Скачайте и установите приложение ShadowRay из App Store. \n "
            f"2. Откройте приложение и нажмите на кнопку 'Добавить конфигурацию'. \n "
            f"3. Выберите 'Импортировать из ссылки' и вставьте ваш VPN ключ, который вы получили от бота. \n "
            f"4. Сохраните конфигурацию и активируйте её.")
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=instructions_builder.as_markup())
@dp.callback_query(F.data == "windows_instruction")
async def windows_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    text = (f"Инструкция для Windows: \n "
            f"1. Скачайте и установите приложение XrayR для Windows с официального сайта. \n "
            f"2. Откройте приложение и нажмите на кнопку 'Добавить конфигурацию'. \n "
            f"3. Выберите 'Импортировать из ссылки' и вставьте ваш VPN ключ, который вы получили от бота. \n "
            f"4. Сохраните конфигурацию и активируйте её.")
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=instructions_builder.as_markup())

@dp.callback_query(F.data == "macos_instruction")
async def macos_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    text = (f"Инструкция для MacOS: \n "
            f"1. Скачайте и установите приложение ShadowRay для MacOS с официального сайта. \n "
            f"2. Откройте приложение и нажмите на кнопку 'Добавить конфигурацию'. \n "
            f"3. Выберите 'Импортировать из ссылки' и вставьте ваш VPN ключ, который вы получили от бота. \n "
            f"4. Сохраните конфигурацию и активируйте её.")
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=instructions_builder.as_markup())

if __name__ == '__main__':
    from asyncio import run
    run(dp.start_polling(bot))
