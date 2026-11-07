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

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
PRIMARY_ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 

SECRET_ADMIN_CODE = "Ризван РЭУ Чечня"
ADMIN_IDS = {PRIMARY_ADMIN_ID} 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

users_db = {}      
likes_db = {}      
swiped_db = {}     
user_bot_style = {} 
messages_map = {}

# Состояния (FSM)
class ProfileForm(StatesGroup):
    name = State()
    age = State()
    about = State()
    goal = State()
    photo = State()

class AdminForm(StatesGroup):
    waiting_for_code = State()

class SupportForm(StatesGroup):
    waiting_for_msg = State()

# --- ТЕКСТЫ ---
TEXTS = {
    "standard": {
        "start": "Йоу, {name}! Я Лицейский Мэтч. Готов найти пару?",
        "ask_name": "Погнали! Как тебя зовут?",
        "ask_age": "Сколько тебе лет?",
        "ask_about": "Расскажи пару слов о себе:",
        "ask_photo": "Кинь свою фотку для анкеты (отправь как фото):",
        "done": "Анкета готова! 🎉",
        "match": "🎉 МЭТЧ! Вы понравились друг другу!"
    },
    "flirt": {
        "start": "Приветик, {name} 😘 Я твой личный сваха-бот. Погнали искать любовь?",
        "ask_name": "Как зовут моего пупсика?",
        "ask_age": "Сколько тебе годиков, конфетка?",
        "ask_about": "Расскажи, чем ты так цепляешь людей? 😏",
        "ask_photo": "А теперь скинь свою самую сочную аватарку 💋",
        "done": "Ммм, выглядишь потрясно! Анкета готова 🥵",
        "match": "🔥 МЭТЧ! Пупсик, вы созданы друг для друга!"
    },
    "alt": {
        "start": "Йоу, {name} 🖤 Я Лицейский Мэтч. Тут не кринжуют, а ищут свою родственную душу.",
        "ask_name": "Как тебя величать, дед инсайд?",
        "ask_age": "Сколько тебе лет?",
        "ask_about": "Напиши что-нибудь эдакое. Че ты за вайб?",
        "ask_photo": "Закинь фотку, где ты максимально на стиле. Жду.",
        "done": "Окей, база. Твоя анкета в деле 🕸",
        "match": "💀 МЭТЧ! Вы нашли друг друга в этом жестоком мире."
    },
    "en": {
        "start": "Yo {name}! I'm the Lyceum Match bot. Ready to find a date?",
        "ask_name": "Let's go! What's your name?",
        "ask_age": "How old are you?",
        "ask_about": "Tell me a bit about yourself:",
        "ask_photo": "Drop your best pic for the profile:",
        "done": "Profile is ready! 🎉",
        "match": "🎉 IT'S A MATCH! You liked each other!"
    },
    "ky": {
        "start": "Салам, {name}! Мен Лицей Мэтч ботумун. Жуп табабызбы?",
        "ask_name": "Атың ким?",
        "ask_age": "Жашың нечеде?",
        "ask_about": "Өзүң жөнүндө эки ооз сүйлөп бер:",
        "ask_photo": "Анкетаңа сүрөтүңдү жөнөт:",
        "done": "Анкета даяр! 🎉",
        "match": "🎉 МЭТЧ! Тил табыштыңар!"
    }
}

def get_text(user_id, key, **kwargs):
    style = user_bot_style.get(user_id, "standard")
    text = TEXTS[style].get(key, TEXTS["standard"].get(key, ""))
    return text.format(**kwargs)

def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📝 Создать/Изменить анкету"))
    builder.add(KeyboardButton(text="🔍 Искать пару"))
    builder.add(KeyboardButton(text="👤 Мой профиль"))
    builder.add(KeyboardButton(text="🗑 Удалить профиль"))
    builder.add(KeyboardButton(text="⚙️ Сменить стиль бота"))
    builder.add(KeyboardButton(text="📩 Связь с админом"))
    builder.add(KeyboardButton(text="👑 Я админ")) 
    return builder.as_markup(resize_keyboard=True)

def get_style_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😎 Стандарт", callback_data="set_standard")],
        [InlineKeyboardButton(text="😘 Флирт", callback_data="set_flirt")],
        [InlineKeyboardButton(text="🖤 Альтушка", callback_data="set_alt")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_en")],
        [InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="set_ky")]
    ])
    return kb

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id not in user_bot_style:
        await message.answer("Выбери, как со мной общаться:", reply_markup=get_style_kb())
    else:
        await message.answer(
            get_text(message.from_user.id, "start", name=message.from_user.first_name),
            reply_markup=get_main_kb()
        )

# --- ВХОД В АДМИНКУ ---
@dp.message(F.text == "👑 Я админ")
async def start_admin_login(message: types.Message, state: FSMContext):
    await message.answer("Введи секретный код доступа:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdminForm.waiting_for_code)

@dp.message(AdminForm.waiting_for_code)
async def process_admin_code(message: types.Message, state: FSMContext):
    if message.text.strip() == SECRET_ADMIN_CODE:
        ADMIN_IDS.add(message.from_user.id)
        await message.answer("✅ Код верный! Теперь тебе будут приходить сообщения из кнопки 'Связь с админом'.", reply_markup=get_main_kb())
    else:
        await message.answer("❌ Неверный код. Попробуй еще раз или нажми /start.", reply_markup=get_main_kb())
    await state.clear()

@dp.message(F.text == "⚙️ Сменить стиль бота")
async def change_style_cmd(message: types.Message):
    await message.answer("Выбери новый стиль общения:", reply_markup=get_style_kb())

@dp.callback_query(F.data.startswith("set_"))
async def set_style(callback: CallbackQuery):
    style = callback.data.split("_")[1]
    user_bot_style[callback.from_user.id] = style
    await callback.message.delete()
    await callback.message.answer(
        get_text(callback.from_user.id, "start", name=callback.from_user.first_name),
        reply_markup=get_main_kb()
    )
    await callback.answer()

# --- СВЯЗЬ С АДМИНОМ ---
@dp.message(F.text == "📩 Связь с админом")
async def start_support(message: types.Message, state: FSMContext):
    await message.answer(
        "📩 <b>Анонимная связь с админами</b>\n\n"
        "Пиши сюда любые вопросы! Это может быть вопрос по учебе, просьба о помощи, жалоба на баг или просто предложение.\n"
        "Все строго анонимно, мы не увидим твое имя.",
        reply_markup=ReplyKeyboardRemove(), parse_mode="HTML"
    )
    await state.set_state(SupportForm.waiting_for_msg)

@dp.message(SupportForm.waiting_for_msg, F.chat.type == "private")
async def forward_support_to_admin(message: types.Message, state: FSMContext):
    success = False
    for admin_id in ADMIN_IDS:
        try:
            sent_msg = await bot.copy_message(chat_id=admin_id, from_chat_id=message.chat.id, message_id=message.message_id)
            messages_map[sent_msg.message_id] = message.from_user.id
            success = True
        except Exception:
            pass 
    if success:
        await message.answer("Твое сообщение отправлено админам! Жди ответа.", reply_markup=get_main_kb())
    else:
        await message.answer("Не удалось отправить. Возможно, админы недоступны.", reply_markup=get_main_kb())
    await state.clear()

@dp.message(F.chat.type == "private", F.reply_to_message)
async def admin_reply_to_support(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return 
    original_msg_id = message.reply_to_message.message_id
    if original_msg_id in messages_map:
        target_user_id = messages_map[original_msg_id]
        try:
            await bot.copy_message(chat_id=target_user_id, from_chat_id=message.from_user.id, message_id=message.message_id)
            await message.answer("Ответ отправлен пользователю! ✅")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

# --- СОЗДАНИЕ АНКЕТЫ ---
@dp.message(F.text == "📝 Создать/Изменить анкету")
async def start_create(message: types.Message, state: FSMContext):
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
    await message.answer(get_text(message.from_user.id, "ask_about"))
    await state.set_state(ProfileForm.about)

@dp.message(ProfileForm.about)
async def process_about(message: types.Message, state: FSMContext):
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
    photo_id = message.photo[-1].file_id
    user_data = await state.get_data()
    users_db[message.from_user.id] = {
        "name": user_data['name'], "age": user_data['age'],
        "about": user_data['about'], "goal": user_data['goal'],
        "photo": photo_id
    }
    swiped_db[message.from_user.id] = [] 
    await message.answer(get_text(message.from_user.id, "done"), reply_markup=get_main_kb())
    await state.clear()

# --- ПРОФИЛЬ И УДАЛЕНИЕ ---
@dp.message(F.text == "👤 Мой профиль")
async def my_profile(message: types.Message):
    data = users_db.get(message.from_user.id)
    if not data:
        return await message.answer("Ты пока не создал анкету!")
    await message.answer_photo(
        photo=data['photo'],
        caption=f"👤 <b>Твоя анкета:</b>\n\n<b>Имя:</b> {data['name']}\n<b>Возраст:</b> {data['age']}\n<b>Цель:</b> {data['goal']}\n<b>О себе:</b> {data['about']}",
        parse_mode="HTML"
    )

@dp.message(F.text == "🗑 Удалить профиль")
async def delete_profile(message: types.Message):
    if message.from_user.id in users_db:
        del users_db[message.from_user.id]
        await message.answer("Твоя анкета удалена.", reply_markup=get_main_kb())

# --- СВАЙПЫ И МЭТЧИ ---
@dp.message(F.text == "🔍 Искать пару")
async def search_profile(message: types.Message):
    my_id = message.from_user.id
    if my_id not in users_db:
        return await message.answer("Сначала создай анкету!")
    if my_id not in swiped_db: swiped_db[my_id] = []
    available = [uid for uid in users_db if uid != my_id and uid not in swiped_db[my_id]]
    if not available:
        return await message.answer("Анкеты закончились! Жди других.")
    target_id = random.choice(available)
    target = users_db[target_id]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{target_id}"),
         InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dis_{target_id}")]
    ])
    await message.answer_photo(
        photo=target['photo'],
        caption=f"<b>{target['name']}, {target['age']}</b>\n🎯 {target['goal']}\n\n{target['about']}",
        reply_markup=kb, parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("like_"))
async def process_like(callback: CallbackQuery):
    my_id = callback.from_user.id
    target_id = int(callback.data.split("_")[1])
    
    swiped_db[my_id].append(target_id)
    if my_id not in likes_db: likes_db[my_id] = []
    likes_db[my_id].append(target_id)
    
    if target_id in likes_db and my_id in likes_db[target_id]:
        # МЭТЧ!
        await callback.message.edit_caption(caption=get_text(my_id, "match"))
        
        # Кнопка "Поделиться юзернеймом" для обоих
        kb_share = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤝 Показать мой @username", callback_data=f"share_{target_id}")]
        ])
        
        try:
            await bot.send_message(
                target_id, 
                get_text(target_id, "match") + "\n\nХочешь пообщаться? Нажми кнопку ниже, чтобы показать свой юзернейм!",
                reply_markup=kb_share
            )
        except: pass
        
        await callback.message.answer(
            "Хочешь пообщаться? Нажми кнопку ниже, чтобы показать свой юзернейм!",
            reply_markup=kb_share
        )
    else:
        await callback.message.edit_caption(caption="Ты лайкнул анкету! 😉")
    
    await callback.answer()

@dp.callback_query(F.data.startswith("share_"))
async def process_share_username(callback: CallbackQuery):
    target_id = int(callback.data.split("_")[1])
    my_id = callback.from_user.id
    
    # Проверяем, есть ли юзернейм
    if not callback.from_user.username:
        await callback.answer("У тебя нет юзернейма в Телеграме! Зайди в настройки профиля, создай его и попробуй снова.", show_alert=True)
        return
        
    my_name = users_db.get(my_id, {}).get("name", "Кто-то")
    my_username = f"@{callback.from_user.username}"
    
    try:
        await bot.send_message(
            target_id, 
            f"🎉 <b>У вас взаимная симпатия!</b>\n\n"
            f"Пользователь <b>{my_name}</b> хочет с тобой пообщаться.\n"
            f"Вот его юзернейм: {my_username}\n"
            f"Скорее пиши ему в личку! 😉",
            parse_mode="HTML"
        )
        await callback.message.edit_text("✅ Твой юзернейм отправлен партнеру! Жди сообщения.")
    except Exception as e:
        await callback.message.edit_text("Не удалось отправить. Возможно, пользователь заблокировал бота.")
    
    await callback.answer()

@dp.callback_query(F.data.startswith("dis_"))
async def process_dislike(callback: CallbackQuery):
    my_id = callback.from_user.id
    target_id = int(callback.data.split("_")[1])
    swiped_db[my_id].append(target_id)
    await callback.message.edit_caption(caption="Дизлайк. Идем дальше! 👎")
    await callback.answer()

async def main():
    print("Лицейский Мэтч (с обменом контактами) запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
