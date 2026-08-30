import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

# توکن ربات از تنظیمات رندر خوانده می‌شود
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ذخیره موقت شناسه‌های ویدیو در حافظه
videos_db = {}

# وب‌سرور برای زنده نگه داشتن ربات در رندر
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Web server started on port {PORT}")

# وقتی کاربر روی لینک اختصاصی می‌زنه و ربات باز میشه
@dp.message(CommandStart(deep_link=True))
async def handle_start_deep_link(message: Message, command: CommandObject):
    link_key = command.args
    video_id = videos_db.get(link_key)
    
    if video_id:
        # ارسال ویدیو مستقیماً در چت خصوصی کاربر
        sent_video = await message.answer_video(
            video=video_id,
            caption="⚠️ این ویدیو پس از ۳۰ ثانیه به صورت خودکار حذف خواهد شد."
        )
        # ۳۰ ثانیه صبر و سپس حذف ویدیو
        await asyncio.sleep(30)
        try:
            await sent_video.delete()
        except Exception as e:
            logging.error(f"Error deleting video: {e}")
    else:
        await message.answer("❌ متأسفانه این ویدیو یافت نشد یا منقضی شده است.")

# وقتی کاربر استارت معمولی بدون لینک می‌زنه
@dp.message(CommandStart())
async def handle_start_plain(message: Message):
    await message.answer("👋 سلام! برای دریافت ویدیو از لینک اختصاصی استفاده کنید یا برای ساخت لینک، یک ویدیو به ربات ارسال کنید.")

# دریافت ویدیو از ادمین و تولید لینک اختصاصی
@dp.message(F.video)
async def handle_video_upload(message: Message):
    video_id = message.video.file_id
    link_key = f"vid_{message.message_id}"
    videos_db[link_key] = video_id
    
    bot_info = await bot.get_me()
    share_link = f"https://t.me/{bot_info.username}?start={link_key}"
    
    # فقط به خود شما لینک رو پیام میده (هیچ ارسالی به کانال وجود نداره)
    await message.reply(
        f"✅ ویدیو با موفقیت ثبت شد!\n\n"
        f"🔗 **لینک اختصاصی تماشای ویدیو:**\n`{share_link}`\n\n"
        f"هر کس روی این لینک بزنه، ویدیو داخل همین ربات براش باز میشه و بعد از ۳۰ ثانیه حذف میشه."
    )

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
