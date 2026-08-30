import os
import asyncio
from aiogram import Bot, Dispatcher, types, F

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.video)
async def handle_video(message: types.Message):
    video = message.video
    status_msg = await message.reply("در حال پردازش و دریافت ویدیو...")

    file_info = await bot.get_file(video.file_id)
    file_path = f"temp_{video.file_id}.mp4"

    try:
        await bot.download_file(file_info.file_path, file_path)
        await status_msg.edit_text("ویدیو دریافت شد. در حال ارسال به مقصد...")

        video_file = types.FSInputFile(file_path)
        caption = message.caption or ""
        await bot.send_video(chat_id=TARGET_CHAT_ID, video=video_file, caption=caption)

        await status_msg.edit_text("✅ با موفقیت ارسال شد و فایل موقت پاک شد.")
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا در پردازش: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
