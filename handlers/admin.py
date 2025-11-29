from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_all_users, get_funnel_stats, get_user_data
from config import ADMIN_IDS

router = Router()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Админ-панель"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к админ-панели.")
        return
    
    stats = await get_funnel_stats()
    users = await get_all_users()
    
    text = f"""📊 Админ-панель

👥 Всего пользователей: {len(users)}

📈 Статистика по воронке:
"""
    
    for step, count in stats.items():
        text += f"  • {step}: {count}\n"
    
    text += "\nИспользуйте команды:\n"
    text += "/users - список всех пользователей\n"
    text += "/stats - детальная статистика\n"
    text += "/user <user_id> - данные конкретного пользователя"
    
    await message.answer(text)


@router.message(Command("users"))
async def list_users(message: Message):
    """Список всех пользователей"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к админ-панели.")
        return
    
    users = await get_all_users()
    
    if not users:
        await message.answer("Пользователей пока нет.")
        return
    
    text = "👥 Список пользователей:\n\n"
    for user in users[:20]:  # Показываем первые 20
        text += f"ID: {user['user_id']}\n"
        text += f"Имя: {user.get('name', 'Не указано')}\n"
        text += f"Запрос: {user.get('request', 'Не указано')[:50]}...\n"
        text += f"Скидка: {'Да' if user.get('discount_claimed') else 'Нет'}\n"
        text += f"Дата: {user.get('created_at', 'Неизвестно')}\n\n"
    
    if len(users) > 20:
        text += f"... и ещё {len(users) - 20} пользователей"
    
    await message.answer(text)


@router.message(Command("stats"))
async def detailed_stats(message: Message):
    """Детальная статистика"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к админ-панели.")
        return
    
    stats = await get_funnel_stats()
    users = await get_all_users()
    
    total_users = len(users)
    discount_claimed = sum(1 for u in users if u.get('discount_claimed'))
    
    text = f"""📊 Детальная статистика

👥 Всего пользователей: {total_users}
🎁 Скидок получено: {discount_claimed}
📈 Конверсия в скидку: {round(discount_claimed / total_users * 100, 2) if total_users > 0 else 0}%

📋 Шаги воронки:
"""
    
    for step, count in sorted(stats.items()):
        percentage = round(count / total_users * 100, 2) if total_users > 0 else 0
        text += f"  • {step}: {count} ({percentage}%)\n"
    
    await message.answer(text)


@router.message(Command("user"))
async def user_info(message: Message):
    """Информация о конкретном пользователе"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет доступа к админ-панели.")
        return
    
    try:
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("Использование: /user <user_id>")
        return
    
    user_data = await get_user_data(user_id)
    
    if not user_data:
        await message.answer(f"Пользователь с ID {user_id} не найден.")
        return
    
    text = f"""👤 Данные пользователя:

ID: {user_data['user_id']}
Имя: {user_data.get('name', 'Не указано')}
Username: {user_data.get('username', 'Не указано')}
Запрос: {user_data.get('request', 'Не указано')}
Результат кубика: {user_data.get('dice_result', 'Не указано')}
Карта 1: {user_data.get('card_1', 'Не указано')}
Карта 2: {user_data.get('card_2', 'Не указано')}
Подарок 1: {user_data.get('gift_card_1', 'Не указано')}
Подарок 2: {user_data.get('gift_card_2', 'Не указано')}
Instagram: {user_data.get('instagram_nick', 'Не указано')}
Скидка: {'Да' if user_data.get('discount_claimed') else 'Нет'}
Создан: {user_data.get('created_at', 'Неизвестно')}
Обновлен: {user_data.get('updated_at', 'Неизвестно')}
"""
    
    await message.answer(text)

