import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIMARY_ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 
SECRET_ADMIN_CODE = "Ризван РЭУ Чечня"
BAN_SECRET_CODE = "Наталья Альбертовна" 
ADMIN_IDS = {PRIMARY_ADMIN_ID} 

BANNED_WORDS = ["хуй", "пизд", "бля", "еба", "ебал", "секс", "порно", "гандон", "долбоеб"]
banned_users = set() 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

users_db = {}      
pending_db = {}    
likes_db = {}      
swiped_db = {}     
user_bot_style = {} 
messages_map = {} 

class ProfileForm(StatesGroup):
    name = State()
    age = State()
    gender = State()
    grade = State()
    about = State()
    goal = State()
    photo = State()

class AdminForm(StatesGroup):
    waiting_for_code = State()

class SupportForm(StatesGroup):
    waiting_for_msg = State()

class BanForm(StatesGroup):
    waiting_for_reason = State()

class TikTokForm(StatesGroup):
    waiting_for_link = State()

# --- ТЕКСТЫ СТИЛЕЙ ---
TEXTS = {
    "standard": {
        "start": "Йоу, {name}! Я АлкоRedБот. Готов найти пару?",
        "ask_name": "Погнали! Как тебя зовут?",
        "ask_age": "Сколько тебе лет?",
        "ask_photo": "Кинь свою фотку для анкеты (отправь как фото):",
        "done": "Анкета отправлена на проверку админам! 🕵️‍♂️",
        "match": "🎉 МЭТЧ! Вы понравились друг другу!"
    },
    "flirt": {
        "start": "Приветик, {name} 😘 Я твой личный сваха-бот. Погнали искать любовь?",
        "ask_name": "Как зовут моего пупсика?",
        "ask_age": "Сколько тебе годиков, конфетка?",
        "ask_photo": "А теперь скинь свою самую сочную аватарку 💋",
        "done": "Ммм, анкета улетела на проверку! Жди, пупсик 🥵",
        "match": "🔥 МЭТЧ! Пупсик, вы созданы друг для друга!"
    },
    "alt": {
        "start": "Йоу, {name} 🖤 Я АлкоRedБот. Тут не кринжуют, а ищут свою родственную душу.",
        "ask_name": "Как тебя величать, дед инсайд?",
        "ask_age": "Сколько тебе лет?",
        "ask_photo": "Закинь фотку, где ты максимально на стиле. Жду.",
        "done": "Окей, база. Анкета на модерации, жди 🕸",
        "match": "💀 МЭТЧ! Вы нашли друг друга в этом жестоком мире."
    },
    "en": {
        "start": "Yo {name}! I'm the AlkoRedBot. Ready to find a date?",
        "ask_name": "Let's go! What's your name?",
        "ask_age": "How old are you?",
        "ask_photo": "Drop your best pic for the profile:",
        "done": "Profile sent for moderation! 🕵️‍♂️",
        "match": "🎉 IT'S A MATCH! You liked each other!"
    },
    "chechnya": {
        "start": "Ассаламу алейкум, {name}! 🔥 Я АлкоRedБот. Братан, ищем пару на бал или просто красивую девушку? Вах, погнали!",
        "ask_name": "Братан, как тебя зовут? (Напиши имя)",
        "ask_age": "Сколько лет тебе, брат?",
        "ask_photo": "Кинь фотку, брат. Где ты на стиле, как настоящий джигит 🦅",
        "done": "Анкета готова, брат! Вах, красавчик! Отправил на проверку админам 🦅",
        "match": "🔥 МЭТЧ! Братан, это судьба! Вах, поздравляю, она твоя! 😎"
    }
}

AURAS = [
    "🌟 Аура: 99% Джигит. Вах, красавчик! 🦅",
    "🖤 Аура: 100% Альтушка. Дед инсайд detected 🕸",
    "😎 Аура: 85% Мачо. База.",
    "🤡 Аура: 70% Кринж. Но мы тебя все равно любим.",
    "🔥 Аура: 120% Огонь. Я уже красный!",
    "💀 Аура: 66% Сатана. С тобой лучше не шутить.",
    "🥀 Аура: 90% Романтик. Ждешь вальс на балу?",
    "💸 Аура: 100% Спонсор. Угостишь всех шаурмой?",
    "👽 Аура: 42% Инопланетянин. Ты точно из нашего лицея?",
    "👑 Аура: 100% Король/Королева бала. Слушаюсь и повинуюсь."
]

TIKTOK_ALT = [
    "🖤 Ну такое... Слишком попсово для меня. Меньше трендов, больше депрессии.",
    "🕸 Че за база? Я такое видела в 2019. Удали, пока не поздно.",
    "💀 Кринж. Но мне почему-то нравится. Странно.",
    "🥀 Слишком ярко. Мне нужно что-то потемнее и погрустнее.",
    "🦇 Норм, но тебе не хватает черной одежды и грустной музыки."
]

TIKTOK_JEW = [
    "💸 А сколько ты за этот ТикТок заплатил? Зря. Лучше бы в бизнес вложил.",
    "🤨 И это все? Мой дедушка в Одессе снимал лучше на кассету в 90-х.",
    "💼 Ладно, допустим. Но коммерческой жилки я тут не вижу. В минус работаешь.",
    "🥯 Норм, но за такую музыку нужно доплачивать. Ты вообще в курсе цен на рынке?",
    "✡️ Слушай, ну это несерьезно. Давай по-деловому: где гарантии, где контракт?"
]

def get_text(user_id, key, **kwargs):
    style = user_bot_style.get(user_id, "standard")
    text = TEXTS[style].get(key, TEXTS["standard"].get(key, ""))
    return text.format(**kwargs)

# --- КЛАВИАТУРЫ ---
def get_start_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📩 Связь с админом"))
    builder.add(KeyboardButton(text="👑 Я админ"))
    builder.add(KeyboardButton(text="🚀 В главное меню"))
    return builder.as_markup(resize_keyboard=True)

def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📝 Создать/Изменить анкету"))
    builder.add(KeyboardButton(text="🔍 Искать пару"))
    builder.add(KeyboardButton(text="👤 Мой профиль"))
    builder.add(KeyboardButton(text="✨ Моя аура")) 
    builder.add(KeyboardButton(text="📱 Оценить ТикТок")) 
    builder.add(KeyboardButton(text="🗑 Удалить профиль"))
    builder.add(KeyboardButton(text="⚙️ Сменить стиль бота"))
    return builder.as_markup(resize_keyboard=True)

def get_search_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📩 Связь с админом"))
    builder.add(KeyboardButton(text="⬅️ В главное меню"))
    return builder.as_markup(resize_keyboard=True)

def get_style_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😎 Стандарт", callback_data="set_standard")],
        [InlineKeyboardButton(text="😘 Флирт", callback_data="set_flirt")],
        [InlineKeyboardButton(text="🖤 Альтушка", callback_data="set_alt")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_en")],
        [InlineKeyboardButton(text="🔥 Резванская Чечня", callback_data="set_chechnya")]
    ])

# --- СТАРТ И СТИЛИ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id not in user_bot_style:
        await message.answer("Выбери, как со мной общаться:", reply_markup=get_style_kb())
    else:
        await message.answer(
            get_text(message.from_user.id, "start", name=message.from_user.first_name) + "\n\nЧем займемся?",
            reply_markup=get_start_kb()
        )

@dp.message(F.text == "🚀 В главное меню")
async def go_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear() 
    await message.answer("Твой личный бармен готов! Выбирай действие:", reply_markup=get_main_kb())

@dp.message(F.text == "⬅️ В главное меню")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear() 
    await message.answer("Возвращаемся в меню. Чем займемся?", reply_markup=get_main_kb())

@dp.message(F.text == "⚙️ Сменить стиль бота")
async def change_style_cmd(message: types.Message):
    await message.answer("Выбери новый стиль общения:", reply_markup=get_style_kb())

@dp.callback_query(F.data.startswith("set_"))
async def set_style(callback: CallbackQuery):
    style = callback.data.split("_")[1]
    user_bot_style[callback.from_user.id] = style
    await callback.message.delete()
    await callback.message.answer(
        get_text(callback.from_user.id, "start", name=callback.from_user.first_name) + "\n\nЧем займемся?",
        reply_markup=get_start_kb()
    )
    await callback.answer()

# --- АУРА И ТИКТОК ---
@dp.message(F.text == "✨ Моя аура")
async def show_my_aura(message: types.Message):
    if message.from_user.id not in users_db:
        return await message.answer("Сначала создай анкету, чтобы я увидел твою ауру!")
    
    my_name = users_db[message.from_user.id]['name']
    # Генерируем ауру на основе имени, чтобы она не менялась
    aura_index = sum(ord(c) for c in my_name) % len(AURAS)
    await message.answer(f"🔮 Твоя аура, {my_name}:\n\n{AURAS[aura_index]}")

# Обработка кнопки проверки ЧУЖОЙ ауры
@dp.callback_query(F.data.startswith("aura_"))
async def process_check_aura(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    if target_id in users_db:
        target_name = users_db[target_id]['name']
        aura_index = sum(ord(c) for c in target_name) % len(AURAS)
        # Используем show_alert=True, чтобы всплыло окошко поверх экрана
        await callback.answer(f"🔮 Аура {target_name}:\n\n{AURAS[aura_index]}", show_alert=True)
    else:
        await callback.answer("Анкета недоступна.", show_alert=True)

@dp.message(F.text == "📱 Оценить ТикТок")
async def start_tiktok(message: types.Message, state: FSMContext):
    await message.answer("Скинь ссылку на свой ТикТок, и я его оценю! 👇", reply_markup=ReplyKeyboardRemove())
    await state.set_state(TikTokForm.waiting_for_link)

@dp.message(TikTokForm.waiting_for_link)
async def process_tiktok_link(message: types.Message, state: FSMContext):
    link = message.text
    if "tiktok.com" not in link.lower():
        return await message.answer("Это не похоже на ссылку с ТикТока. Попробуй еще раз или нажми /start для выхода.")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖤 Оценит Альтушка", callback_data="tt_alt")],
        [InlineKeyboardButton(text="💼 Оценит Еврей", callback_data="tt_jew")]
    ])
    await message.answer("Кто должен прокомментировать твой ТикТок?", reply_markup=kb)
    await state.clear()

@dp.callback_query(F.data.startswith("tt_"))
async def review_tiktok(callback: CallbackQuery):
    style = callback.data.split("_")[1]
    if style == "alt":
        comment = random.choice(TIKTOK_ALT)
    else:
        comment = random.choice(TIKTOK_JEW)
        
    await callback.message.edit_text(f"🎬 <b>Вердикт:</b>\n\n{comment}", parse_mode="HTML")
    await callback.message.answer("Возвращаемся в меню:", reply_markup=get_main_kb())
    await callback.answer()

# --- АДМИНКА ---
@dp.message(F.text == "👑 Я админ")
async def start_admin_login(message: types.Message, state: FSMContext):
    await message.answer("Введи секретный код доступа:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminForm.waiting_for_code)

@dp.message(AdminForm.waiting_for_code)
async def process_admin_code(message: types.Message, state: FSMContext):
    if message.text.strip() == SECRET_ADMIN_CODE:
        ADMIN_IDS.add(message.from_user.id)
        await message.answer("✅ Код верный! Теперь тебе будут приходить анкеты на проверку, анонимки и жалобы.", reply_markup=get_start_kb())
    else:
        await message.answer("❌ Неверный код.", reply_markup=get_start_kb())
    await state.clear()

# --- СВЯЗЬ С АДМИНОМ ---
@dp.message(F.text == "📩 Связь с админом")
async def start_support(message: types.Message, state: FSMContext):
    await message.answer("📩 <b>Анонимная связь с админами</b>\n\nПиши сюда любые вопросы. Все строго анонимно.", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    await state.set_state(SupportForm.waiting_for_msg)

@dp.message(SupportForm.waiting_for_msg, F.chat.type == "private")
async def forward_support_to_admin(message: types.Message, state: FSMContext):
    for admin_id in ADMIN_IDS:
        try:
            sent_msg = await bot.copy_message(chat_id=admin_id, from_chat_id=message.chat.id, message_id=message.message_id)
            messages_map[sent_msg.message_id] = message.from_user.id
        except: pass 
    await message.answer("Твое сообщение отправлено админам! Возвращаемся в меню.", reply_markup=get_start_kb())
    await state.clear()

@dp.message(F.chat.type == "private", F.reply_to_message)
async def admin_reply_to_support(message: types.Message):
    if message.from_user.id not in ADMIN_IDS: return 
    original_msg_id = message.reply_to_message.message_id
    if original_msg_id in messages_map:
        target_user_id = messages_map[original_msg_id]
        try:
            await bot.copy_message(chat_id=target_user_id, from_chat_id=message.from_user.id, message_id=message.message_id)
            await message.answer("Ответ отправлен! ✅")
        except: pass

# --- СИСТЕМА ЖАЛОБ И БАНОВ ---
@dp.callback_query(F.data.startswith("report_"))
async def process_report(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    
    kb_ban = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Забанить", callback_data=f"askban_{target_id}")]
    ])
    
    report_text = f"🚨 <b>ЖАЛОБА НА АНКЕТУ!</b>\n\nID нарушителя: <code>{target_id}</code>\n"
    if target_id in users_db:
        report_text += f"Имя: {users_db[target_id]['name']}\n\nНажми «Забанить», чтобы вынести приговор."
    
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, report_text, reply_markup=kb_ban, parse_mode="HTML")
        except: pass
    
    await callback.answer("Жалоба отправлена админам! Спасибо.", show_alert=True)

@dp.callback_query(F.data.startswith("askban_"))
async def ask_ban_reason(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("Ты не админ!", show_alert=True)
        
    target_id = int(callback.data.split("_")[1])
    await state.update_data(target_ban_id=target_id)
    
    await callback.message.edit_text(
        "🛑 <b>Вынеси приговор!</b>\n\n"
        "Напиши причину бана для этого пользователя.\n"
        "Или введи секретный код <b>«Наталья Альбертовна»</b>, чтобы забанить без объяснений."
    )
    await state.set_state(BanForm.waiting_for_reason)
    await callback.answer()

@dp.message(BanForm.waiting_for_reason)
async def process_ban_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("target_ban_id")
    reason = message.text.strip()
    
    if target_id in users_db:
        del users_db[target_id]
    banned_users.add(target_id)
    
    if reason == BAN_SECRET_CODE:
        admin_msg = "✅ Пользователь забанен по секретному коду (без объяснений)."
        user_msg = "❌ Твой профиль был забанен. Причина: Нарушение правил."
    else:
        admin_msg = f"✅ Пользователь забанен. Причина: {reason}"
        user_msg = f"❌ Твой профиль был забанен админами.\nПричина: {reason}"
        
    await message.answer(admin_msg, reply_markup=get_main_kb())
    try:
        await bot.send_message(target_id, user_msg)
    except: pass
    await state.clear()

# --- СОЗДАНИЕ АНКЕТЫ ---
@dp.message(F.text == "📝 Создать/Изменить анкету")
async def start_create(message: types.Message, state: FSMContext):
    if message.from_user.id in banned_users:
        return await message.answer("❌ Ты забанен за нарушение правил (фейк). Создание анкеты недоступно.")
    
    await state.clear()
    await message.answer(get_text(message.from_user.id, "ask_name"), reply_markup=ReplyKeyboardRemove())
    await state.set_state(ProfileForm.name)

@dp.message(ProfileForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(get_text(message.from_user.id, "ask_age"))
    await state.set_state(ProfileForm.age)

@dp.message(ProfileForm.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👦 Парень", callback_data="gender_boy")],
        [InlineKeyboardButton(text="👧 Девушка", callback_data="gender_girl")]
    ])
    await message.answer("Кто ты по полу?", reply_markup=kb)
    await state.set_state(ProfileForm.gender)

@dp.callback_query(ProfileForm.gender)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender_text = "Парень 👦" if callback.data == "gender_boy" else "Девушка 👧"
    await state.update_data(gender=gender_text)
    await callback.message.edit_text("В каком ты классе? (Напиши цифру)")
    await state.set_state(ProfileForm.grade)

@dp.message(ProfileForm.grade)
async def process_grade(message: types.Message, state: FSMContext):
    await state.update_data(grade=message.text)
    await message.answer("Расскажи пару слов о себе:")
    await state.set_state(ProfileForm.about)

@dp.message(ProfileForm.about)
async def process_about(message: types.Message, state: FSMContext):
    text = message.text.lower()
    if any(word in text for word in BANNED_WORDS):
        return await message.answer("⚠️ В описании есть запрещенные слова! Перепиши нормально, без мата.")
    if len(message.text) < 5:
        return await message.answer("⚠️ Слишком короткое описание. Напиши хотя бы пару слов о себе.")

    await state.update_data(about=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎉 На бал", callback_data="goal_ball")],
        [InlineKeyboardButton(text="❤️ Отношения", callback_data="goal_rel")],
        [InlineKeyboardButton(text="🤝 Дружба", callback_data="goal_friend")],
        [InlineKeyboardButton(text="💬 Общение", callback_data="goal_chat")]
    ])
    await message.answer("Какая у тебя цель?", reply_markup=kb)
    await state.set_state(ProfileForm.goal)

@dp.callback_query(ProfileForm.goal)
async def process_goal(callback: CallbackQuery, state: FSMContext):
    goals = {"goal_ball": "На бал 🎉", "goal_rel": "Отношения ❤️", "goal_friend": "Дружба 🤝", "goal_chat": "Общение 💬"}
    await state.update_data(goal=goals[callback.data])
    await callback.message.edit_text(get_text(callback.from_user.id, "ask_photo"))
    await state.set_state(ProfileForm.photo)

@dp.message(ProfileForm.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    if message.from_user.id in banned_users:
        return await message.answer("❌ Ты забанен.")

    photo_id = message.photo[-1].file_id
    user_data = await state.get_data()
    
    pending_db[message.from_user.id] = {
        "name": user_data['name'], "age": user_data['age'],
        "gender": user_data['gender'], "grade": user_data['grade'],
        "about": user_data['about'], "goal": user_data['goal'],
        "photo": photo_id
    }
    
    await message.answer(get_text(message.from_user.id, "done"), reply_markup=get_main_kb())
    await state.clear()

    kb_mod = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{message.from_user.id}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{message.from_user.id}")]
    ])
    mod_text = (f"🕵️‍♂️ <b>НОВАЯ АНКЕТА НА ПРОВЕРКУ!</b>\n\n<b>Имя:</b> {user_data['name']}\n<b>Возраст:</b> {user_data['age']}\n"
                f"<b>Пол:</b> {user_data['gender']}\n<b>Класс:</b> {user_data['grade']}\n<b>Цель:</b> {user_data['goal']}\n<b>О себе:</b> {user_data['about']}")
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(chat_id=admin_id, photo=photo_id, caption=mod_text, reply_markup=kb_mod, parse_mode="HTML")
        except: pass

# --- МОДЕРАЦИЯ ---
@dp.callback_query(F.data.startswith("approve_"))
async def approve_profile(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    if user_id in pending_db:
        users_db[user_id] = pending_db[user_id]
        del pending_db[user_id]
        await callback.message.edit_caption(caption="✅ Анкета ОДОБРЕНА и добавлена в поиск.")
        try: await bot.send_message(user_id, "🎉 Твоя анкета одобрена админами! Теперь она участвует в поиске.")
        except: pass
    else:
        await callback.message.edit_caption(caption="Анкета уже была обработана.")
    await callback.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject_profile(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    if user_id in pending_db:
        del pending_db[user_id]
        await callback.message.edit_caption(caption="❌ Анкета ОТКЛОНЕНА.")
        try: await bot.send_message(user_id, "❌ Твоя анкета отклонена админами. Странное фото или описание. Попробуй еще раз.")
        except: pass
    else:
        await callback.message.edit_caption(caption="Анкета уже была обработана.")
    await callback.answer()

# --- ПРОФИЛЬ И УДАЛЕНИЕ ---
@dp.message(F.text == "👤 Мой профиль")
async def my_profile(message: types.Message):
    data = users_db.get(message.from_user.id)
    if not data:
        return await message.answer("Ты пока не создал одобренную анкету!")
    await message.answer_photo(
        photo=data['photo'],
        caption=f"👤 <b>Твоя анкета:</b>\n\n<b>Имя:</b> {data['name']}\n<b>Возраст:</b> {data['age']}\n<b>Пол:</b> {data['gender']}\n<b>Класс:</b> {data['grade']}\n<b>Цель:</b> {data['goal']}\n<b>О себе:</b> {data['about']}",
        parse_mode="HTML"
    )

@dp.message(F.text == "🗑 Удалить профиль")
async def delete_profile(message: types.Message):
    if message.from_user.id in users_db:
        del users_db[message.from_user.id]
        await message.answer("Твоя анкета удалена.", reply_markup=get_main_kb())
    elif message.from_user.id in pending_db:
        del pending_db[message.from_user.id]
        await message.answer("Твоя анкета (на модерации) удалена.", reply_markup=get_main_kb())

# --- ЛЕНТА ---
async def show_next_profile(chat_id, user_id):
    if user_id not in users_db:
        return await bot.send_message(chat_id, "Сначала создай анкету (и дождись одобрения)!")
    
    if user_id not in swiped_db: swiped_db[user_id] = []
    
    available = [uid for uid in users_db if uid != user_id and uid not in swiped_db[user_id]]
    
    if not available:
        return await bot.send_message(chat_id, "Анкеты закончились! Жди новых лицеистов.", reply_markup=get_main_kb())
        
    target_id = random.choice(available)
    target = users_db[target_id]
    
    # Добавили кнопку Ауры для чужих анкет
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{target_id}"),
         InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dis_{target_id}")],
        [InlineKeyboardButton(text="⏭ Скип", callback_data=f"skip_{target_id}"),
         InlineKeyboardButton(text="🔮 Аура", callback_data=f"aura_{target_id}")], # <--- Новая кнопка
        [InlineKeyboardButton(text="🚩 Пожаловаться", callback_data=f"report_{target_id}")]
    ])
    
    await bot.send_photo(
        chat_id=chat_id,
        photo=target['photo'],
        caption=f"<b>{target['name']}, {target['age']}</b> ({target['gender']})\n🎓 Класс: {target['grade']}\n🎯 Цель: {target['goal']}\n\n{target['about']}",
        reply_markup=kb, parse_mode="HTML"
    )

@dp.message(F.text == "🔍 Искать пару")
async def search_profile(message: types.Message):
    await message.answer("Режим поиска активирован. Нажми «Лайк», «Дизлайк», «Скип» или «Аура» под анкетой. Чтобы выйти, нажми кнопку ниже 👇", reply_markup=get_search_kb())
    await show_next_profile(message.chat.id, message.from_user.id)

@dp.callback_query(F.data.startswith("like_"))
async def process_like(callback: CallbackQuery):
    my_id = callback.from_user.id
    target_id = int(callback.data.split("_")[1])
    
    if my_id not in swiped_db: swiped_db[my_id] = []
    swiped_db[my_id].append(target_id)
    
    if my_id not in likes_db: likes_db[my_id] = []
    likes_db[my_id].append(target_id)
    
    if target_id in likes_db and my_id in likes_db[target_id]:
        await callback.message.edit_caption(caption=get_text(my_id, "match"))
        kb_share = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🤝 Показать мой @username", callback_data=f"share_{target_id}")]])
        try: await bot.send_message(target_id, get_text(target_id, "match") + "\n\nХочешь пообщаться? Жми кнопку!", reply_markup=kb_share)
        except: pass
        await callback.message.answer("Хочешь пообщаться? Жми кнопку!", reply_markup=kb_share)
    else:
        await callback.message.edit_caption(caption="Ты лайкнул анкету! 😉")
    
    await callback.answer()
    await asyncio.sleep(0.5)
    await show_next_profile(callback.message.chat.id, my_id)

@dp.callback_query(F.data.startswith("dis_"))
async def process_dislike(callback: CallbackQuery):
    my_id = callback.from_user.id
    target_id = int(callback.data.split("_")[1])
    
    if my_id not in swiped_db: swiped_db[my_id] = []
    swiped_db[my_id].append(target_id)
    
    await callback.message.edit_caption(caption="Дизлайк. Идем дальше! 👎")
    await callback.answer()
    
    await asyncio.sleep(0.5)
    await show_next_profile(callback.message.chat.id, my_id)

@dp.callback_query(F.data.startswith("skip_"))
async def process_skip(callback: CallbackQuery):
    my_id = callback.from_user.id
    target_id = int(callback.data.split("_")[1])
    
    if my_id not in swiped_db: swiped_db[my_id] = []
    swiped_db[my_id].append(target_id)
    
    await callback.message.edit_caption(caption="⏭ Анкета пропущена.")
    await callback.answer()
    
    await asyncio.sleep(0.5)
    await show_next_profile(callback.message.chat.id, my_id)

@dp.callback_query(F.data.startswith("share_"))
async def process_share_username(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    my_id = callback.from_user.id
    if not callback.from_user.username:
        return await callback.answer("У тебя нет @username в настройках Телеграма!", show_alert=True)
    my_name = users_db.get(my_id, {}).get("name", "Кто-то")
    try:
        await bot.send_message(target_id, f"🎉 <b>У вас мэтч!</b>\n\nПользователь <b>{my_name}</b> хочет пообщаться.\nЕго юзернейм: @{callback.from_user.username}", parse_mode="HTML")
        await callback.message.edit_text("✅ Твой юзернейм отправлен партнеру!")
    except: pass
    await callback.answer()

async def main():
    print("АлкоRedБот (с Аурой для всех) запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
