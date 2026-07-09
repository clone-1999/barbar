"""
Multi-Game Telegram Bot
ဂိမ်းအစုံပါတဲ့ Bot - UNO, Werewolf, Quiz, RPS, Hangman
Owner ID တစ်ယောက်တည်းအတွက် Broadcast ပါ
MongoDB နဲ့ Data သိမ်း၊ Auto Restart ပါ
"""

import asyncio
import logging
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType

# Config နဲ့ Database
from config import config
from database import db

# ဂိမ်းအကုန်ယူမယ်
from games import UnoGame, WerewolfGame, QuizGame, RPSGame, HangmanGame

# Owner Tools
from owner_tools import setup_owner_handlers, is_owner

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Pyrogram Client
app = Client(
    "game_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# === Active Games Storage ===
active_games = {
    "uno": {},
    "werewolf": {},
    "quiz": {},
    "rps": {},
    "hangman": {}
}

# === Helper Functions ===
def get_game_instance(game_type, chat_id):
    """ဂိမ်း instance ပြန်ပေးမယ်"""
    if game_type == "uno":
        return UnoGame(chat_id)
    elif game_type == "werewolf":
        return WerewolfGame(chat_id)
    elif game_type == "quiz":
        return QuizGame(chat_id)
    elif game_type == "rps":
        return RPSGame(chat_id)
    elif game_type == "hangman":
        return HangmanGame(chat_id)
    return None

def get_game_players(game_type, chat_id):
    """ဂိမ်းထဲကလူတွေပြန်မယ်"""
    game = get_game_instance(game_type, chat_id)
    if game and game.started:
        return list(game.players.keys()) if hasattr(game, 'players') else []
    return []

# === Start Command ===
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    """Bot စတင်တဲ့အခါ"""
    user = message.from_user
    db.add_player(user.id, user.username, user.first_name)
    
    await message.reply(
        f"🎮 ဟိုင်း {user.first_name}!\n\n"
        "ကျွန်တော်က Multi-Game Bot ပါ။\n"
        "အုပ်စုထဲမှာ အောက်ပါ Command တွေသုံးပြီး ဆော့လို့ရပါတယ်:\n\n"
        "🃏 `/uno` - UNO ဂိမ်းစမယ်\n"
        "🐺 `/werewolf` - ဝံပုလွေဂိမ်းစမယ်\n"
        "❓ `/quiz` - ဉာဏ်စမ်းစမယ်\n"
        "🪨 `/rps` - ကျောက်/ကတ်ကြေး/စက္ကူစမယ်\n"
        "🪢 `/hangman` - ကြိုးဆွဲစမယ်\n\n"
        "📊 `/top` - ထိပ်ဆုံး ၁၀ ယောက်ပြမယ်\n"
        "ℹ️ `/help` - အကူအညီ\n\n"
        "ပျော်ရွှင်စွာဆော့ကြပါ! 🎉"
    )

# === Help Command ===
@app.on_message(filters.command("help") & filters.group)
async def help_cmd(client, message: Message):
    """အကူအညီ"""
    help_text = """
🎮 **ဂိမ်း Command တွေ**

🃏 **UNO**
`/uno` - UNO စမယ်
`/join` - ဂိမ်းထဲဝင်မယ်
`/play [ကတ်နံပါတ်]` - ကတ်ကစားမယ်
`/draw` - ကတ်ဆွဲမယ်
`/color [အရောင်]` - အရောင်ရွေးမယ် (wild)
`/status` - ဂိမ်းအခြေအနေ

🐺 **Werewolf**
`/werewolf` - ဂိမ်းစမယ်
`/join` - ပါဝင်မယ်
`/kill [@username]` - ညဘက်သတ်မယ်
`/see [@username]` - ဗေဒင်ကြည့်မယ်
`/save [@username]` - ကယ်မယ်
`/vote [@username]` - မဲပေးမယ်

❓ **Quiz**
`/quiz` - ဉာဏ်စမ်းစမယ်
`/1`, `/2`, `/3`, `/4` - အဖြေရွေးမယ်

🪨 **RPS**
`/rps` - ဂိမ်းစမယ်
`/rock` - ကျောက်ရွေးမယ်
`/paper` - စက္ကူရွေးမယ်
`/scissors` - ကတ်ကြေးရွေးမယ်

🪢 **Hangman**
`/hangman` - ကြိုးဆွဲစမယ်
`/guess [စာလုံး]` - စာလုံးခန့်မှန်းမယ်

📊 **အခြား**
`/top` - ထိပ်ဆုံး ၁၀ ယောက်
`/cancel` - ဂိမ်းဖျက်မယ်
"""
    await message.reply(help_text)

# === UNO Commands ===
@app.on_message(filters.command("uno") & filters.group)
async def uno_start(client, message: Message):
    """UNO ဂိမ်းစမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = UnoGame(chat_id)
    if game.started:
        await message.reply("⚠️ UNO ဂိမ်းရှိနေပြီးသား။ `/join` နဲ့ဝင်ပါ။")
        return
        
    # ဂိမ်းအသစ်စမယ်
    game.players = {user_id: []}
    game.started = True
    game._save()
    
    await message.reply(
        f"🃏 **UNO ဂိမ်းစပြီ!**\n"
        f"👤 {message.from_user.first_name} က စထားတယ်\n\n"
        f"ပါဝင်ချင်ရင် `/join` ကိုနှိပ်ပါ\n"
        f"လူ ၂ ယောက်ရှိရင် `/start` နဲ့စပါ"
    )

@app.on_message(filters.command("join") & filters.group)
async def uno_join(client, message: Message):
    """UNO ဂိမ်းထဲဝင်မယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = UnoGame(chat_id)
    if not game.started:
        await message.reply("⚠️ ဂိမ်းမရှိသေးဘူး။ `/uno` နဲ့စပါ။")
        return
        
    if user_id in game.players:
        await message.reply("မင်းပါနေပြီးသား။")
        return
        
    if len(game.players) >= 10:
        await message.reply("⚠️ လူ ၁၀ ယောက်ပြည့်သွားပြီ။")
        return
        
    game.players[user_id] = []
    game._save()
    
    await message.reply(f"✅ {message.from_user.first_name} ပါဝင်သွားပြီ! ({len(game.players)}/10)")

@app.on_message(filters.command("start") & filters.group)
async def uno_start_game(client, message: Message):
    """UNO ဂိမ်းစတယ်"""
    chat_id = message.chat.id
    
    game = UnoGame(chat_id)
    if not game.started:
        await message.reply("⚠️ ဂိမ်းမရှိဘူး။ `/uno` နဲ့စပါ။")
        return
        
    if len(game.players) < 2:
        await message.reply("⚠️ လူ ၂ ယောက်အနည်းဆုံးလိုပါတယ်။ `/join` နဲ့ခေါ်ပါ။")
        return
        
    # ကတ်စပေးမယ်
    import random
    game.deck = game._build_deck()
    for pid in game.players:
        game.players[pid] = [game.deck.pop() for _ in range(7)]
        
    # ပထမကတ်ချမယ်
    first_card = game.deck.pop()
    while first_card["value"] in ["wild", "wild_draw4"]:
        game.deck.append(first_card)
        random.shuffle(game.deck)
        first_card = game.deck.pop()
        
    game.discard_pile.append(first_card)
    game.current_color = first_card["color"]
    game.current_value = first_card["value"]
    game.turn_index = 0
    game._save()
    
    players_list = list(game.players.keys())
    msg = f"🃏 **UNO စပြီ!**\n"
    msg += f"ပထမကတ်: {first_card['color']} {first_card['value']}\n"
    msg += f"ပထမလှည့်: {players_list[0]}\n\n"
    msg += "📌 `/play [ကတ်နံပါတ်]` နဲ့ကစားပါ\n"
    msg += "📌 `/draw` နဲ့ကတ်ဆွဲပါ"
    
    await message.reply(msg)

@app.on_message(filters.command("play") & filters.group)
async def uno_play(client, message: Message):
    """UNO ကတ်ကစားမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("❗ `/play [ကတ်နံပါတ်]` လို့သုံးပါ")
        return
        
    try:
        card_index = int(parts[1])
    except:
        await message.reply("❗ နံပါတ်ပဲထည့်ပါ")
        return
        
    game = UnoGame(chat_id)
    if not game.started:
        await message.reply("⚠️ ဂိမ်းမရှိဘူး")
        return
        
    result = game.play_card(user_id, card_index)
    await message.reply(result)

@app.on_message(filters.command("draw") & filters.group)
async def uno_draw(client, message: Message):
    """UNO ကတ်ဆွဲမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = UnoGame(chat_id)
    if not game.started:
        await message.reply("⚠️ ဂိမ်းမရှိဘူး")
        return
        
    result = game.draw_card(user_id)
    await message.reply(result)

@app.on_message(filters.command("status") & filters.group)
async def game_status(client, message: Message):
    """ဂိမ်းအခြေအနေကြည့်မယ်"""
    chat_id = message.chat.id
    game = UnoGame(chat_id)
    result = game.get_status()
    await message.reply(result)

# === Werewolf Commands ===
@app.on_message(filters.command("werewolf") & filters.group)
async def werewolf_start(client, message: Message):
    """Werewolf ဂိမ်းစမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = WerewolfGame(chat_id)
    if game.started:
        await message.reply("⚠️ ဝံပုလွေဂိမ်းရှိနေပြီးသား")
        return
        
    # စာရင်းသိမ်းမယ်
    game.players = {user_id: "villager"}
    game.alive = [user_id]
    game.started = True
    game.phase = "waiting"
    game._save()
    
    await message.reply(
        f"🐺 **ဝံပုလွေဂိမ်းစပြီ!**\n"
        f"👤 {message.from_user.first_name} က စထားတယ်\n\n"
        f"ပါဝင်ချင်ရင် `/join` ကိုနှိပ်ပါ\n"
        f"လူ ၅ ယောက်ရှိရင် `/start` နဲ့အလုပ်ခွဲပါမယ်"
    )

@app.on_message(filters.command("join") & filters.group)
async def werewolf_join(client, message: Message):
    """Werewolf ဂိမ်းထဲဝင်မယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = WerewolfGame(chat_id)
    if not game.started or game.phase != "waiting":
        await message.reply("⚠️ ဂိမ်းမရှိဘူး ဒါမှမဟုတ် စပြီးသား")
        return
        
    if user_id in game.players:
        await message.reply("မင်းပါနေပြီးသား")
        return
        
    game.players[user_id] = "villager"
    game.alive.append(user_id)
    game._save()
    
    await message.reply(f"✅ {message.from_user.first_name} ပါဝင်သွားပြီ! ({len(game.players)} ယောက်)")

@app.on_message(filters.command("start") & filters.group)
async def werewolf_start_game(client, message: Message):
    """Werewolf ဂိမ်းစတယ် (အလုပ်ခွဲ)"""
    chat_id = message.chat.id
    
    game = WerewolfGame(chat_id)
    if not game.started:
        await message.reply("⚠️ ဂိမ်းမရှိဘူး")
        return
        
    if len(game.players) < 5:
        await message.reply("⚠️ လူ ၅ ယောက်အနည်းဆုံးလိုပါတယ်")
        return
        
    # အလုပ်တွေခွဲပေးမယ်
    import random
    user_ids = list(game.players.keys())
    n = len(user_ids)
    werewolf_count = max(1, n // 4)
    
    roles = ["werewolf"] * werewolf_count
    roles.append("seer")
    if n >= 6:
        roles.append("doctor")
    if n >= 8:
        roles.append("hunter")
    roles.extend(["villager"] * (n - len(roles)))
    random.shuffle(roles)
    
    game.players = {uid: role for uid, role in zip(user_ids, roles)}
    game.alive = user_ids.copy()
    game.phase = "night"
    game._save()
    
    # ကိုယ့်အလုပ်ကိုကိုယ်ပြောပါမယ်
    for uid, role in game.players.items():
        try:
            await client.send_message(uid, f"🐺 မင်းက {role} ပါ။ ဂိမ်းစပြီ!")
        except:
            pass
            
    msg = f"🐺 **ဝံပုလွေဂိမ်းစပြီ!**\n"
    msg += f"👤 လူ {len(game.players)} ယောက်ပါတယ်\n"
    msg += f"🐺 ဝံပုလွေ {werewolf_count} ကောင်\n\n"
    msg += "🌙 ညဘက်ရောက်ပြီ!\n"
    msg += "ဝံပုလွေတွေ `/kill [@username]` နဲ့သတ်ပါ\n"
    msg += "ဗေဒင်ဆရာ `/see [@username]` နဲ့ကြည့်ပါ\n"
    msg += "ဆရာဝန် `/save [@username]` နဲ့ကယ်ပါ"
    
    await message.reply(msg)

@app.on_message(filters.command("kill") & filters.group)
async def werewolf_kill(client, message: Message):
    """ဝံပုလွေသတ်မယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    target = message.text.split()
    
    if len(target) < 2:
        await message.reply("❗ `/kill [@username]` လို့သုံးပါ")
        return
        
    game = WerewolfGame(chat_id)
    result = game.night_action(user_id, target[1])
    await message.reply(result)

@app.on_message(filters.command("see") & filters.group)
async def werewolf_see(client, message: Message):
    """ဗေဒင်ကြည့်မယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    target = message.text.split()
    
    if len(target) < 2:
        await message.reply("❗ `/see [@username]` လို့သုံးပါ")
        return
        
    game = WerewolfGame(chat_id)
    result = game.night_action(user_id, target[1])
    await message.reply(result)

@app.on_message(filters.command("save") & filters.group)
async def werewolf_save(client, message: Message):
    """ဆရာဝန်ကယ်မယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    target = message.text.split()
    
    if len(target) < 2:
        await message.reply("❗ `/save [@username]` လို့သုံးပါ")
        return
        
    game = WerewolfGame(chat_id)
    result = game.night_action(user_id, target[1])
    await message.reply(result)

@app.on_message(filters.command("vote") & filters.group)
async def werewolf_vote(client, message: Message):
    """မဲပေးမယ် (နေ့ဘက်)"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    target = message.text.split()
    
    if len(target) < 2:
        await message.reply("❗ `/vote [@username]` လို့သုံးပါ")
        return
        
    game = WerewolfGame(chat_id)
    result = game.vote(user_id, target[1])
    await message.reply(result)

# === Quiz Commands ===
@app.on_message(filters.command("quiz") & filters.group)
async def quiz_start(client, message: Message):
    """Quiz စမယ်"""
    chat_id = message.chat.id
    
    game = QuizGame(chat_id)
    if game.started:
        await message.reply("⚠️ ဉာဏ်စမ်းရှိနေပြီးသား")
        return
        
    # လူစာရင်းကောက်မယ် (ဒီမှာ အုပ်စုထဲကလူအကုန်ထည့်)
    user_ids = []
    async for member in client.get_chat_members(chat_id):
        if not member.user.is_bot:
            user_ids.append(member.user.id)
            
    if len(user_ids) < 2:
        await message.reply("⚠️ လူ ၂ ယောက်အနည်းဆုံးလိုပါတယ်")
        return
        
    game.players = {uid: False for uid in user_ids[:10]}  # ၁၀ ယောက်အထိ
    game.scores = {uid: 0 for uid in game.players}
    game.current_q = 0
    game.started = True
    game._save()
    
    # ပထမမေးခွန်းထုတ်မယ်
    q_data = game.QUESTIONS[0]
    msg = f"❓ **ဉာဏ်စမ်းစပြီ!**\n"
    msg += f"👤 လူ {len(game.players)} ယောက်ပါတယ်\n\n"
    msg += f"{q_data['q']}\n"
    for i, opt in enumerate(q_data["opts"], 1):
        msg += f"{i}. {opt}\n"
    msg += f"\n📌 `/1`, `/2`, `/3`, `/4` နဲ့ဖြေပါ"
    
    await message.reply(msg)

@app.on_message(filters.command(["1", "2", "3", "4"]) & filters.group)
async def quiz_answer(client, message: Message):
    """Quiz အဖြေရွေးမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    answer_idx = int(message.text.replace("/", ""))
    
    game = QuizGame(chat_id)
    result = game.answer(user_id, answer_idx)
    await message.reply(result)

# === RPS Commands ===
@app.on_message(filters.command("rps") & filters.group)
async def rps_start(client, message: Message):
    """RPS စမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = RPSGame(chat_id)
    if game.started:
        await message.reply("⚠️ RPS ဂိမ်းရှိနေပြီးသား")
        return
        
    # ဒီဂိမ်းက ၂ ယောက်ပဲဆော့လို့ရတယ်
    game.players = {user_id: None}
    game.started = True
    game._save()
    
    await message.reply(
        f"🪨📄✂️ **RPS စပြီ!**\n"
        f"👤 {message.from_user.first_name} က စထားတယ်\n\n"
        f"ပါဝင်ချင်ရင် `/join` ကိုနှိပ်ပါ\n"
        f"လူ ၂ ယောက်ရှိရင် `/rock`, `/paper`, `/scissors` နဲ့ရွေးပါ"
    )

@app.on_message(filters.command("rock") & filters.group)
async def rps_rock(client, message: Message):
    """ကျောက်ရွေးမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = RPSGame(chat_id)
    result = game.choose(user_id, "rock")
    await message.reply(result)

@app.on_message(filters.command("paper") & filters.group)
async def rps_paper(client, message: Message):
    """စက္ကူရွေးမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = RPSGame(chat_id)
    result = game.choose(user_id, "paper")
    await message.reply(result)

@app.on_message(filters.command("scissors") & filters.group)
async def rps_scissors(client, message: Message):
    """ကတ်ကြေးရွေးမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = RPSGame(chat_id)
    result = game.choose(user_id, "scissors")
    await message.reply(result)

# === Hangman Commands ===
@app.on_message(filters.command("hangman") & filters.group)
async def hangman_start(client, message: Message):
    """Hangman စမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    game = HangmanGame(chat_id)
    if game.started:
        await message.reply("⚠️ ကြိုးဆွဲဂိမ်းရှိနေပြီးသား")
        return
        
    result = game.start(user_id)
    await message.reply(result)

@app.on_message(filters.command("guess") & filters.group)
async def hangman_guess(client, message: Message):
    """စာလုံးခန့်မှန်းမယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("❗ `/guess [စာလုံး]` လို့သုံးပါ")
        return
        
    letter = parts[1]
    game = HangmanGame(chat_id)
    result = game.guess(user_id, letter)
    await message.reply(result)

# === Top Scores Command ===
@app.on_message(filters.command("top") & filters.group)
async def top_scores(client, message: Message):
    """ထိပ်ဆုံး ၁၀ ယောက်ပြမယ်"""
    game_type = "quiz"  # default
    if len(message.text.split()) > 1:
        game_type = message.text.split()[1]
        
    scores = db.get_top_scores(game_type, 10)
    
    if not scores:
        await message.reply(f"📊 {game_type} အတွက် ရမှတ်မရှိသေးဘူး")
        return
        
    msg = f"🏆 **{game_type.upper()} ထိပ်ဆုံး ၁၀ ယောက်**\n"
    msg += "━━━━━━━━━━━━━━━━\n"
    for i, score in enumerate(scores, 1):
        user_id = score["user_id"]
        points = score["score"]
        player = db.get_player(user_id)
        name = player["first_name"] if player else str(user_id)
        msg += f"{i}. {name}: {points} မှတ်\n"
        
    await message.reply(msg)

# === Cancel Command ===
@app.on_message(filters.command("cancel") & filters.group)
async def cancel_game(client, message: Message):
    """ဂိမ်းဖျက်မယ်"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # ဂိမ်းအကုန်ဖျက်မယ်
    for game_type in ["uno", "werewolf", "quiz", "rps", "hangman"]:
        game = get_game_instance(game_type, chat_id)
        if game and game.started:
            game.started = False
            game._save()
            
    await message.reply(f"✅ {message.from_user.first_name} ဂိမ်းအကုန်ဖျက်လိုက်ပြီ!")

# === Owner Broadcast ===
@app.on_message(filters.command("broadcast") & filters.private & filters.user(config.OWNER_ID))
async def broadcast_cmd(client, message: Message):
    """Broadcast ပို့မယ် (Owner ပဲသုံးလို့ရ)"""
    if not message.reply_to_message:
        await message.reply("❗ `/broadcast` ကို reply တစ်ခုနဲ့သုံးပါ")
        return
        
    msg = message.reply_to_message.text or message.reply_to_message.caption
    if not msg:
        await message.reply("❗ စာသားပါတဲ့မက်ဆေ့ချ်ပဲပို့လို့ရတယ်")
        return
        
    # Bot ရှိတဲ့ Group တွေအကုန်ရှာမယ်
    chat_ids = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            chat_ids.append(dialog.chat.id)
            
    if not chat_ids:
        await message.reply("⚠️ ဘယ် Group မှမရှိဘူး")
        return
        
    sent = 0
    failed = 0
    
    for cid in chat_ids:
        try:
            await client.send_message(cid, f"📢 {msg}")
            sent += 1
            await asyncio.sleep(0.5)  # Flood မဖြစ်အောင်
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send to {cid}: {e}")
            
    db.save_broadcast(msg, chat_ids)
    await message.reply(f"✅ {sent} အုပ်စုကိုပို့ပြီးပြီ!\n❌ {failed} အုပ်စု မအောင်မြင်")

# === Auto Restart Check ===
async def auto_restart_check():
    """ပိသွားတဲ့ဂိမ်းတွေကို auto ပြန်ဖျက်မယ်"""
    while True:
        try:
            # Database ထဲက restart flag တွေစစ်မယ်
            for game_type in ["uno", "werewolf", "quiz", "rps", "hangman"]:
                game = get_game_instance(game_type, 0)  # chat_id 0 နဲ့မစစ်ရ
                # ဒီနေရာမှာ ကိုယ်ပိုင် logic ထည့်ချင်ရင်ထည့်
                
            await asyncio.sleep(60)  # ၁ မိနစ်တစ်ခါစစ်မယ်
        except Exception as e:
            logger.error(f"Auto restart check error: {e}")
            await asyncio.sleep(60)

# === Main ===
async def main():
    """Bot စတင်မယ်"""
    logger.info("🚀 Bot is starting...")
    
    # Auto restart check ကို background မှာ run မယ်
    asyncio.create_task(auto_restart_check())
    
    # Pyrogram ကို run မယ်
    await app.start()
    logger.info(f"✅ Bot started as @{(await app.get_me()).username}")
    
    # Owner ကို noti ပို့မယ်
    try:
        await app.send_message(config.OWNER_ID, "🚀 Bot စပြီး! ဂိမ်းအကုန်အဆင်သင့်ပါပြီ။")
    except:
        pass
        
    # Idle (bot ကို ဖွင့်ထားမယ်)
    await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
