from pymongo import MongoClient
from config import config
import asyncio
import time

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DB_NAME]
        
        # Collections
        self.games = self.db["games"]
        self.players = self.db["players"]
        self.scores = self.db["scores"]
        self.broadcast = self.db["broadcast"]
        self.restart = self.db["restart"]
        
        # Indexes
        self.games.create_index("game_id", unique=True)
        self.players.create_index("user_id")
        self.scores.create_index([("user_id", 1), ("game_type", 1)])
        
    # === Game State ===
    def save_game(self, game_id, game_type, data):
        """ဂိမ်း data သိမ်းမယ်"""
        self.games.update_one(
            {"game_id": game_id},
            {"$set": {
                "game_type": game_type,
                "data": data,
                "updated_at": time.time()
            }},
            upsert=True
        )
        
    def get_game(self, game_id):
        """ဂိမ်း data ပြန်ယူမယ်"""
        result = self.games.find_one({"game_id": game_id})
        return result["data"] if result else None
        
    def delete_game(self, game_id):
        """ဂိမ်း data ဖျက်မယ်"""
        self.games.delete_one({"game_id": game_id})
        
    # === Player ===
    def add_player(self, user_id, username, first_name):
        """ကစားသူထည့်မယ်"""
        self.players.update_one(
            {"user_id": user_id},
            {"$set": {
                "username": username,
                "first_name": first_name,
                "last_active": time.time()
            }},
            upsert=True
        )
        
    def get_player(self, user_id):
        return self.players.find_one({"user_id": user_id})
        
    # === Score ===
    def update_score(self, user_id, game_type, points):
        """အမှတ်တွေတိုးမယ်"""
        self.scores.update_one(
            {"user_id": user_id, "game_type": game_type},
            {"$inc": {"score": points}, "$set": {"updated_at": time.time()}},
            upsert=True
        )
        
    def get_top_scores(self, game_type, limit=10):
        """ထိပ်ဆုံး ၁၀ ယောက်ပြန်မယ်"""
        return list(self.scores.find(
            {"game_type": game_type}
        ).sort("score", -1).limit(limit))
        
    # === Broadcast ===
    def save_broadcast(self, message, chat_ids):
        """Broadcast မှတ်မယ်"""
        self.broadcast.insert_one({
            "message": message,
            "chat_ids": chat_ids,
            "sent_at": time.time()
        })
        
    # === Auto Restart ===
    def set_restart_flag(self, game_id):
        """Restart flag ထားမယ်"""
        self.restart.update_one(
            {"game_id": game_id},
            {"$set": {"restart_at": time.time() + config.RESTART_TIMEOUT}},
            upsert=True
        )
        
    def check_restart(self, game_id):
        """Restart လုပ်ရမလားစစ်မယ်"""
        result = self.restart.find_one({"game_id": game_id})
        if result and result["restart_at"] < time.time():
            self.restart.delete_one({"game_id": game_id})
            return True
        return False

db = Database()
