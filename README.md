# Telegram-бот "Ты и Вселенная"

Мини-игра-воронка на aiogram 3.x

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` на основе `.env.example`:
```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
INSTAGRAM_ACCOUNT=@your_instagram_account
```

3. Добавьте карты в папку `cards/`:
   - Названия файлов: `card_1.jpg`, `card_2.jpg`, и т.д.
   - Форматы: `.jpg`, `.png`, `.jpeg`

## Запуск

```bash
python main.py
```

## Админ-панель

Команды для администраторов:
- `/admin` - главная панель
- `/users` - список всех пользователей
- `/stats` - детальная статистика
- `/user <user_id>` - данные конкретного пользователя

## Структура проекта

- `main.py` - точка входа
- `config.py` - конфигурация
- `database.py` - работа с БД
- `states.py` - FSM состояния
- `cards.py` - работа с картами
- `handlers/` - обработчики сообщений
  - `start.py` - приветствие
  - `name.py` - сбор имени
  - `request.py` - сбор запроса
  - `dice.py` - бросок кубика
  - `cards.py` - работа с картами
  - `discount.py` - оффер на скидку
  - `admin.py` - админ-панель

## База данных

Используется SQLite (`bot_database.db`):
- `users` - данные пользователей
- `user_answers` - ответы на вопросы
- `funnel_stats` - статистика по воронке

