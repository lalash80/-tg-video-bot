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
PORT = int(os.getenv لینک اختصاصی کانال استفاده کنید یا ویدیویی بفرستید تا لینک آن را دریافت نمایید.")

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
# روشن کردن همزمان وب‌سرور رندر و پولینگ تلگرام
await start_web_server()
await dp.start_polling(bot)

if __name__ == "__main__":
asyncio.run(main())
