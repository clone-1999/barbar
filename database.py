from pymongo import MongoClient
from config import config
import time

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DB_NAME]
        self.games = self.db["games"]
        self.players = self.db["players"]
        self.scores = self.db["scores"]
        self.broadcast = self.db["broadcast"]

    def _convert_keys_to_string(self, data):
        """Dictionary ထဲက integer keys တွေကို string ပြောင်းမယ်"""
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                new_key = str(key)
                if isinstance(value, dict):
                    new_data[new_key] = self._convert_keys_to_string(value)
                elif isinstance(value, list):
                    new_data[new_key] = [
                        self._convert_keys_to_string(item) if isinstance(item, dict) else item 
                        for item in value
                    ]
                else:
                    new_data[new_key] = value
            return new_data
        return data

    def save_game(self, game_id, game_type, data):
        """ဂိမ်း data သိမ်းမယ် (keys တွေကို string ပြောင်းပြီး)"""
        cleaned_data = self._convert_keys_to_string(data)
        self.games.update_one(
            {"game_id": game_id},
            {"$set": {
                "game_type": game_type,
                "data": cleaned_data,
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

    def add_player(self, user_id, username, first_name):
        """ကစားသူထည့်မယ်"""
        self.players.update_one(
            {"user_id": str(user_id)},
            {"$set": {
                "username": username,
                "first_name": first_name,
                "last_active": time.time()
            }},
            upsert=True
        )

    def get_player(self, user_id):
        """ကစားသူပြန်ယူမယ်"""
        return self.players.find_one({"user_id": str(user_id)})

    def update_score(self, user_id, game_type, points):
        """အမှတ်တွေတိုးမယ်"""
        self.scores.update_one(
            {"user_id": str(user_id), "game_type": game_type},
            {"$inc": {"score": points}, "$set": {"updated_at": time.time()}},
            upsert=True
        )

    def get_top_scores(self, game_type, limit=10):
        """ထိပ်ဆုံး ၁၀ ယောက်ပြန်မယ်"""
        return list(self.scores.find(
            {"game_type": game_type}
        ).sort("score", -1).limit(limit))

    def save_broadcast(self, message, chat_ids):
        """Broadcast မှတ်မယ်"""
        self.broadcast.insert_one({
            "message": message,
            "chat_ids": chat_ids,
            "sent_at": time.time()
        })

db = Database()
