import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram import F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import logging
from dotenv import load_dotenv
import os
import datetime
import httpx

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
start_builder = InlineKeyboardBuilder()
start_builder.row(InlineKeyboardButton(text="🚀Основная", callback_data="main_key"), 
                  InlineKeyboardButton(text="🆘 Дополнительная", callback_data="emergency_key"),
                  InlineKeyboardButton(text="🐹 Профиль", callback_data="profile"),
                  InlineKeyboardButton(text="❓ Как настроить", callback_data="instruction"), width=2)
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
                  width=2)
registration_builder = InlineKeyboardBuilder()
registration_builder.row(InlineKeyboardButton(text="🔓 Активировать доступ", callback_data="register"))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
                    )
logger = logging.getLogger(__name__)


class RegistrationState(StatesGroup):
    waiting_for_code = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/user/{message.from_user.id}")
    user_info = response.json()
    print(f"User info for {message.from_user.id}: {user_info}")
    if user_info is None or not user_info['is_active']:
        await message.answer("<b>Привет! На связи Hamsterdam 🐹</b>"
            "Твой персональный туннель в свободный интернет."
            "Нажми кнопку ниже, чтобы получить доступ.", reply_markup=registration_builder.as_markup())
    
    else:
        text = (f"<b>🐹 Hamsterdam на базе!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Статус: 🟢 <b>Подключен</b>\n"
            f"Сервер: 🇳🇱 Нидерланды\n\n"
            f"Твой трафик за месяц: <code>{user_info['traffic_usage']/1024/1024/1024:.2f} ГБ</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Нужна помощь с настройкой? Жми на <b>Инструкцию</b>."
                    )
        await message.answer(text, parse_mode="HTML", reply_markup=start_builder.as_markup())



@dp.callback_query(F.data == "main_key")
async def get_key(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        name = callback_query.from_user.username or callback_query.from_user.first_name
        response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/get_link/{callback_query.from_user.id}",params={"username": name})
        link = response.json().get("link") 
        text = (
        "🐹 <b>Твоя основная ссылка</b>\n"
        "Нажми на код ниже, чтобы скопировать его в буфер обмена:\n\n"
        f"<code>{link}</code>\n\n"
        "<i>После копирования вставь ссылку в своё приложение для VPN.</i>"
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
        response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/get_config/{callback_query.from_user.id}",params={"username": name, "inbound_index": 1})
        link = response.json().get("link")
        text = (
        "🔄 <b>Резервный канал</b>\n"
        "Используй эту ссылку, если основной канал работает медленно или не подключается:\n\n"
        f"<code>{link}</code>\n\n"
        "<i>Этот ключ использует альтернативный способ обхода блокировок.</i>"
        )
        await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=menu_builder.as_markup())
    except Exception as e:
        logger.error(f"Error occurred while fetching emergency VPN config: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}")



@dp.callback_query(F.data == "instruction")
async def show_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("⚙️ <b>Настройка подключения</b>\n"
                        "Выбери устройство, на котором будешь использовать VPN:", 
                           parse_mode="HTML", reply_markup=instructions_builder.as_markup())


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(    "🐹 <b>Hamsterdam на связи!</b>\n"
        "Все системы работают штатно. Выбери нужное действие в меню ниже:",
        parse_mode="HTML", reply_markup=start_builder.as_markup())

@dp.callback_query(F.data == "profile")
async def show_profile(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/user/{callback_query.from_user.id}")
        user_info = response.json()
        if user_info is None:
            await callback_query.message.answer("🐹 Похоже, мы еще не знакомы. Нажми \"Основная\", чтобы создать аккаунт.", parse_mode="HTML")
            return
        status = "🟢 Активен" if user_info['is_active'] else "🔴 Неактивен"
        text = (f"👤 Имя: {user_info['username']}\n"
                        f"🌍 Локация: Нидерланды 🇳🇱\n"
                         f"🌐 IP сервера: {user_info['server_ip']}\n"
                         f"🔋 Статус: {status}\n"
                         f"⏳ Срок действия: Бессрочно\n"
                         f"📊 Использованный трафик: {user_info['traffic_usage']/(1024*1024*1024):.2f} Гб\n"
                    )
        await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=menu_builder.as_markup())
    except Exception as e:
        logger.error(f"Error occurred while fetching user profile: {str(e)}, User Info: {user_info}")
        await callback_query.message.answer(f"Error: {str(e)}", parse_mode="HTML")

@dp.callback_query(F.data == "register")
async def register_user(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/user/{callback_query.from_user.id}")
    if response.json():
        await callback_query.message.answer("🐹 Спокойно, ты уже с нами! Ключи лежат в главном меню.", parse_mode="HTML", reply_markup=start_builder.as_markup())
        return
    await state.set_state(RegistrationState.waiting_for_code)
    await callback_query.message.answer("🐹 Пожалуйста, введите секретный код для входа в Hamsterdamю"
                                        "Получить код можно у администратора сервера "
                                        , parse_mode="HTML")

@dp.message(RegistrationState.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/invite/{code}")
    if not response.json():
        await message.answer("🐹 <b>Код неверный.</b> Убедись, что нет лишних пробелов, и попробуй ещё раз.", parse_mode="HTML")
        return

    try:
        uuid = await httpx.AsyncClient().post(f"{os.getenv('API_URL')}/register", json={
            "username": message.from_user.username or message.from_user.first_name,
            "telegram_id": str(message.from_user.id)
        }).json().get("uuid")
        await message.answer("✨ Готово! Ты в системе. Теперь загляни в меню за ключами.", parse_mode="HTML", reply_markup=start_builder.as_markup())
        await httpx.AsyncClient().post(f"{os.getenv('API_URL')}/invite/{code}/use")
    except Exception as e:
        logger.error(f"Error occurred during registration: {str(e)}")
        await message.answer(f"Ошибка при регистрации: {str(e)}", parse_mode="HTML")
    finally:
        await state.clear()

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if str(message.from_user.id) == os.getenv("ADMIN_TELEGRAM_ID"):
        try:
            await message.answer("Добро пожаловать, Хозяин. Что желаете?", parse_mode="HTML", reply_markup=admin_builder.as_markup())
        except Exception as e:
            logger.error(f"Error occurred while fetching vnstat data: {str(e)}")
            await message.answer(f"Error: {str(e)}", parse_mode="HTML")
    else:
        await message.answer("🚫 Сюда хомякам нельзя. Это только для смотрителя тоннеля.", parse_mode="HTML")

@dp.callback_query(F.data == "show_stats")
async def show_stats(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/vnstat/daily")
        daily_usage = response.json().get("daily_usage")
        response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/vnstat/monthly")
        monthly_usage = response.json().get("monthly_usage")
        response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/users")
        users = response.json().get("users")
        traffic = [(user[1], user[6]) for user in users]
        text = "<b>Статистика использования трафика:</b>\n\n"
        for username, usage in traffic:
            usage_gb = usage / (1024 * 1024 * 1024)  # Convert to GB
            text += f"Пользователь: {username}, Использованный трафик: {usage_gb:.2f} Гб\n"
        text += f"\n<b>Общий трафик за сегодня:</b> {daily_usage} Гб\n"
        text += f"<b>Общий трафик за этот месяц:</b> {monthly_usage} Гб\n"
        text += f"<b>Остаток трафика:</b> {1000 - float(monthly_usage):.2f} Гб\n"
        await callback_query.message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error occurred while fetching vnstat data: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}", parse_mode="HTML")
@dp.callback_query(F.data == "show_users")
async def show_users(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        response = await httpx.AsyncClient().get(f"{os.getenv('API_URL')}/users")
        users = response.json().get("users")

        if not users:
            await callback_query.message.answer("Пользователей не найдено.", parse_mode="HTML")
            return
        text = "<b>Список пользователей:</b>\n\n"
        for user in users:
            text += f"Имя: {user[1]}, Дата регистрации: {user[4]}, Статус: {'Активен' if user[5] else 'Неактивен'}\n"
        await callback_query.message.answer(text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error occurred while fetching users: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}", parse_mode="HTML")

@dp.callback_query(F.data == "create_invite")
async def create_invite(callback_query: CallbackQuery):
    await callback_query.answer()
    try:
        response = await httpx.AsyncClient().post(f"{os.getenv('API_URL')}/invite")
        code = response.json().get("code")
        await callback_query.message.answer(f"Новый инвайт код: <code>{code}</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error occurred while creating invite code: {str(e)}")
        await callback_query.message.answer(f"Error: {str(e)}", parse_mode="HTML")

@dp.callback_query(F.data == "android_instruction")
async def android_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    text = ("🤖 Инструкция для Android\n"
            "1. Скачай v2rayNG из Play Store или GitHub.\n"
            "2. Скопируй ссылку из бота.\n"
            "3. В приложении нажми '+' вверху -> 'Импортировать из буфера обмена'.\n"
            "4. Нажми на иконку щита (или V в кружочке) для подключения.")
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=instructions_builder.as_markup())
@dp.callback_query(F.data == "ios_instruction")
async def ios_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    text = ("🍎 Инструкция для iOS\n"
            "1. Скачай V2Box или Streisand из App Store (они бесплатные и поддерживают Reality).\n"
            "2. Скопируй ссылку из бота.\n"
            "3. В приложении нажми \"Configs\" -> "+" -> \"Import vless link from clipboard\"\n"
            "4. Вернись на главный экран и нажми \"Connect\".")
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=instructions_builder.as_markup())
@dp.callback_query(F.data == "windows_instruction")
async def windows_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    text = ("💻 Инструкция для Windows\n"
            "1. Скачай v2rayN (GitHub) или Nekoray.\n"
            "2. Распакуй архив и запусти .exe.\n"
            "3. Скопируй ссылку, в приложении нажми \"Серверы\" -> \"Импортировать из буфера обмена\".\n"
            "4. Нажми правой кнопкой на значок в трее -> \"Режим системного прокси\" -> \"Включить\".")
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=instructions_builder.as_markup())

@dp.callback_query(F.data == "macos_instruction")
async def macos_instruction(callback_query: CallbackQuery):
    await callback_query.answer()
    text = ("🍏 Инструкция для macOS\n"
            "1. Скачай V2Box или FoXray из App Store.\n"
            "2. Скопируй ссылку.\n"
            "3. В приложении нажми \"+\" (или \"Import\") и вставь ссылку из буфера."
            "4. Нажми кнопку подключения.")
    await callback_query.message.edit_text(text, parse_mode="HTML", reply_markup=instructions_builder.as_markup())

async def traffic_update():
    last_reset_month = datetime.datetime.now().month
    while True:
        current_month = datetime.datetime.now().month
        if current_month != last_reset_month:
            try:
                logger.info("Resetting monthly traffic usage for all users...")
                await httpx.AsyncClient().post(f"{os.getenv('API_URL')}/reset_all_traffic")
                last_reset_month = current_month
                logger.info("Monthly traffic usage reset successfully.")
            except Exception as e:
                logger.error(f"Error occurred while resetting monthly traffic usage: {str(e)}")
        try:
            logger.info("Updating traffic usage for all users...")
            await httpx.AsyncClient().post(f"{os.getenv('API_URL')}/update_traffic_usage")
            logger.info("Traffic usage updated successfully.")
        except Exception as e:
            logger.error(f"Error occurred while updating traffic usage: {str(e)}")
        await asyncio.sleep(600)  # Update every 10 minutes

async def main():
    logger.info("Bot is starting up...")
    asyncio.create_task(traffic_update())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
