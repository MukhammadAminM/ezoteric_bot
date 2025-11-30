import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from database import save_user_data, save_answer, log_funnel_step
from states import GameStates
from cards import get_card_path, get_all_cards, get_gift_card_path, get_all_gift_cards

router = Router()
logger = logging.getLogger(__name__)


async def show_card_with_pagination(message: Message, state: FSMContext, card_index: int):
    """Показать карту с кнопками пагинации"""
    data = await state.get_data()
    cards_list = data.get("cards_list", [])
    
    if not cards_list or card_index < 0 or card_index >= len(cards_list):
        return
    
    card_filename = cards_list[card_index]
    card_path = get_card_path(card_filename)
    
    if not card_path or not os.path.exists(card_path):
        return
    
    photo = FSInputFile(card_path)
    
    # Создаем кнопки навигации
    keyboard_buttons = []
    
    # Кнопки навигации с номером карты в центре
    nav_buttons = []
    if len(cards_list) > 1:
        if card_index > 0:
            nav_buttons.append(InlineKeyboardButton(text="◀️ Предыдущая", callback_data=f"card_prev_{card_index}"))
        
        # Номер карты в центре (неактивная кнопка)
        nav_buttons.append(InlineKeyboardButton(text=f"{card_index + 1}/{len(cards_list)}", callback_data="card_number"))
        
        if card_index < len(cards_list) - 1:
            nav_buttons.append(InlineKeyboardButton(text="Следующая ▶️", callback_data=f"card_next_{card_index}"))
        
        if nav_buttons:
            keyboard_buttons.append(nav_buttons)
    
    # Кнопка выбора карты
    keyboard_buttons.append([InlineKeyboardButton(text="Выбрать эту карту", callback_data=f"card_select_{card_index}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем или обновляем сообщение (без caption)
    if message.photo:
        # Обновляем существующее сообщение
        media = InputMediaPhoto(media=photo)
        await message.edit_media(media=media, reply_markup=keyboard)
    else:
        # Отправляем новое сообщение
        await message.answer_photo(photo, reply_markup=keyboard)


# Обработчики навигации по картам
@router.callback_query(F.data.startswith("card_prev_"))
async def card_previous(callback: CallbackQuery, state: FSMContext):
    """Переход к предыдущей карте"""
    await callback.answer()
    card_index = int(callback.data.split("_")[-1])
    new_index = max(0, card_index - 1)
    await state.update_data(current_card_index=new_index)
    await show_card_with_pagination(callback.message, state, new_index)


@router.callback_query(F.data.startswith("card_next_"))
async def card_next(callback: CallbackQuery, state: FSMContext):
    """Переход к следующей карте"""
    await callback.answer()
    data = await state.get_data()
    cards_list = data.get("cards_list", [])
    card_index = int(callback.data.split("_")[-1])
    new_index = min(len(cards_list) - 1, card_index + 1)
    await state.update_data(current_card_index=new_index)
    await show_card_with_pagination(callback.message, state, new_index)


@router.callback_query(F.data == "card_number")
async def card_number_click(callback: CallbackQuery):
    """Обработка клика на номер карты (ничего не делаем)"""
    await callback.answer()


@router.callback_query(F.data.startswith("card_select_"))
async def card_select(callback: CallbackQuery, state: FSMContext):
    """Выбор карты"""
    await callback.answer("Карта выбрана!")
    
    card_index = int(callback.data.split("_")[-1])
    data = await state.get_data()
    cards_list = data.get("cards_list", [])
    
    if 0 <= card_index < len(cards_list):
        selected_card = cards_list[card_index]
        await save_user_data(callback.from_user.id, card_1=selected_card)
        await log_funnel_step(callback.from_user.id, "card_selected")
        
        # Переход к первому вопросу
        text = "👁️ Напиши, что ты видишь на этой карте. Просто опиши изображение."
        await callback.message.answer(text)
        await state.set_state(GameStates.waiting_for_card_description)


@router.message(GameStates.waiting_for_card_description)
async def process_card_description(message: Message, state: FSMContext):
    """Обработка описания карты"""
    description = message.text.strip()
    await save_answer(message.from_user.id, 1, description)
    await log_funnel_step(message.from_user.id, "card_description")
    
    text = "💭 Какие эмоции и чувства у тебя вызывает эта карта? Опиши честно."
    await message.answer(text)
    await state.set_state(GameStates.waiting_for_card_emotions)


@router.message(GameStates.waiting_for_card_emotions)
async def process_card_emotions(message: Message, state: FSMContext):
    """Обработка эмоций от карты"""
    emotions = message.text.strip()
    await save_answer(message.from_user.id, 2, emotions)
    await log_funnel_step(message.from_user.id, "card_emotions")
    
    text = "🤔 Как ты думаешь, зачем тебе выпала именно эта карта? Чтобы что?"
    await message.answer(text)
    await state.set_state(GameStates.waiting_for_card_purpose)


@router.message(GameStates.waiting_for_card_purpose)
async def process_card_purpose(message: Message, state: FSMContext):
    """Обработка цели карты"""
    purpose = message.text.strip()
    await save_answer(message.from_user.id, 3, purpose)
    await log_funnel_step(message.from_user.id, "card_purpose")
    
    text = """🔍 Посмотри ещё раз на карту.
Как ты думаешь, что тебе нужно улучшить в себе, чтобы твоё желание осуществилось?

Ответ приходит обычно первым, что всплывает в голове."""
    await message.answer(text)
    await state.set_state(GameStates.waiting_for_self_improvement)


@router.message(GameStates.waiting_for_self_improvement)
async def process_self_improvement(message: Message, state: FSMContext):
    """Обработка ответа о самосовершенствовании"""
    answer = message.text.strip().lower()
    
    # Проверяем на "не знаю"
    if any(phrase in answer for phrase in ["не знаю", "не понимаю", "нет идей", "не знаю", "не понимаю"]):
        # Ветка поддержки
        text = """🧙‍♀️ Представь, что ты сама — мудрый наставник для этой карты.
Какой совет ты бы дала ей, чтобы она помогла тебе исполнить твоё желание?

Запиши в формате:

…
…
…"""
        await message.answer(text)
        await state.set_state(GameStates.waiting_for_advice)
    else:
        # Обычный ответ
        await save_answer(message.from_user.id, 4, message.text.strip())
        await log_funnel_step(message.from_user.id, "self_improvement")
        await process_final_advice(message, state)


async def process_final_advice(message: Message, state: FSMContext):
    """Обработка финального совета"""
    text = """✨ Отлично!
Сейчас ты написала три варианта того, что может помочь тебе приблизиться к своему желанию.
Если ты действительно сделаешь это для себя — Вселенная обязательно наградит тебя результатом 🙌"""
    
    await message.answer(text)
    
    # Переход к подаркам
    gift_text = """Теперь выбери свой подарок в игре 🎁
Выбери две карты."""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Начать выбор подарков", callback_data="start_gift_selection")]
    ])
    
    sent_message = await message.answer(gift_text, reply_markup=keyboard)
    # Сохраняем message_id для последующего редактирования
    await state.update_data(gift_start_message_id=sent_message.message_id)
    await state.set_state(GameStates.waiting_for_gift_start)


@router.message(GameStates.waiting_for_advice)
async def process_advice(message: Message, state: FSMContext):
    """Обработка совета в формате списка"""
    advice = message.text.strip()
    await save_answer(message.from_user.id, 4, advice)
    await log_funnel_step(message.from_user.id, "advice_given")
    
    await process_final_advice(message, state)


@router.callback_query(F.data == "start_gift_selection", GameStates.waiting_for_gift_start)
async def start_gift_selection(callback: CallbackQuery, state: FSMContext):
    """Начало выбора подарков"""
    await callback.answer()
    
    # Редактируем сообщение, убирая кнопку и сохраняем message_id
    try:
        edited_message = await callback.message.edit_text("🎁 Выбери первую карту подарка:", reply_markup=None)
        gift_start_text_message_id = edited_message.message_id
    except:
        gift_start_text_message_id = None
    
    # Получаем все карты подарков из папки gift_images
    all_cards = get_all_gift_cards()
    if not all_cards:
        await callback.message.answer("❌ Карты подарков не найдены!")
        return
    
    # Сохраняем список карт и начинаем с первой карты
    await state.update_data(
        gift_cards_list=all_cards,
        current_gift_card_index=0,
        gift_type="gift_card_1",
        gift_card_1_selected=False,
        gift_card_2_selected=False,
        gift_card_1_message_id=None,
        gift_card_2_message_id=None,
        gift_start_text_message_id=gift_start_text_message_id
    )
    
    # Отправляем первую карту с кнопками навигации для первого подарка
    gift_message = await show_gift_card_with_pagination(callback.message, state, 0, "gift_card_1")
    if gift_message:
        await state.update_data(gift_card_1_message_id=gift_message.message_id)
    await state.set_state(GameStates.waiting_for_gift_card_1)


async def show_gift_card_with_pagination(message: Message, state: FSMContext, card_index: int, gift_type: str):
    """Показать карту подарка с кнопками пагинации"""
    data = await state.get_data()
    cards_list = data.get("gift_cards_list", [])
    
    if not cards_list or card_index < 0 or card_index >= len(cards_list):
        return None
    
    card_filename = cards_list[card_index]
    card_path = get_gift_card_path(card_filename)
    
    if not card_path or not os.path.exists(card_path):
        return None
    
    photo = FSInputFile(card_path)
    
    # Создаем кнопки навигации
    keyboard_buttons = []
    
    # Кнопки навигации с номером карты в центре
    nav_buttons = []
    if len(cards_list) > 1:
        if card_index > 0:
            nav_buttons.append(InlineKeyboardButton(text="◀️ Предыдущая", callback_data=f"gift_{gift_type}_prev_{card_index}"))
        
        # Номер карты в центре (неактивная кнопка)
        nav_buttons.append(InlineKeyboardButton(text=f"{card_index + 1}/{len(cards_list)}", callback_data=f"gift_{gift_type}_number"))
        
        if card_index < len(cards_list) - 1:
            nav_buttons.append(InlineKeyboardButton(text="Следующая ▶️", callback_data=f"gift_{gift_type}_next_{card_index}"))
        
        if nav_buttons:
            keyboard_buttons.append(nav_buttons)
    
    # Кнопка выбора карты
    keyboard_buttons.append([InlineKeyboardButton(text="Выбрать эту карту", callback_data=f"gift_{gift_type}_select_{card_index}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем или обновляем сообщение (без caption)
    if message.photo:
        # Обновляем существующее сообщение
        media = InputMediaPhoto(media=photo)
        await message.edit_media(media=media, reply_markup=keyboard)
        return message
    else:
        # Отправляем новое сообщение
        sent_message = await message.answer_photo(photo, reply_markup=keyboard)
        return sent_message


# Обработчики навигации по подаркам
@router.callback_query(F.data.startswith("gift_gift_card_1_prev_"))
async def gift_card_1_previous(callback: CallbackQuery, state: FSMContext):
    """Переход к предыдущей карте подарка 1"""
    await callback.answer()
    card_index = int(callback.data.split("_")[-1])
    new_index = max(0, card_index - 1)
    await state.update_data(current_gift_card_index=new_index)
    await show_gift_card_with_pagination(callback.message, state, new_index, "gift_card_1")


@router.callback_query(F.data.startswith("gift_gift_card_1_next_"))
async def gift_card_1_next(callback: CallbackQuery, state: FSMContext):
    """Переход к следующей карте подарка 1"""
    await callback.answer()
    data = await state.get_data()
    cards_list = data.get("gift_cards_list", [])
    card_index = int(callback.data.split("_")[-1])
    new_index = min(len(cards_list) - 1, card_index + 1)
    await state.update_data(current_gift_card_index=new_index)
    await show_gift_card_with_pagination(callback.message, state, new_index, "gift_card_1")


@router.callback_query(F.data == "gift_gift_card_1_number")
async def gift_card_1_number_click(callback: CallbackQuery):
    """Обработка клика на номер карты подарка 1 (ничего не делаем)"""
    await callback.answer()


@router.callback_query(F.data.startswith("gift_gift_card_1_select_"))
async def gift_card_1_select(callback: CallbackQuery, state: FSMContext):
    """Выбор первой карты подарка"""
    await callback.answer("Карта выбрана!")
    
    try:
        card_index = int(callback.data.split("_")[-1])
        data = await state.get_data()
        cards_list = data.get("gift_cards_list", [])
        
        if 0 <= card_index < len(cards_list):
            selected_card = cards_list[card_index]
            await save_user_data(callback.from_user.id, gift_card_1=selected_card)
            await log_funnel_step(callback.from_user.id, "gift_card_1")
            
            # Сохраняем message_id первого подарка для последующего удаления
            data = await state.get_data()
            gift_card_1_msg_id = data.get("gift_card_1_message_id")
            if not gift_card_1_msg_id:
                gift_card_1_msg_id = callback.message.message_id
                await state.update_data(gift_card_1_message_id=gift_card_1_msg_id)
            
            # Удаляем сообщение "🎁 Выбери первую карту подарка:"
            gift_start_text_msg_id = data.get("gift_start_text_message_id")
            if gift_start_text_msg_id:
                try:
                    await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=gift_start_text_msg_id)
                except Exception as e:
                    logger.error(f"Ошибка при удалении сообщения о выборе первой карты: {e}")
            
            # Удаляем сообщение с картинкой первой карты
            try:
                await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=gift_card_1_msg_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщения с первой картой подарка: {e}")
            
            # Автоматически переходим к выбору второго подарка
            all_cards = data.get("gift_cards_list", [])
            
            if all_cards:
                # Создаем новый список карт без первой выбранной карты
                remaining_cards = [card for card in all_cards if card != selected_card]
                
                if not remaining_cards:
                    await callback.message.answer("❌ Больше нет доступных карт для выбора!")
                    return
                
                # Сохраняем обновленный список карт для второго выбора
                await state.update_data(
                    gift_cards_list=remaining_cards,
                    current_gift_card_index=0,
                    gift_type="gift_card_2",
                    selected_gift_card_1=selected_card
                )
                
                # Отправляем сообщение о выборе второго подарка и сохраняем его message_id
                second_gift_text_message = await callback.message.answer("🎁 Теперь выбери вторую карту подарка:")
                await state.update_data(gift_card_2_text_message_id=second_gift_text_message.message_id)
                
                # Отправляем первую карту для второго подарка (из оставшихся карт)
                # Используем bot напрямую, так как callback.message уже удалено
                from aiogram.types import FSInputFile
                from cards import get_gift_card_path
                import os
                
                first_remaining_card = remaining_cards[0]
                card_path = get_gift_card_path(first_remaining_card)
                if card_path and os.path.exists(card_path):
                    photo = FSInputFile(card_path)
                    
                    # Создаем кнопки навигации
                    keyboard_buttons = []
                    nav_buttons = []
                    if len(remaining_cards) > 1:
                        nav_buttons.append(InlineKeyboardButton(text=f"1/{len(remaining_cards)}", callback_data="gift_gift_card_2_number"))
                        nav_buttons.append(InlineKeyboardButton(text="Следующая ▶️", callback_data=f"gift_gift_card_2_next_0"))
                        keyboard_buttons.append(nav_buttons)
                    
                    keyboard_buttons.append([InlineKeyboardButton(text="Выбрать эту карту", callback_data=f"gift_gift_card_2_select_0")])
                    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
                    
                    gift_message = await callback.bot.send_photo(
                        chat_id=callback.message.chat.id,
                        photo=photo,
                        reply_markup=keyboard
                    )
                    await state.update_data(gift_card_2_message_id=gift_message.message_id)
                
                await state.set_state(GameStates.waiting_for_gift_card_2)
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка при выборе первого подарка: {e}")


@router.callback_query(F.data == "gift_card_1_selected")
async def gift_card_1_selected_click(callback: CallbackQuery):
    """Обработка клика на уже выбранную первую карту (ничего не делаем)"""
    await callback.answer("Эта карта уже выбрана")


# Обработчики для второго подарка
@router.callback_query(F.data.startswith("gift_gift_card_2_prev_"))
async def gift_card_2_previous(callback: CallbackQuery, state: FSMContext):
    """Переход к предыдущей карте подарка 2"""
    await callback.answer()
    card_index = int(callback.data.split("_")[-1])
    new_index = max(0, card_index - 1)
    await state.update_data(current_gift_card_index=new_index)
    await show_gift_card_with_pagination(callback.message, state, new_index, "gift_card_2")


@router.callback_query(F.data.startswith("gift_gift_card_2_next_"))
async def gift_card_2_next(callback: CallbackQuery, state: FSMContext):
    """Переход к следующей карте подарка 2"""
    await callback.answer()
    data = await state.get_data()
    cards_list = data.get("gift_cards_list", [])
    card_index = int(callback.data.split("_")[-1])
    new_index = min(len(cards_list) - 1, card_index + 1)
    await state.update_data(current_gift_card_index=new_index)
    await show_gift_card_with_pagination(callback.message, state, new_index, "gift_card_2")


@router.callback_query(F.data == "gift_gift_card_2_number")
async def gift_card_2_number_click(callback: CallbackQuery):
    """Обработка клика на номер карты подарка 2 (ничего не делаем)"""
    await callback.answer()


@router.callback_query(F.data.startswith("gift_gift_card_2_select_"))
async def gift_card_2_select(callback: CallbackQuery, state: FSMContext):
    """Выбор второй карты подарка"""
    await callback.answer("Карта выбрана!")
    
    try:
        card_index = int(callback.data.split("_")[-1])
        data = await state.get_data()
        cards_list = data.get("gift_cards_list", [])
        
        if 0 <= card_index < len(cards_list):
            selected_card = cards_list[card_index]
            await save_user_data(callback.from_user.id, gift_card_2=selected_card)
            await log_funnel_step(callback.from_user.id, "gift_card_2")
            
            # Меняем кнопку на "выбран" в том же сообщении (быстро, без edit_media)
            keyboard_buttons = []
            nav_buttons = []
            if len(cards_list) > 1:
                if card_index > 0:
                    nav_buttons.append(InlineKeyboardButton(text="◀️ Предыдущая", callback_data=f"gift_gift_card_2_prev_{card_index}"))
                nav_buttons.append(InlineKeyboardButton(text=f"{card_index + 1}/{len(cards_list)}", callback_data="gift_gift_card_2_number"))
                if card_index < len(cards_list) - 1:
                    nav_buttons.append(InlineKeyboardButton(text="Следующая ▶️", callback_data=f"gift_gift_card_2_next_{card_index}"))
                if nav_buttons:
                    keyboard_buttons.append(nav_buttons)
            
            keyboard_buttons.append([InlineKeyboardButton(text="✅ Выбрано", callback_data="gift_card_2_selected")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            # Быстро обновляем только кнопки, без изменения медиа
            await callback.message.edit_reply_markup(reply_markup=keyboard)
            
            # Помечаем второй подарок как выбранный
            await state.update_data(gift_card_2_selected=True, selected_gift_card_2=selected_card)
            
            # Удаляем сообщения с картинками подарков и текстовые сообщения
            data = await state.get_data()
            gift_card_1_msg_id = data.get("gift_card_1_message_id")
            gift_card_2_msg_id = data.get("gift_card_2_message_id")
            gift_card_2_text_msg_id = data.get("gift_card_2_text_message_id")
            
            try:
                if gift_card_1_msg_id:
                    await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=gift_card_1_msg_id)
                if gift_card_2_msg_id:
                    await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=gift_card_2_msg_id)
                if gift_card_2_text_msg_id:
                    await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=gift_card_2_text_msg_id)
            except Exception as e:
                logger.error(f"Ошибка при удалении сообщений с подарками: {e}")
            
            # Теперь отправляем финальный текст
            text = """✨ В 60% случаев подарки, которые выпадают в игре, проявляются и в реальной жизни.
Я желаю тебе удачи и смелости идти новым путём.
Помни: так как было раньше — уже не работает."""
            
            await callback.message.answer(text)
            
            # Переход к офферу
            from config import INSTAGRAM_ACCOUNT
            
            offer_text = """Если хочешь получить полный план по изменению своей жизни — я приглашаю тебя на большую трансформационную игру по созданию твоего нового настоящего 🔥"""
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔥 Хочу узнать подробнее", url=f"https://instagram.com/{INSTAGRAM_ACCOUNT.replace('@', '')}")]
            ])
            
            await callback.message.answer(offer_text, reply_markup=keyboard)
            
            # Оффер на скидку
            discount_text = """Прямо сейчас ты можешь получить скидку 15%, если напишешь отзыв о том, как тебе мини-версия игры, и отметишь наш Instagram-аккаунт ✨"""
            
            keyboard2 = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Хочу скидку 15%", callback_data="want_discount")]
            ])
            
            await callback.message.answer(discount_text, reply_markup=keyboard2)
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка при выборе второго подарка: {e}")


@router.callback_query(F.data == "gift_card_2_selected")
async def gift_card_2_selected_click(callback: CallbackQuery):
    """Обработка клика на уже выбранную вторую карту (ничего не делаем)"""
    await callback.answer("Эта карта уже выбрана")

