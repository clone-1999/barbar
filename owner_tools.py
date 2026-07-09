from pyrogram import Client, filters
from pyrogram.types import Message
from config import config
from database import db
import asyncio

async def is_owner(client, message):
    return message.from_user.id == config.OWNER_ID

def setup_owner_handlers(app):
    """Owner အတွက် command တွေ"""
    
    # === /broadcast ===
    @app.on_message(filters.command("broadcast") & filters.private & filters.user(config.OWNER_ID))
    async def broadcast_cmd(client, message: Message):
        """အုပ်စုအကုန်ကိုမက်ဆေ့ချ်ပို့မယ်"""
        if not message.reply_to_message:
            await message.reply("❗ reply တစ်ခုနဲ့သုံးပါ: /broadcast")
            return
            
        msg = message.reply_to_message.text or message.reply_to_message.caption
        if not msg:
            await message.reply("❗ စာသားပါတဲ့မက်ဆေ့ချ်ပဲပို့လို့ရတယ်")
            return
            
        # ဘယ် group တွေကိုပို့မယ်ဆိုတာ သိမ်းထား (ဒီမှာ manual ထည့်ထား)
        # ဒါမှမဟုတ် bot ရှိတဲ့ group အကုန် auto ရှာချင်ရင် အောက်က comment ဖြေပြီး သုံး
        chat_ids = []  # ဒီနေရာမှာ group id တွေထည့် [123, 456]
        
        if not chat_ids:
            # Auto: bot ရှိတဲ့ group အကုန်
            async for dialog in client.get_dialogs():
                if dialog.chat.type in ["group", "supergroup"]:
                    chat_ids.append(dialog.chat.id)
                    
        sent = 0
        for cid in chat_ids:
            try:
                await client.send_message(cid, f"📢 {msg}")
                sent += 1
                await asyncio.sleep(1)  # flood မဖြစ်အောင်
            except Exception as e:
                print(f"Failed to send to {cid}: {e}")
                
        db.save_broadcast(msg, chat_ids)
        await message.reply(f"✅ {sent} အုပ်စုကိုပို့ပြီးပြီ!")
        
    # === /restart_game ===
    @app.on_message(filters.command("restart") & filters.user(config.OWNER_ID))
    async def restart_cmd(client, message: Message):
        """ဂိမ်းတစ်ခုကို restart လုပ်မယ်"""
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("❗ သုံးပုံ: /rest
