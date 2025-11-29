import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Путь к папке с картами
CARDS_DIR = "images"

# Путь к папке с картами подарков
GIFT_CARDS_DIR = "gift_images"

# Instagram аккаунт для перехода
INSTAGRAM_ACCOUNT = os.getenv("INSTAGRAM_ACCOUNT", "@your_account")

# База данных
DATABASE_PATH = "bot_database.db"

