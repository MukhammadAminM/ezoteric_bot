import aiosqlite
from datetime import datetime
from config import DATABASE_PATH


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT,
                request TEXT,
                dice_result INTEGER,
                card_1 TEXT,
                card_2 TEXT,
                gift_card_1 TEXT,
                gift_card_2 TEXT,
                answers TEXT,
                instagram_nick TEXT,
                discount_claimed INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_number INTEGER,
                answer TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS funnel_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                step TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        await db.commit()


async def save_user_data(user_id: int, **kwargs):
    """Сохранение данных пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Проверяем, существует ли пользователь
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        exists = await cursor.fetchone()
        
        if exists:
            # Обновляем существующего пользователя
            fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [datetime.now().isoformat(), user_id]
            await db.execute(f"UPDATE users SET {fields}, updated_at = ? WHERE user_id = ?", values)
        else:
            # Создаем нового пользователя
            fields = ", ".join(kwargs.keys())
            placeholders = ", ".join(["?" for _ in kwargs])
            values = [user_id] + list(kwargs.values()) + [datetime.now().isoformat(), datetime.now().isoformat()]
            await db.execute(
                f"INSERT INTO users (user_id, {fields}, created_at, updated_at) VALUES (?, {placeholders}, ?, ?)",
                values
            )
        await db.commit()


async def save_answer(user_id: int, question_number: int, answer: str):
    """Сохранение ответа на вопрос"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO user_answers (user_id, question_number, answer, created_at) VALUES (?, ?, ?, ?)",
            (user_id, question_number, answer, datetime.now().isoformat())
        )
        await db.commit()


async def log_funnel_step(user_id: int, step: str):
    """Логирование шага воронки"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO funnel_stats (user_id, step, created_at) VALUES (?, ?, ?)",
            (user_id, step, datetime.now().isoformat())
        )
        await db.commit()


async def get_user_data(user_id: int):
    """Получение данных пользователя"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return None


async def get_all_users():
    """Получение всех пользователей (для админ-панели)"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT * FROM users ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]


async def get_funnel_stats():
    """Получение статистики по воронке"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            SELECT step, COUNT(*) as count 
            FROM funnel_stats 
            GROUP BY step
        """)
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

