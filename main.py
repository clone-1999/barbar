import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from config import config
from database import db

app = Client("game_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN)

# === Start Command ===
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🃏 UNO", callback_data="game_uno")],
        [InlineKeyboardButton("🐺 Werewolf", callback_data="game_werewolf")],
        [InlineKeyboardButton("❓ Quiz", callback_data="game_quiz")],
        [InlineKeyboardButton("🪨 RPS", callback_data="game_rps")],
        [InlineKeyboardButton("🪢 Hangman", callback_data="game_hangman")],
        [InlineKeyboardButton("🏆 Top Scores", callback_data="game_top")]
    ])
    await message.reply(
        "🎮 **ဟိုင်း! ဂိမ်းတစ်ခုရွေးပါ**\n\n"
        "အုပ်စုထဲမှာ ဆော့ချင်ရင် ဒီ Bot ကို Group ထဲထည့်ပြီး သုံးပါ။",
        reply_markup=buttons
    )

# === Group ထဲမှာ /games ဆိုရင် Button ပြမယ် ===
@app.on_message(filters.command("games") & filters.group)
async def games_menu(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🃏 UNO", callback_data="group_uno")],
        [InlineKeyboardButton("🐺 Werewolf", callback_data="group_werewolf")],
        [InlineKeyboardButton("❓ Quiz", callback_data="group_quiz")],
        [InlineKeyboardButton("🪨 RPS", callback_data="group_rps")],
        [InlineKeyboardButton("🪢 Hangman", callback_data="group_hangman")],
        [InlineKeyboardButton("❌ Cancel Game", callback_data="group_cancel")]
    ])
    await message.reply("🎮 **ဂိမ်းတစ်ခုရွေးပါ**", reply_markup=buttons)

# === Button Click Handler ===
@app.on_callback_query()
async def handle_callback(client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    message = callback_query.message
    
    await callback_query.answer()  # loading ပျောက်ဖို့
    
    # === UNO ===
    if data == "group_uno":
        game_id = f"uno_{chat_id}"
        if db.get_game(game_id):
            await message.reply("⚠️ UNO ဂိမ်းရှိနေပြီးသား။")
            return
        db.save_game(game_id, "uno", {"players": [user_id], "started": False})
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Join", callback_data=f"join_uno_{chat_id}")],
            [InlineKeyboardButton("▶️ Start", callback_data=f"start_uno_{chat_id}")]
        ])
        await message.reply(
            f"🃏 **UNO ဂိမ်းစပြီ!**\n"
            f"👤 {callback_query.from_user.first_name} က စထားတယ်\n"
            f"လူ {len(db.get_game(game_id)['players'])} ယောက်ပါတယ်",
            reply_markup=buttons
        )
        
    # === Quiz ===
    elif data == "group_quiz":
        game_id = f"quiz_{chat_id}"
        if db.get_game(game_id):
            await message.reply("⚠️ Quiz ဂိမ်းရှိနေပြီးသား။")
            return
            
        questions = [
            {"q": "မြန်မာနိုင်ငံရဲ့မြို့တော်က?", "a": "နေပြည်တော်", "opts": ["ရန်ကုန်", "မန္တလေး", "နေပြည်တော်", "ပဲခူး"]},
            {"q": "၁+၁ က?", "a": "၂", "opts": ["၁", "၂", "၃", "၄"]},
        ]
        db.save_game(game_id, "quiz", {"questions": questions, "current": 0, "scores": {}, "players": []})
        
        q = questions[0]
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("1️⃣", callback_data=f"quiz_0_{chat_id}"),
             InlineKeyboardButton("2️⃣", callback_data=f"quiz_1_{chat_id}"),
             InlineKeyboardButton("3️⃣", callback_data=f"quiz_2_{chat_id}"),
             InlineKeyboardButton("4️⃣", callback_data=f"quiz_3_{chat_id}")]
        ])
        await message.reply(f"❓ {q['q']}", reply_markup=buttons)
        
    # === RPS ===
    elif data == "group_rps":
        game_id = f"rps_{chat_id}"
        if db.get_game(game_id):
            await message.reply("⚠️ RPS ဂိမ်းရှိနေပြီးသား။")
            return
        db.save_game(game_id, "rps", {"players": [user_id], "choices": {}, "started": False})
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🪨 Rock", callback_data=f"rps_rock_{chat_id}"),
             InlineKeyboardButton("📄 Paper", callback_data=f"rps_paper_{chat_id}"),
             InlineKeyboardButton("✂️ Scissors", callback_data=f"rps_scissors_{chat_id}")]
        ])
        await message.reply(
            f"🪨📄✂️ **RPS စပြီ!**\n"
            f"👤 {callback_query.from_user.first_name} က စထားတယ်\n"
            f"ရွေးချယ်ပါ။",
            reply_markup=buttons
        )
        
    # === Cancel ===
    elif data == "group_cancel":
        for gtype in ["uno", "werewolf", "quiz", "rps", "hangman"]:
            db.delete_game(f"{gtype}_{chat_id}")
        await message.reply("✅ ဂိမ်းအကုန်ဖျက်လိုက်ပြီ!")

    # === Join UNO ===
    elif data.startswith("join_uno_"):
        chat_id = int(data.split("_")[2])
        game_id = f"uno_{chat_id}"
        data_game = db.get_game(game_id)
        if not data_game:
            await message.reply("⚠️ ဂိမ်းမရှိတော့ဘူး။")
            return
        if user_id in data_game["players"]:
            await message.reply("မင်းပါနေပြီးသား။")
            return
        data_game["players"].append(user_id)
        db.save_game(game_id, "uno", data_game)
        await message.reply(f"✅ {callback_query.from_user.first_name} ပါဝင်သွားပြီ! ({len(data_game['players'])} ယောက်)")

    # === Start UNO ===
    elif data.startswith("start_uno_"):
        chat_id = int(data.split("_")[2])
        game_id = f"uno_{chat_id}"
        data_game = db.get_game(game_id)
        if not data_game:
            await message.reply("⚠️ ဂိမ်းမရှိတော့ဘူး။")
            return
        if len(data_game["players"]) < 2:
            await message.reply("⚠️ လူ ၂ ယောက်အနည်းဆုံးလိုပါတယ်။")
            return
        await message.reply("🃏 UNO စပြီ! /play နဲ့ကစားပါ။")
        
    # === Quiz Answer ===
    elif data.startswith("quiz_"):
        parts = data.split("_")
        idx = int(parts[1])
        chat_id = int(parts[2])
        game_id = f"quiz_{chat_id}"
        data_game = db.get_game(game_id)
        if not data_game:
            await message.reply("⚠️ ဂိမ်းမရှိတော့ဘူး။")
            return
            
        q = data_game["questions"][data_game["current"]]
        if q["opts"][idx] == q["a"]:
            data_game["scores"][user_id] = data_game["scores"].get(user_id, 0) + 1
            await message.reply(f"✅ {callback_query.from_user.first_name} မှန်ပါတယ်!")
        else:
            await message.reply(f"❌ မှားပါတယ်။ အဖြေက {q['a']}")
            
        data_game["current"] += 1
        if data_game["current"] >= len(data_game["questions"]):
            result = "🏆 မေးခွန်းအကုန်ပြီးပါပြီ!\n"
            sorted_scores = sorted(data_game["scores"].items(), key=lambda x: x[1], reverse=True)
            for i, (uid, score) in enumerate(sorted_scores[:5], 1):
                result += f"{i}. {uid}: {score} မှတ်\n"
            await message.reply(result)
            db.delete_game(game_id)
        else:
            db.save_game(game_id, "quiz", data_game)
            q2 = data_game["questions"][data_game["current"]]
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("1️⃣", callback_data=f"quiz_0_{chat_id}"),
                 InlineKeyboardButton("2️⃣", callback_data=f"quiz_1_{chat_id}"),
                 InlineKeyboardButton("3️⃣", callback_data=f"quiz_2_{chat_id}"),
                 InlineKeyboardButton("4️⃣", callback_data=f"quiz_3_{chat_id}")]
            ])
            await message.reply(f"❓ {q2['q']}", reply_markup=buttons)

    # === RPS Choices ===
    elif data.startswith("rps_"):
        parts = data.split("_")
        choice = parts[1]
        chat_id = int(parts[2])
        game_id = f"rps_{chat_id}"
        data_game = db.get_game(game_id)
        if not data_game:
            await message.reply("⚠️ ဂိမ်းမရှိတော့ဘူး။")
            return
            
        if "choices" not in data_game:
            data_game["choices"] = {}
        data_game["choices"][user_id] = choice
        db.save_game(game_id, "rps", data_game)
        
        if len(data_game["choices"]) == 2:
            p1, p2 = list(data_game["choices"].keys())
            c1, c2 = data_game["choices"][p1], data_game["choices"][p2]
            emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
            msg = f"{p1}: {emojis[c1]}  VS  {p2}: {emojis[c2]}\n"
            
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
            await message.reply(msg)
            db.delete_game(game_id)
        else:
            await message.reply(f"✅ {callback_query.from_user.first_name} ရွေးပြီးပြီ! နောက်တစ်ယောက်စောင့်နေ")

# === Top Scores ===
@app.on_message(filters.command("top") & filters.group)
async def top_scores(client, message):
    scores = db.get_top_scores("quiz", 5)
    if not scores:
        await message.reply("📊 ရမှတ်မရှိသေးဘူး။")
        return
    msg = "🏆 ထိပ်ဆုံး ၅ ယောက်\n"
    for i, s in enumerate(scores, 1):
        player = db.get_player(s["user_id"])
        name = player["first_name"] if player else str(s["user_id"])
        msg += f"{i}. {name}: {s['score']} မှတ်\n"
    await message.reply(msg)

# === Broadcast (Owner Only) ===
@app.on_message(filters.command("broadcast") & filters.private & filters.user(config.OWNER_ID))
async def broadcast_cmd(client, message):
    if not message.reply_to_message:
        await message.reply("❗ /broadcast ကို reply တစ်ခုနဲ့သုံးပါ။")
        return
    msg = message.reply_to_message.text
    if not msg:
        await message.reply("❗ စာသားပဲပို့လို့ရတယ်။")
        return
    chat_ids = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            chat_ids.append(dialog.chat.id)
    sent = 0
    for cid in chat_ids:
        try:
            await client.send_message(cid, f"📢 {msg}")
            sent += 1
            await asyncio.sleep(0.5)
        except:
            pass
    await message.reply(f"✅ {sent} အုပ်စုကိုပို့ပြီးပြီ။")

# === Main ===
async def main():
    await app.start()
    print(f"✅ Bot started as @{(await app.get_me()).username}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    app.run(main())
