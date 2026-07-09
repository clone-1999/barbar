import random
from database import db

class HangmanGame:
    """ကြိုးဆွဲဂိမ်း"""
    
    WORDS = ["မြန်မာ", "ထိုင်း", "တရုတ်", "အင်္ဂလိပ်", "ဂျပန်", "ကိုရီးယား", "အိန္ဒိယ"]
    
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.game_id = f"hangman_{chat_id}"
        self.word = ""
        self.display = []
        self.guessed = []
        self.tries = 6
        self.players = set()
        self.started = False
        self._load()
        
    def _load(self):
        data = db.get_game(self.game_id)
        if data:
            self.word = data.get("word", "")
            self.display = data.get("display", [])
            self.guessed = data.get("guessed", [])
            self.tries = data.get("tries", 6)
            self.players = set([int(x) for x in data.get("players", [])])
            self.started = data.get("started", False)
            
    def _save(self):
        players_data = [str(x) for x in self.players]
        db.save_game(self.game_id, "hangman", {
            "word": self.word,
            "display": self.display,
            "guessed": self.guessed,
            "tries": self.tries,
            "players": players_data,
            "started": self.started
        })
        
    def start(self, user_id):
        self.word = random.choice(self.WORDS)
        self.display = ["_"] * len(self.word)
        self.guessed = []
        self.tries = 6
        self.players = {user_id}
        self.started = True
        self._save()
        return f"🪢 ကြိုးဆွဲဂိမ်းစပြီ!\n{' '.join(self.display)}\nအကြိမ် {self.tries} ကျန်တယ်"
        
    def guess(self, user_id, letter):
        if not self.started:
            return "ဂိမ်းမစရသေးဘူး"
        if user_id not in self.players:
            return "မင်းမပါဘူး"
        if len(letter) != 1:
            return "တစ်လုံးပဲထည့်ပါ"
        if letter in self.guessed:
            return f"'{letter}' ကိုပြောပြီးသား"
            
        self.guessed.append(letter)
        
        if letter in self.word:
            for i, ch in enumerate(self.word):
                if ch == letter:
                    self.display[i] = letter
            msg = f"✅ မှန်တယ်!\n{' '.join(self.display)}"
        else:
            self.tries -= 1
            msg = f"❌ မှားတယ်! ကြိုးဆွဲထည့်လိုက်ပြီ...\n{' '.join(self.display)}\nအကြိမ် {self.tries} ကျန်တယ်"
            
        if "_" not in self.display:
            self.started = False
            msg += f"\n🎉 အနိုင်ရသွားပြီ! စကားလုံးက '{self.word}'"
            db.update_score(user_id, "hangman", 5)
        elif self.tries == 0:
            self.started = False
            msg += f"\n💀 ရှုံးသွားပြီ! စကားလုံးက '{self.word}'"
            
        self._save()
        return msg
