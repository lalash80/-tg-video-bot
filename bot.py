import os
import json
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_FILE = "videos_db.json"

# توابع ذخیره و خواندن دائمی اطلاعات ویدیوها
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

# وب‌سرور برای زنده ماندن ربات در سرور رندر
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

# ۱. وقتی کاربر با لینک اختصاصی وارد ربات می‌شود
@dp.message(CommandStart(deep_link=True))
async def handle_start_deep_link(message: Message, command: CommandObject):
    link_key = command.args.strip()
    db = load_db()
    video_id = db.get(link_key)
    
    if video_id:
        # ارسال ویدیو به کاربر
        sent_video = await message.answer_video(
            video=video_id,
            caption="🎬 **ویدیوی درخواستی شما با موفقیت دریافت شد!**\n\n⏳ *توجه: این ویدیو پس از ۳۰ ثانیه به صورت خودکار حذف خواهد شد.*"
        )
        
        # ۳۰ ثانیه شمارش معکوس و حذف پیام
        await asyncio.sleep(30)
        try:
            await sent_video.delete()
            await message.answer("⏱️ **مهلت تماشای ویدیو به پایان رسید.**\n\n✨ اگر مجدداً قصد تماشای آن را دارید، می‌توانید دوباره روی همان لینک اختصاصی کلیک کنید.")
        except Exception as e:
            logging.error(f"Error deleting video: {e}")
    else:
        await message.answer("❌ متأسفانه این لینک نامعتبر است یا ویدیوی مربوطه پیدا نشد.")

# ۲. پیام شروع ساده و شیک (بدون نام کاربر و راهنمای اضافه)
@dp.message(CommandStart())
async def handle_start_plain(message: Message):
    welcome_text = (
        "سلام! خیلی خوش اومدی به ربات ما.\n\n"
        "امیدوارم لذت ببرید! 💫"
    )
    await message.answer(welcome_text)

# ۳. دریافت ویدیو از ادمین و ساخت لینک دائمی
@dp.message(F.video)
async def handle_video_upload(message: Message):
    video_id = message.video.file_id
    link_key = f"v_{message.message_id}_{message.from_user.id}"
    
    # ذخیره در دیتابیس فایل
    db = load_db()
    db[link_key] = video_id
    save_db(db)
    
    bot_info = await bot.get_me()
    share_link = f"https://t.me/{bot_info.username}?start={link_key}"
    
    await message.reply(
        f"✅ **ویدیو با موفقیت ذخیره شد!**\n\n"
        f"🔗 **لینک اختصاصی ویدیو:**\n`{share_link}`"
    )

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
