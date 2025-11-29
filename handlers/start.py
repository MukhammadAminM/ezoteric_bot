from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import log_funnel_step
from states import GameStates

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    await state.clear()
    
    welcome_text = """✨ Добро пожаловать в мини-игру "Ты и Вселенная".
Сегодня ты сможешь прикоснуться к энергии своего будущего и увидеть подсказки, которые Вселенная приготовила лично для тебя.

Эта игра поможет заглянуть внутрь себя, понять свои истинные желания и сделать первый шаг к тому, что ты хочешь привлечь в свою жизнь."""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Начать игру", callback_data="start_game")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard)
    await log_funnel_step(message.from_user.id, "start")


@router.callback_query(F.data == "start_game")
async def start_game(callback, state: FSMContext):
    """Начало игры - запрос имени"""
    await callback.answer()
    await log_funnel_step(callback.from_user.id, "game_started")
    
    text = "👤 Напиши своё имя и фамилию или ник в Instagram/Telegram — то, что тебе комфортнее."
    await callback.message.answer(text)
    await state.set_state(GameStates.waiting_for_name)

