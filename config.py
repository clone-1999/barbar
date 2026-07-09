import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram API
    API_ID = int(os.getenv("API_ID", "123456"))
    API_HASH = os.getenv("API_HASH", "your_api_hash")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
    
    # Owner
    OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))  # သင့် Telegram ID
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "game_bot_db")
    
    # Settings
    AUTO_RESTART = True  # ပိသွားရင် auto restart
    RESTART_TIMEOUT = 300  # 5 မိနစ်

config = Config()
