import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# دیتابیس موقت در حافظه برای ذخیره شناسه ویدیوها
videos_db = {}

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

@dp.message(CommandStart(deep_link=True))
async def handle_start_deep_link(message: Message, command: CommandObject):
    link_key = command.args
    video_id = videos_db.get(link_key)
    
    if video_id:
        sent_video = await message.answer_video(
            video=video_id,
            caption="⚠️ این ویدیو پس از ۳۰ ثانیه به صورت خودکار حذف خواهد شد."
        )
        # ۳۰ ثانیه بعد پیام حذف می‌شود
        await asyncio.sleep(30)
        try:
            await sent_video.delete()
        except Exception as e:
            logging.error(f"Error deleting video: {e}")
    else:
        await message.answer("❌ متأسفانه این ویدیو یافت نشد یا منقضی شده است.")

@dp.message(CommandStart())
async def handle_start_plain(message: Message):
    await message.answer("👋 سلام! برای دریافت ویدیو از لینک اختصاصی کانال استفاده کنید یا ویدیویی بفرستید تا لینک آن را دریافت نمایید.")

@dp.message(F.video)
async def handle_video_upload(message: Message):
    video_id = message.video.file_id
    link_key = f"vid_{message.message_id}"
    videos_db[link_key] = video_id
    
    bot_info = await bot.get_me()
    share_link = f"https://t.me/{bot_info.username}?start={link_key}"
    
    if TARGET_CHAT_ID:
        try:
            await bot.send_video(
                chat_id=TARGET_CHAT_ID,
                video=video_id,
                caption=f"🔗 برای تماشای این ویدیو در بات کلیک کنید:\n{share_link}"
            )
        except Exception as e:
            logging.error(f"Channel error: {e}")
            
    await message.reply(
        f"✅ ویدیو ثبت شد!\n\n"
        f"🔗 **لینک اشتراک‌گذاری در کانال:**\n`{share_link}`\n\n"
        f"کاربر با زدن روی این لینک ویدیو را تحویل گرفته و بعد از ۳۰ ثانیه حذف خواهد شد."
    )

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
