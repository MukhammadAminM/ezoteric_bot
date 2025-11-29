from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database import save_user_data, log_funnel_step
from states import GameStates

router = Router()


@router.message(GameStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка введенного имени"""
    name = message.text.strip()
    await save_user_data(message.from_user.id, name=name, username=message.from_user.username)
    await log_funnel_step(message.from_user.id, "name_collected")
    
    request_text = """Положи руку на сердце ❤️
Сделай глубокий вдох и подумай о том, что ты искренне хочешь, чтобы осуществилось.

Это может быть всё, что угодно:
— закрыть долги
— улучшить отношения
— полюбить себя
— увеличить доход
— открыть бизнес
— или любая другая важная для тебя цель.

Главное — чтобы желание было честным и от души.

Когда почувствуешь его — представь, что оно уже сбылось. Почувствуй эмоции, которые ты испытываешь в этом будущем."""

    await message.answer(request_text)
    await message.answer("✍️ Теперь напиши свой запрос в настоящем времени, как будто это уже произошло.")
    await state.set_state(GameStates.waiting_for_request)

