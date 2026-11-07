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
ADMIN_IDS = {PRIMARY_ADMIN_ID} 

# Базы данных
BANNED_WORDS = ["хуй", "пизд", "бля", "еба", "ебал", "секс", "порно", "гандон", "долбоеб"]
banned_users = set() # Тут храним ID забаненных фейков

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
    "ky": {
        "start": "Салам, {name}! Мен АлкоRedБотмун. Жуп табабызбы?",
        "ask_name": "Атың ким?",
        "ask_age": "Жашың нечеде?",
        "ask_photo": "Анкетаңа сүрөтүңдү жөнөт:",
        "done": "Анкета текшерүүгө жөнөтүлдү! 🕵️‍♂️",
        "match": "🎉 МЭТЧ! Тил табыштыңар!"
    }
}

def get_text(user_id, key, **kwargs):
    style = user_bot_style.get(user_id, "standard")
    text = TEXTS[style].get(key, TEXTS["standard"].get(key, ""))
    return text.format(**kwargs)

# --- КЛАВИАТУРЫ ---
def get_start_kb():
    """Меню на 3 кнопки для самого начала"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📩 Связь с админом"))
    builder.add(KeyboardButton(text="👑 Я админ"))
    builder.add(KeyboardButton(text="🚀 В главное меню"))
    return builder.as_markup(resize_keyboard=True)

def get_main_kb():
    """Полное меню для работы с анкетой"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📝 Создать/Изменить анкету"))
    builder.add(KeyboardButton(text="🔍 Искать пару"))
    builder.add(KeyboardButton(text="👤 Мой профиль"))
    builder.add(KeyboardButton(text="🗑 Удалить профиль"))
    builder.add(KeyboardButton(text="⚙️ Сменить стиль бота"))
    return builder.as_markup(resize_keyboard=True)

def get_style_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😎 Стандарт", callback_data="set_standard")],
        [InlineKeyboardButton(text="😘 Флирт", callback_data="set_flirt")],
        [InlineKeyboardButton(text="🖤 Альтушка", callback_data="set_alt")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_en")],
        [InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="set_ky")]
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
async def go_to_main_menu(message: types.Message):
    await message.answer("Твой личный бармен готов! Выбирай действие:", reply_markup=get_main_kb())

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
    await message.answer("Твое сообщение отправлено админам!", reply_markup=get_start_kb())
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

# --- ЛЕНТА (ИСПРАВЛЕНА АВТОЗАГРУЗКА) ---
async def show_next_profile(chat_id, user_id):
    if user_id not in users_db:
        return await bot.send_message(chat_id, "Сначала создай анкету (и дождись одобрения)!")
    
    if user_id not in swiped_db: swiped_db[user_id] = []
    
    # Исключаем себя и тех, кого уже свайпнули
    available = [uid for uid in users_db if uid != user_id and uid not in swiped_db[user_id]]
    
    if not available:
        return await bot.send_message(chat_id, "Анкеты закончились! Жди новых лицеистов. Ты просмотрел всех.")
        
    target_id = random.choice(available)
    target = users_db[target_id]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{target_id}"),
         InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dis_{target_id}")],
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
    # АВТОМАТИЧЕСКИЙ ПЕРЕХОД К СЛЕДУЮЩЕЙ АНКЕТЕ
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
    
    # АВТОМАТИЧЕСКИЙ ПЕРЕХОД К СЛЕДУЮЩЕЙ АНКЕТЕ
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

# --- СИСТЕМА ЖАЛОБ И БАНОВ ---
@dp.callback_query(F.data.startswith("report_"))
async def process_report(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    reporter_id = callback.from_user.id
    
    kb_ban = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Забанить фейк", callback_data=f"ban_{target_id}")]
    ])
    
    report_text = f"🚨 <b>ЖАЛОБА НА АНКЕТУ!</b>\n\nКто-то нажал на кнопку жалобы. Проверь этого пользователя.\nID нарушителя: <code>{target_id}</code>\n"
    if target_id in users_db:
        report_text += f"Имя: {users_db[target_id]['name']}"
    
    for admin_id in ADMIN_IDS:
        try: await bot.send_message(admin_id, report_text, reply_markup=kb_ban, parse_mode="HTML")
        except: pass
    
    await callback.answer("Жалоба отправлена админам! Спасибо, мы разберемся.", show_alert=True)

@dp.callback_query(F.data.startswith("ban_"))
async def process_ban(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    
    if target_id in users_db:
        del users_db[target_id]
    
    banned_users.add(target_id)
    
    await callback.message.edit_text("✅ Профиль забанен и удален из поиска.")
    try:
        await bot.send_message(target_id, "❌ Твой профиль был забанен админами из-за жалоб (фейк или нарушение правил).")
    except: pass
    await callback.answer()

async def main():
    print("АлкоRedБот (Финальная версия с жалобами) запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
