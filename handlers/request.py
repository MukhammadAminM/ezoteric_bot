from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import save_user_data, log_funnel_step
from states import GameStates

router = Router()


@router.message(GameStates.waiting_for_request)
async def process_request(message: Message, state: FSMContext):
    """Обработка запроса пользователя"""
    request = message.text.strip()
    await save_user_data(message.from_user.id, request=request)
    await log_funnel_step(message.from_user.id, "request_collected")
    
    text = """✨ Отлично! Теперь давай посмотрим, насколько искренним получилось твоё желание.
Нажми на кнопку, чтобы бросить кубик 🎲"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Кинуть кубик", callback_data="roll_dice")]
    ])
    
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(GameStates.waiting_for_dice)

