import random
import time
from database import db

class WerewolfGame:
    """Werewolf ဂိမ်း - လူ ၅ ယောက်မှ ၂၀ ယောက်အထိ"""
    
    ROLES = {
        "villager": "ရွာသား",
        "werewolf": "ဝံပုလွေ",
        "seer": "ဗေဒင်",
        "doctor": "ဆရာဝန်",
        "hunter": "မုဆိုး"
    }
    
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.game_id = f"werewolf_{chat_id}"
        self.players = {}
        self.alive = []
        self.phase = "waiting"
        self.night_actions = {}
        self.started = False
        self._load()
        
    def _load(self):
        data = db.get_game(self.game_id)
        if data:
            self.players = {int(k): v for k, v in data.get("players", {}).items()}
            self.alive = [int(x) for x in data.get("alive", [])]
            self.phase = data.get("phase", "waiting")
            self.night_actions = data.get("night_actions", {})
            self.started = data.get("started", False)
            
    def _save(self):
        players_data = {str(k): v for k, v in self.players.items()}
        alive_data = [str(x) for x in self.alive]
        db.save_game(self.game_id, "werewolf", {
            "players": players_data,
            "alive": alive_data,
            "phase": self.phase,
            "night_actions": self.night_actions,
            "started": self.started
        })
        
    def assign_roles(self, user_ids):
        n = len(user_ids)
        roles = []
        werewolf_count = max(1, n // 4)
        
        roles.extend(["werewolf"] * werewolf_count)
        roles.append("seer")
        if n >= 6:
            roles.append("doctor")
        if n >= 8:
            roles.append("hunter")
        roles.extend(["villager"] * (n - len(roles)))
        random.shuffle(roles)
        
        self.players = {uid: role for uid, role in zip(user_ids, roles)}
        self.alive = user_ids.copy()
        self.started = True
        self.phase = "night"
        self._save()
        return self.players
        
    def night_action(self, user_id, target_id):
        if self.phase != "night":
            return "ညဘက်မဟုတ်သေးဘူး"
            
        role = self.players.get(user_id)
        if role == "werewolf":
            self.night_actions["kill"] = target_id
        elif role == "seer":
            self.night_actions["seer"] = target_id
        elif role == "doctor":
            self.night_actions["save"] = target_id
        else:
            return "မင်းဒီလုပ်ဆောင်ချက်မလုပ်နိုင်ဘူး"
            
        self._save()
        return f"{self.ROLES[role]} action လုပ်ပြီး"
        
    def resolve_night(self):
        if self.phase != "night":
            return "ညဘက်မဟုတ်ဘူး"
            
        kill_target = self.night_actions.get("kill")
        save_target = self.night_actions.get("save")
        seer_target = self.night_actions.get("seer")
        
        msg = ""
        
        if seer_target and seer_target in self.players:
            role = self.players[seer_target]
            msg += f"🔮 {seer_target} က {self.ROLES[role]} ဖြစ်တယ်\n"
            
        if kill_target and kill_target != save_target:
            if kill_target in self.alive:
                self.alive.remove(kill_target)
                msg += f"💀 {kill_target} သေသွားပြီ!\n"
        else:
            msg += "🛡️ ဘယ်သူမှမသေဘူး\n"
            
        self.phase = "day"
        self.night_actions = {}
        self._save()
        
        alive_roles = [self.players[uid] for uid in self.alive]
        if "werewolf" not in alive_roles:
            self.started = False
            msg += "🎉 ရွာသားတွေအနိုင်ရသွားပြီ!"
        elif len(alive_roles) == 1 and "werewolf" in alive_roles:
            self.started = False
            msg += "🐺 ဝံပုလွေတွေအနိုင်ရသွားပြီ!"
            
        return msg
        
    def vote(self, user_id, target_id):
        if self.phase != "day":
            return "မဲပေးချိန်မဟုတ်ဘူး"
            
        if user_id not in self.alive:
            return "မင်းသေသွားပြီ"
            
        if target_id not in self.alive:
            return "ဒီလူသေသွားပြီ"
            
        self.night_actions[f"vote_{user_id}"] = target_id
        self._save()
        return f"✅ {user_id} က {target_id} ကိုမဲပေးပြီး"
        
    def get_status(self):
        msg = f"🐺 Werewolf - {self.phase}\n"
        msg += f"အသက်ရှင်သူ: {len(self.alive)} ယောက်\n"
        for uid in self.alive:
            msg += f"  👤 {uid}\n"
        return msg
