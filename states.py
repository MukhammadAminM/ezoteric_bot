from aiogram.fsm.state import State, StatesGroup


class GameStates(StatesGroup):
    """Состояния для игры"""
    waiting_for_name = State()
    waiting_for_request = State()
    waiting_for_dice = State()
    waiting_for_retry_decision = State()
    waiting_for_card_selection = State()
    waiting_for_card_description = State()
    waiting_for_card_emotions = State()
    waiting_for_card_purpose = State()
    waiting_for_self_improvement = State()
    waiting_for_advice = State()
    waiting_for_gift_start = State()
    waiting_for_gift_card_1 = State()
    waiting_for_gift_card_2 = State()
    waiting_for_instagram_nick = State()

