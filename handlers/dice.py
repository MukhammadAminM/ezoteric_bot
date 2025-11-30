import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import save_user_data, log_funnel_step
from states import GameStates

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "roll_dice")
async def roll_dice(callback: CallbackQuery, state: FSMContext):
    """Обработка броска кубика"""
    logger.info(f"Нажата кнопка roll_dice, текущее состояние: {await state.get_state()}")
    await callback.answer()
    
    # Отправляем анимированный кубик
    dice_message = await callback.message.answer_dice()
    dice_value = dice_message.dice.value
    logger.info(f"Кубик отправлен, message_id={dice_message.message_id}, chat_id={dice_message.chat.id}, value={dice_value}")
    logger.info(f"Результат кубика: {dice_value}, ждем завершения анимации...")
    
    # Ждем завершения анимации (около 4 секунд)
    await asyncio.sleep(4)
    logger.info(f"Анимация завершена, обрабатываем результат: {dice_value}")
    
    # Обрабатываем результат
    await handle_dice_result(callback.message, state, dice_value)


async def handle_dice_result(message: Message, state: FSMContext, dice_value: int):
    """Обработка результата броска кубика"""
    await save_user_data(message.from_user.id, dice_result=dice_value)
    await log_funnel_step(message.from_user.id, f"dice_rolled_{dice_value}")
    
    # Получаем количество попыток
    data = await state.get_data()
    attempts = data.get("dice_attempts", 0) + 1
    await state.update_data(dice_attempts=attempts)
    
    if dice_value == 1:
        # Успех - переходим к выбору карты
        text = """✨ Я тебя поздравляю!
Твоё желание действительно искреннее, и ты готова принимать подсказки Вселенной 🔮

Теперь выбери карту."""
        
        # Сразу отправляем выбор карты
        from handlers.cards import show_card_with_pagination
        from cards import get_all_cards
        
        all_cards = get_all_cards()
        if not all_cards:
            await message.answer("❌ Карты не найдены!")
            return
        
        await state.update_data(
            cards_list=all_cards,
            current_card_index=0
        )
        
        await show_card_with_pagination(message, state, 0)
        await state.set_state(GameStates.waiting_for_card_selection)
    else:
        # Неудача
        if attempts >= 2:
            # Максимум попыток достигнут
            text = """🤔 Кажется, твоё желание немного спрятано глубже. Возможно, ты выразила его не полностью или не так, как чувствуешь…
Но давай продолжим с тем, что есть. Иногда Вселенная показывает нам путь не сразу ✨"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➡️ Продолжить", callback_data="continue_anyway")]
            ])
            
            sent_message = await message.answer(text, reply_markup=keyboard)
            # Сохраняем message_id для последующего удаления
            await state.update_data(retry_message_id=sent_message.message_id)
            # Не устанавливаем состояние, чтобы обработчик continue_anyway мог сработать
        else:
            text = """🤔 Кажется, твоё желание немного спрятано глубже. Возможно, ты выразила его не полностью или не так, как чувствуешь…
Хочешь попробовать ещё раз? 🔄"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Да, попробовать снова", callback_data="retry_dice")],
                [InlineKeyboardButton(text="➡️ Нет, оставить как есть", callback_data="continue_anyway")]
            ])
            
            sent_message = await message.answer(text, reply_markup=keyboard)
            # Сохраняем message_id для последующего редактирования
            await state.update_data(retry_message_id=sent_message.message_id)
            await state.set_state(GameStates.waiting_for_retry_decision)


@router.callback_query(F.data == "retry_dice", GameStates.waiting_for_retry_decision)
async def retry_dice(callback: CallbackQuery, state: FSMContext):
    """Повторный бросок кубика"""
    await callback.answer()
    
    text = """✨ Отлично! Давай попробуем ещё раз.
Нажми на кнопку, чтобы бросить кубик 🎲"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Кинуть кубик", callback_data="roll_dice")]
    ])
    
    # Редактируем сообщение вместо отправки нового
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except:
        # Если не получилось отредактировать, отправляем новое
        await callback.message.answer(text, reply_markup=keyboard)
    
    await state.set_state(GameStates.waiting_for_dice)


@router.callback_query(F.data == "continue_anyway")
async def continue_anyway(callback: CallbackQuery, state: FSMContext):
    """Продолжить несмотря на неудачу"""
    logger.info(f"=== ОБРАБОТЧИК continue_anyway ВЫЗВАН ===")
    logger.info(f"Нажата кнопка continue_anyway, текущее состояние: {await state.get_state()}")
    logger.info(f"Callback data: {callback.data}")
    await callback.answer()
    await log_funnel_step(callback.from_user.id, "continued_anyway")
    
    # Удаляем сообщение с кнопкой
    try:
        data = await state.get_data()
        retry_msg_id = data.get("retry_message_id")
        if retry_msg_id:
            # Удаляем сообщение с кнопками
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=retry_msg_id
            )
        else:
            # Если нет сохраненного message_id, удаляем текущее сообщение
            await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")
    
    # Отправляем сообщение о выборе карты
    text = "🃏 Теперь выбери одну из карт:"
    await callback.message.answer(text)
    
    # Затем отправляем карты
    from handlers.cards import show_card_with_pagination
    from cards import get_all_cards
    
    logger.info("Получаем список карт...")
    all_cards = get_all_cards()
    logger.info(f"Найдено карт: {len(all_cards) if all_cards else 0}")
    
    if not all_cards:
        logger.warning("Карты не найдены!")
        await callback.message.answer("❌ Карты не найдены!")
        return
    
    # Сохраняем список карт и начинаем с первой (индекс 0)
    await state.update_data(
        cards_list=all_cards,
        current_card_index=0
    )
    
    logger.info("Отправляем карту с пагинацией...")
    # Отправляем первую карту с кнопками навигации
    # Создаем новое сообщение, так как callback.message может не иметь photo
    try:
        await show_card_with_pagination(callback.message, state, 0)
        logger.info("Карта отправлена через show_card_with_pagination")
    except Exception as e:
        logger.error(f"Ошибка при отправке карты: {e}")
        # Если не получилось, отправляем напрямую
        from aiogram.types import FSInputFile
        from cards import get_card_path
        import os
        
        first_card = all_cards[0]
        card_path = get_card_path(first_card)
        if card_path and os.path.exists(card_path):
            photo = FSInputFile(card_path)
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Предыдущая", callback_data="card_prev_0")],
                [InlineKeyboardButton(text="1/3", callback_data="card_number")],
                [InlineKeyboardButton(text="Следующая ▶️", callback_data="card_next_0")],
                [InlineKeyboardButton(text="Выбрать эту карту", callback_data="card_select_0")]
            ])
            
            await callback.message.answer_photo(photo, reply_markup=keyboard)
            logger.info("Карта отправлена напрямую")
    
    await state.set_state(GameStates.waiting_for_card_selection)
    logger.info("Состояние изменено на waiting_for_card_selection")

