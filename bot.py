import os
import json
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

# لیست آیدی عددی تلگرام ادمین‌ها (با کاما جدا کنید یا در متغیر رندر ADMIN_IDS قرار دهید)
# مثال: ADMIN_IDS = "123456789,987654321"
admin_env = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(i.strip()) for i in admin_env.split(",") if i.strip().isdigit()]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_FILE = "videos_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving database: {e}")

# وب‌سرور برای زنده ماندن ربات در رندر
async def handle_ping(request):
    return web.Response(text="Bot is online and working!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Web server started on port {PORT}")

# مدیریت دستور start چه ساده و چه با لینک (Direct command handler)
@dp.message(Command("start"))
async def handle_start(message: Message):
    text_parts = message.text.strip().split(maxsplit=1)
    
    # اگر لینک همراه با پارامتر باشد (مانند /start v_123_456)
    if len(text_parts) > 1:
        link_key = text_parts[1].strip()
        db = load_db()
        video_id = db.get(link_key)
        
        if video_id:
            try:
                sent_video = await message.answer_video(
                    video=video_id,
                    caption="🎬 **ویدیوی درخواستی شما دریافت شد!**\n\n⏳ *توجه: این پیام پس از ۳۰ ثانیه حذف خواهد شد.*"
                )
                # حذف پیام ویدیو بعد از ۳۰ ثانیه
                await asyncio.sleep(30)
                try:
                    await sent_video.delete()
                except Exception as e:
                    logging.error(f"Error deleting video: {e}")
            except Exception as err:
                logging.error(f"Error sending video: {err}")
                await message.answer("❌ خطا در بارگذاری و ارسال ویدیو.")
        else:
            await message.answer("❌ متأسفانه این ویدیو یافت نشد یا لینک نامعتبر است.")
    else:
        # وقتی کاربر استارت خالی می‌زند
        welcome_text = (
            "سلام! خیلی خوش اومدی به ربات ما.\n\n"
            "امیدوارم لذت ببرید! 💫"
        )
        await message.answer(welcome_text)

# دریافت ویدیو و ساخت لینک اختصاصی (فقط مخصوص ادمین‌ها)
@dp.message(F.video)
async def handle_video_upload(message: Message):
    user_id = message.from_user.id
    
    # بررسی اینکه آیا کاربر ادمین است یا خیر (اگر ADMIN_IDS تنظیم نشده باشد، به همه موقتاً اجازه می‌دهد)
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await message.reply("⛔ شما دسترسی ساخت لینک برای ویدیو را ندارید.")
        return

    video_id = message.video.file_id
    link_key = f"v_{message.message_id}_{user_id}"
    
    db = load_db()
    db[link_key] = video_id
    save_db(db)
    
    bot_info = await bot.get_me()
    share_link = f"https://t.me/{bot_info.username}?start={link_key}"
    
    await message.reply(
        f"✅ **ویدیو ذخیره شد!**\n\n"
        f"🔗 **لینک اختصاصی:**\n`{share_link}`"
    )

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
