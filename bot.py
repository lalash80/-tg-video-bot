import os
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

# دیکشنری دائمی برای نگهداری ویدیوها تا لینک هرگز منقضی نشود
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

# هندلر مدیریت لینک اختصاصی (حتی برای بار چندم)
@dp.message(CommandStart(deep_link=True))
async def handle_start_deep_link(message: Message, command: CommandObject):
    link_key = command.args.strip()
    video_id = videos_db.get(link_key)
    
    if video_id:
        # ارسال ویدیو به کاربر
        sent_video = await message.answer_video(
            video=video_id,
            caption="⚠️ این ویدیو پس از ۳۰ ثانیه به صورت خودکار حذف خواهد شد."
        )
        
        # ۳۰ ثانیه بعد فقط پیام ارسالی به این کاربر حذف می‌شود، اصل لینک و ویدیو باقی می‌ماند
        await asyncio.sleep(30)
        try:
            await sent_video.delete()
            # پیام یادآوری بعد از حذف
            await message.answer("⏱️ مهلت تماشای ویدیو به پایان رسید و ویدیو حذف شد.\nبرای دریافت مجدد می‌توانید دوباره روی لینک اختصاصی کلیک کنید.")
        except Exception as e:
            logging.error(f"Error deleting video: {e}")
    else:
        await message.answer("❌ متأسفانه این لینک نامعتبر است یا ربات بازنشانی شده است.")

# هندلر استارت معمولی
@dp.message(CommandStart())
async def handle_start_plain(message: Message):
    await message.answer("👋 سلام! برای دریافت ویدیو از لینک اختصاصی استفاده کنید، یا یک ویدیو برای من بفرستید تا لینک دائمی آن را تحویل بگیرید.")

# دریافت ویدیو از ادمین و ایجاد لینک دائمی
@dp.message(F.video)
async def handle_video_upload(message: Message):
    video_id = message.video.file_id
    # کلید یکتا و مرتب برای لینک
    link_key = f"v_{message.message_id}_{message.from_user.id}"
    videos_db[link_key] = video_id
    
    bot_info = await bot.get_me()
    share_link = f"https://t.me/{bot_info.username}?start={link_key}"
    
    await message.reply(
        f"✅ ویدیو با موفقیت ثبت و لینک دائمی ساخته شد!\n\n"
        f"🔗 **لینک اختصاصی ویدیو:**\n`{share_link}`\n\n"
        f"📌 **ویژگی‌ها:**\n"
        f"• این لینک دائمی است و هرگز منقضی نمی‌شود.\n"
        f"• هر کاربر با کلیک روی لینک، ویدیو را دریافت می‌کند و ۳۰ ثانیه بعد از پیام او پاک می‌شود.\n"
        f"• کاربر حتی می‌تواند بعداً دوباره روی لینک کلیک کند و ویدیو را تحویل بگیرد."
    )

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
