import random
import time
from database import db

class UnoGame:
    """UNO ဂိမ်း - ၂ ယောက်မှ ၁၀ ယောက်အထိဆော့လို့ရတယ်"""
    
    COLORS = ["red", "blue", "green", "yellow"]
    VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "skip", "reverse", "draw2"]
    WILD = ["wild", "wild_draw4"]
    
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.game_id = f"uno_{chat_id}"
        self.players = {}
        self.deck = []
        self.discard_pile = []
        self.current_color = None
        self.current_value = None
        self.turn_index = 0
        self.direction = 1  # 1 = clockwise, -1 = counter
        self.started = False
        self._load()
        
    def _load(self):
        """သိမ်းထားတဲ့ game state ပြန်ယူမယ်"""
        data = db.get_game(self.game_id)
        if data:
            self.__dict__.update(data)
            
    def _save(self):
        """Game state သိမ်းမယ်"""
        db.save_game(self.game_id, "uno", {
            "players": self.players,
            "deck": self.deck,
            "discard_pile": self.discard_pile,
            "current_color": self.current_color,
            "current_value": self.current_value,
            "turn_index": self.turn_index,
            "direction": self.direction,
            "started": self.started
        })
        
    def _build_deck(self):
        """ကတ်အကုန်ပြန်လုပ်မယ်"""
        deck = []
        for color in self.COLORS:
            for value in self.VALUES:
                deck.append({"color": color, "value": value})
                if value != "0":  # 0 က တစ်ကတ်ပဲရှိတယ်
                    deck.append({"color": color, "value": value})
        for _ in range(4):
            deck.append({"color": "wild", "value": "wild"})
            deck.append({"color": "wild", "value": "wild_draw4"})
        random.shuffle(deck)
        return deck
        
    def start_game(self, player_ids):
        """ဂိမ်းစမယ်"""
        if len(player_ids) < 2:
            return "လူ ၂ ယောက်အနည်းဆုံးလိုပါတယ်"
            
        self.players = {pid: [] for pid in player_ids}
        self.deck = self._build_deck()
        self.discard_pile = []
        self.started = True
        self.turn_index = 0
        self.direction = 1
        
        # ကတ်စပေးမယ် (၇ ကတ်စီ)
        for pid in player_ids:
            self.players[pid] = [self.deck.pop() for _ in range(7)]
            
        # ပထမဆုံးကတ်ချမယ်
        first_card = self.deck.pop()
        while first_card["value"] in ["wild", "wild_draw4"]:
            self.deck.append(first_card)
            random.shuffle(self.deck)
            first_card = self.deck.pop()
            
        self.discard_pile.append(first_card)
        self.current_color = first_card["color"]
        self.current_value = first_card["value"]
        
        self._save()
        return f"UNO စပြီ! ပထမကတ်: {first_card['color']} {first_card['value']}"
        
    def play_card(self, user_id, card_index, chosen_color=None):
        """ကတ်ကစားမယ်"""
        if not self.started:
            return "ဂိမ်းမစရသေးဘူး"
            
        if user_id not in self.players:
            return "မင်းဒီဂိမ်းထဲမပါဘူး"
            
        current_player = list(self.players.keys())[self.turn_index]
        if user_id != current_player:
            return "မင်းအလှည့်မဟုတ်ဘူး"
            
        hand = self.players[user_id]
        if card_index >= len(hand):
            return "ကတ်မရှိဘူး"
            
        card = hand[card_index]
        top_card = self.discard_pile[-1]
        
        # ကတ်ကစားလို့ရမရစစ်မယ်
        if card["color"] == "wild":
            if not chosen_color:
                return "အရောင်ရွေးပါ"
            card["chosen_color"] = chosen_color
            self.current_color = chosen_color
        elif card["color"] == self.current_color or card["value"] == self.current_value:
            self.current_color = card["color"]
            self.current_value = card["value"]
        else:
            return "ဒီကတ်မကစားရဘူး"
            
        # ကတ်ဖယ်ပြီး discard pile ထဲထည့်
        hand.pop(card_index)
        self.discard_pile.append(card)
        
        # Special cards
        if card["value"] == "skip":
            self.turn_index = (self.turn_index + self.direction) % len(self.players)
        elif card["value"] == "reverse":
            self.direction *= -1
        elif card["value"] == "draw2":
            next_player = list(self.players.keys())[(self.turn_index + self.direction) % len(self.players)]
            for _ in range(2):
                self.players[next_player].append(self.deck.pop())
        elif card["value"] == "wild_draw4":
            next_player = list(self.players.keys())[(self.turn_index + self.direction) % len(self.players)]
            for _ in range(4):
                self.players[next_player].append(self.deck.pop())
                
        # အနိုင်ရရင်
        if len(hand) == 0:
            self.started = False
            db.update_score(user_id, "uno", 10)
            self._save()
            return f"🎉 {user_id} အနိုင်ရသွားပြီ!"
            
        # နောက်လှည့်
        self.turn_index = (self.turn_index + self.direction) % len(self.players)
        self._save()
        return f"ကစားပြီး! နောက်လှည့်: {list(self.players.keys())[self.turn_index]}"
        
    def draw_card(self, user_id):
        """ကတ်ဆွဲမယ်"""
        if not self.started:
            return "ဂိမ်းမစရသေးဘူး"
            
        current_player = list(self.players.keys())[self.turn_index]
        if user_id != current_player:
            return "မင်းအလှည့်မဟုတ်ဘူး"
            
        if not self.deck:
            self.deck = self.discard_pile[:-1]
            random.shuffle(self.deck)
            self.discard_pile = [self.discard_pile[-1]]
            
        card = self.deck.pop()
        self.players[user_id].append(card)
        self.turn_index = (self.turn_index + self.direction) % len(self.players)
        self._save()
        return f"ကတ်တစ်ကတ်ဆွဲပြီး! နောက်လှည့်: {list(self.players.keys())[self.turn_index]}"
        
    def get_status(self):
        """ဂိမ်းအခြေအနေပြန်မယ်"""
        if not self.started:
            return "ဂိမ်းမစရသေးဘူး"
            
        msg = f"🎮 UNO - အလှည့်: {list(self.players.keys())[self.turn_index]}\n"
        msg += f"အရောင်: {self.current_color} | တန်ဖိုး: {self.current_value}\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        for pid, hand in self.players.items():
            msg += f"👤 {pid}: {len(hand)} ကတ်\n"
        return msg
