import asyncio
import json
import logging
import os
import secrets
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# دریافت متغیرهای محیطی
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_IDS_RAW = os.environ.get("ADMIN_IDS", "")
# ساخت لیست عددی از ادمین‌ها
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    raise ValueError("متغیر BOT_TOKEN در Render ست نشده است!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_FILE = "videos_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading DB: {e}")
        return {}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving DB: {e}")

# تابع حذف پیام بعد از ۳۰ ثانیه
async def delete_message_later(chat_id: int, message_id: int, delay: int = 30):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.warning(f"Failed to delete message: {e}")

# هندلر دستور استارت (هم استارت ساده هم با لینک ویدیو)
@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandObject):
    args = command.args
    db = load_db()

    # اگر کاربر با لینک اختصاصی ویدیو وارد شده باشد
    if args and args in db:
        video_info = db[args]
        file_id = video_info.get("file_id")
        caption = video_info.get("caption", "")

        try:
            sent_msg = await message.answer_video(
                video=file_id,
                caption=caption or "🎬 این ویدیو پس از ۳۰ ثانیه به صورت خودکار حذف خواهد شد."
            )
            # زمان‌بندی حذف پیام بعد از ۳۰ ثانیه
            asyncio.create_task(delete_message_later(message.chat.id, sent_msg.message_id, 30))
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await message.answer("⚠️ متأسفانه در ارسال ویدیو مشکلی پیش آمد.")
        return

    # اگر فقط استارت ساده زده باشد
    await message.answer("سلام! خیلی خوش اومدی به ربات ما. امیدوارم لذت ببرید! 💫")

# هندلر دریافت ویدیو (فقط برای ادمین‌ها)
@dp.message(F.video)
async def video_handler(message: Message):
    # چک کردن دسترسی ادمین
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔️ شما دسترسی لازم برای آپلود و تولید لینک ویدیو را ندارید.")
        return

    file_id = message.video.file_id
    caption = message.caption or ""
    video_key = "vid_" + secrets.token_urlsafe(8)

    db = load_db()
    db[video_key] = {
        "file_id": file_id,
        "caption": caption
    }
    save_db(db)

    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={video_key}"

    await message.reply(
        f"✅ **ویدیو با موفقیت ذخیره شد!**\n\n"
        f"🔗 **لینک دائمی ویدیو:**\n`{link}`\n\n"
        f"*(هر کاربری روی این لینک کلیک کند و Start را بزند، ویدیو را دریافت می‌کند و پیام ارسالی بعد از ۳۰ ثانیه برای او حذف می‌شود.)*",
        parse_mode="Markdown"
    )

# وب‌سرور سبک برای زنده نگه داشتن سرویس در Render
async def handle_ping(request):
    return web.Response(text="Bot is running perfectly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/ping", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web server started on port {port}")

async def main():
    await start_web_server()
    # پاک کردن وب‌هوک و آپدیت‌های معلق قدیمی
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot polling started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
