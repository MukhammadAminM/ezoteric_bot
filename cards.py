import os
import random
from config import CARDS_DIR, GIFT_CARDS_DIR


def get_all_cards():
    """Получение списка всех карт"""
    if not os.path.exists(CARDS_DIR):
        return []
    
    # Ищем все изображения в папке (jpg, png, jpeg)
    cards = [f for f in os.listdir(CARDS_DIR) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
    return sorted(cards)  # Сортируем для стабильности


def get_all_gift_cards():
    """Получение списка всех карт подарков"""
    if not os.path.exists(GIFT_CARDS_DIR):
        return []
    
    # Ищем все изображения в папке (jpg, png, jpeg)
    cards = [f for f in os.listdir(GIFT_CARDS_DIR) if f.lower().endswith((".jpg", ".png", ".jpeg"))]
    return sorted(cards)  # Сортируем для стабильности


def get_random_card():
    """Получение случайной карты"""
    cards = get_all_cards()
    if cards:
        return random.choice(cards)
    return None


def get_card_path(card_filename):
    """Получение полного пути к карте"""
    if card_filename:
        return os.path.join(CARDS_DIR, card_filename)
    return None


def get_gift_card_path(card_filename):
    """Получение полного пути к карте подарка"""
    if card_filename:
        return os.path.join(GIFT_CARDS_DIR, card_filename)
    return None

