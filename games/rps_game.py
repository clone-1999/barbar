import random
from database import db

class RPSGame:
    """ကျောက်/ကတ်ကြေး/စက္ကူ"""
    
    CHOICES = ["rock", "paper", "scissors"]
    EMOJIS = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
    
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.game_id = f"rps_{chat_id}"
        self.players = {}
        self.choices = {}
        self.started = False
        self._load()
        
    def _load(self):
        data = db.get_game(self.game_id)
        if data:
            self.players = {int(k): v for k, v in data.get("players", {}).items()}
            self.choices = {int(k): v for k, v in data.get("choices", {}).items()}
            self.started = data.get("started", False)
            
    def _save(self):
        players_data = {str(k): v for k, v in self.players.items()}
        choices_data = {str(k): v for k, v in self.choices.items()}
        db.save_game(self.game_id, "rps", {
            "players": players_data,
            "choices": choices_data,
            "started": self.started
        })
        
    def start(self, user_ids):
        if len(user_ids) != 2:
            return "၂ ယောက်ပဲဆော့လို့ရတယ်"
        self.players = {uid: None for uid in user_ids}
        self.choices = {}
        self.started = True
        self._save()
        return "🪨📄✂️ ရွေးပါ! /rock, /paper, /scissors"
        
    def choose(self, user_id, choice):
        if not self.started:
            return "ဂိမ်းမစရသေးဘူး"
        if user_id not in self.players:
            return "မင်းမပါဘူး"
        if choice not in self.CHOICES:
            return "rock, paper, scissors ပဲရွေးရမယ်"
            
        self.choices[user_id] = choice
        self._save()
        
        if len(self.choices) == 2:
            result = self._resolve()
            self.started = False
            self._save()
            return result
        return f"{user_id} ရွေးပြီးပြီ! နောက်တစ်ယောက်စောင့်နေ"
        
    def _resolve(self):
        p1, p2 = list(self.choices.keys())
        c1, c2 = self.choices[p1], self.choices[p2]
        
        msg = f"{p1}: {self.EMOJIS[c1]}  VS  {p2}: {self.EMOJIS[c2]}\n"
        
        if c1 == c2:
            msg += "🤝 သရေကျသွားတယ်"
        elif (c1 == "rock" and c2 == "scissors") or \
             (c1 == "scissors" and c2 == "paper") or \
             (c1 == "paper" and c2 == "rock"):
            msg += f"🎉 {p1} အနိုင်ရသွားပြီ!"
            db.update_score(p1, "rps", 1)
        else:
            msg += f"🎉 {p2} အနိုင်ရသွားပြီ!"
            db.update_score(p2, "rps", 1)
            
        return msg
