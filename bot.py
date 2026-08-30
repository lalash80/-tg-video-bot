import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# توکن ربات (از رندر خوانده می‌شود و در صورت نبود، مقدار پیش‌فرض)
BOT_TOKEN = os.getenv("BOT_TOKEN", "7963384210:AAGr4U6t-6a84N980PqfV4QZq4Z7Xq-example")

# آیدی‌های ادمین (آیدی عددی شما مستقیماً اینجا ست شد)
ADMIN_IDS = [214838628]

# اگر در متغیرهای محیطی هم چیزی ست شده باشد اضافه می‌شود
env_admins = os.getenv("ADMIN_IDS", "")
if env_admins:
    for a in env_admins.split(","):
        if a.strip().isdigit():
            ADMIN_IDS.append(int(a.strip()))

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# دیکشنری موقت برای ذخیره ویدیوها (file_id)
# در صورت نیاز می‌توانید به دیتابیس متصل کنید
video_db = {}

async def delete_message_later(chat_id: int, message_id: int, delay: int = 30):
    """حذف خودکار پیام بعد از مدت زمان مشخص"""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

@dp.message(CommandStart(deep_link=True))
async def start_deep_link_handler(message: Message, command: CommandObject):
    """هندلر دیپ‌لینک برای استارت از طریق آیفون و اندروید"""
    video_key = command.args
    if not video_key:
        await message.answer("سلام! به ربات خوش آمدید.")
        return

    file_id = video_db.get(video_key)
    if not file_id:
        # اگر کلید خود file_id باشد مستقیم ارسال می‌کنیم
        file_id = video_key

    try:
        sent_msg = await message.answer_video(
            video=file_id,
            caption="⚠️ این ویدیو پس از ۳۰ ثانیه به صورت خودکار حذف خواهد شد."
        )
        # اجرای حذف خودکار در پس‌زمینه
        asyncio.create_task(delete_message_later(message.chat.id, sent_msg.message_id, delay=30))
    except Exception as e:
        await message.answer("❌ متأسفانه ویدیو یافت نشد یا مشکلی در ارسال پیش آمد.")

@dp.message(CommandStart())
async def start_normal_handler(message: Message):
    """هندلر استارت معمولی بدون لینک"""
    if message.from_user.id in ADMIN_IDS:
        await message.answer("سلام ادمین عزیز! 👋\nبرای ساخت لینک، کافیست ویدیو را برای من فوروارد یا آپلود کنید.")
    else:
        await message.answer("سلام! برای دریافت ویدیوها باید از لینک‌های اختصاصی استفاده کنید.")

@dp.message(F.video)
async def video_handler(message: Message):
    """دریافت ویدیو و ساخت لینک اختصاصی (فقط ادمین)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔️ شما دسترسی لازم برای آپلود ویدیو و ایجاد لینک را ندارید.")
        return

    file_id = message.video.file_id
    bot_info = await bot.get_me()
    
    # ساخت کلید کوتاه یا استفاده از شناسه فایل
    link = f"https://t.me/{bot_info.username}?start={file_id}"
    
    await message.reply(
        f"✅ ویدیو با موفقیت ثبت شد!\n\n"
        f"🔗 <b>لینک اختصاصی برای انتشار:</b>\n"
        f"<code>{link}</code>\n\n"
        f"📱 این لینک در تمامی دستگاه‌ها (از جمله آیفون) کار می‌کند."
    )

# وب‌سرور سبک برای زنده نگه داشتن سرویس روی رندر و پورت 10000
async def handle_ping(request):
    return web.Response(text="Bot is running smoothly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/ping", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    # شروع وب‌سرور در پس‌زمینه
    await start_web_server()
    # شروع گوش دادن به پیام‌های تلگرام
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
