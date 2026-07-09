import random
from database import db

class QuizGame:
    """ဉာဏ်စမ်းမေးခွန်း"""
    
    QUESTIONS = [
        {"q": "မြန်မာနိုင်ငံရဲ့မြို့တော်က?", "a": "နေပြည်တော်", "opts": ["ရန်ကုန်", "မန္တလေး", "နေပြည်တော်", "ပဲခူး"]},
        {"q": "၁+၁ က?", "a": "၂", "opts": ["၁", "၂", "၃", "၄"]},
        {"q": "ကမ္ဘာပေါ်မှာအကြီးဆုံးတိရစ္ဆာန်က?", "a": "ဝေလငါး", "opts": ["ဆင်", "ဝေလငါး", "ဂျီရဖ်", "ငါးမန်း"]},
    ]
    
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.game_id = f"quiz_{chat_id}"
        self.players = {}
        self.current_q = 0
        self.scores = {}
        self.started = False
        self._load()
        
    def _load(self):
        data = db.get_game(self.game_id)
        if data:
            self.__dict__.update(data)
            
    def _save(self):
        db.save_game(self.game_id, "quiz", {
            "players": self.players,
            "current_q": self.current_q,
            "scores": self.scores,
            "started": self.started
        })
        
    def start(self, user_ids):
        self.players = {uid: False for uid in user_ids}  # False = not answered
        self.scores = {uid: 0 for uid in user_ids}
        self.current_q = 0
        self.started = True
        self._save()
        return self.get_question()
        
    def get_question(self):
        if self.current_q >= len(self.QUESTIONS):
            self.started = False
            result = "🏆 မေးခွန်းအကုန်ပြီးပါပြီ!\n"
            sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
            for i, (uid, score) in enumerate(sorted_scores[:5], 1):
                result += f"{i}. {uid}: {score} မှတ်\n"
            return result
            
        q_data = self.QUESTIONS[self.current_q]
        msg = f"❓ {q_data['q']}\n"
        for i, opt in enumerate(q_data["opts"], 1):
            msg += f"{i}. {opt}\n"
        return msg
        
    def answer(self, user_id, answer_idx):
        if not self.started:
            return "ဂိမ်းမစရသေးဘူး"
            
        if user_id not in self.players:
            return "မင်းမပါဘူး"
            
        if self.players[user_id]:
            return "မင်းဖြေပြီးသွားပြီ"
            
        q_data = self.QUESTIONS[self.current_q]
        correct = q_data["opts"].index(q_data["a"]) + 1
        
        if answer_idx == correct:
            self.scores[user_id] += 1
            result = f"✅ {user_id} မှန်ပါတယ်! (+၁)"
        else:
            result = f"❌ {user_id} မှားပါတယ်။ အဖြေက {q_data['a']}"
            
        self.players[user_id] = True
        
        # အားလုံးဖြေပြီးရင် နောက်မေးခွန်း
        if all(self.players.values()):
            self.current_q += 1
            for uid in self.players:
                self.players[uid] = False
            self._save()
            result += "\n\n" + self.get_question()
        else:
            self._save()
            
        return result
