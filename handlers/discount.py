from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import save_user_data, log_funnel_step
from states import GameStates
from config import INSTAGRAM_ACCOUNT

router = Router()


@router.callback_query(F.data == "want_discount")
async def want_discount(callback: CallbackQuery, state: FSMContext):
    """Обработка запроса скидки"""
    await callback.answer()
    await log_funnel_step(callback.from_user.id, "discount_requested")
    
    text = "📱 Напиши свой ник в Instagram, чтобы мы могли проверить твою отметку:"
    await callback.message.answer(text)
    await state.set_state(GameStates.waiting_for_instagram_nick)


@router.message(GameStates.waiting_for_instagram_nick)
async def process_instagram_nick(message: Message, state: FSMContext):
    """Обработка ника в Instagram"""
    instagram_nick = message.text.strip()
    await save_user_data(message.from_user.id, instagram_nick=instagram_nick, discount_claimed=1)
    await log_funnel_step(message.from_user.id, "discount_claimed")
    
    text = """Ура! 🎉
Скидка 15% закреплена за тобой.
Напиши в аккаунт Нармины, чтобы получить подарок и выбрать удобную дату игры ♥️"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти в Instagram", url=f"https://instagram.com/{INSTAGRAM_ACCOUNT.replace('@', '')}")]
    ])
    
    await message.answer(text, reply_markup=keyboard)
    await state.clear()

