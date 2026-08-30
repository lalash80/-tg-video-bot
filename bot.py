import asyncio
import os
import json
import uuid
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# توکن ربات
BOT_TOKEN = os.getenv("BOT_TOKEN", "7963384210:AAGr4U6t-6a84N980PqfV4QZq4Z7Xq-example")

# آیدی عددی شما به عنوان ادمین اصلی
ADMIN_IDS = [214838628]

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

# مسیر فایل ذخیره لینک‌ها
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
    except Exception:
        pass

# بارگذاری اولیه دیتابیس
video_db = load_db()

async def delete_message_later(chat_id: int, message_id: int, delay: int = 30):
    """حذف پیام پس از ۳۰ ثانیه"""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

@dp.message(CommandStart())
async def handle_start(message: Message, command: CommandObject):
    """هندلر جامع استارت برای آیفون، اندروید و دسکتاپ"""
    args = command.args

    # اگر کاربر از طریق لینک ویدیویی وارد شده باشد
    if args:
        short_id = args.strip()
        file_id = video_db.get(short_id)

        if file_id:
            try:
                sent_msg = await message.answer_video(
                    video=file_id,
                    caption="⚠️ این ویدیو پس از ۳۰ ثانیه به صورت خودکار حذف خواهد شد."
                )
                asyncio.create_task(delete_message_later(message.chat.id, sent_msg.message_id, delay=30))
                return
            except Exception:
                await message.answer("❌ متأسفانه در ارسال ویدیو خطایی رخ داد.")
                return
        else:
            await message.answer("❌ این لینک معتبر نیست یا منقضی شده است.")
            return

    # اگر استارت معمولی و بدون لینک باشد
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            "سلام ادمین عزیز! 👋\n\n"
            "برای ساخت لینک کوتاه و استاندارد، ویدیو مورد نظر را برای من ارسال یا فوروارد کنید."
        )
    else:
        await message.answer(
            "سلام! 👋\n"
            "برای دریافت ویدیوها لطفا از لینک‌های اختصاصی استفاده کنید."
        )

@dp.message(F.video)
async def handle_video_upload(message: Message):
    """دریافت ویدیو فقط از ادمین و ایجاد لینک کوتاه و ایمن"""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔️ شما اجازه آپلود ویدیو و ساخت لینک را ندارید.")
        return

    file_id = message.video.file_id
    
    # ساخت یک شناسه کوتاه ۸ کاراکتری برای سازگاری کامل با iOS و Android
    short_id = uuid.uuid4().hex[:8]
    
    # ذخیره شناسه در دیتابیس
    video_db[short_id] = file_id
    save_db(video_db)

    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={short_id}"

    await message.reply(
        f"✅ <b>ویدیو با موفقیت ذخیره شد!</b>\n\n"
        f"🔗 <b>لینک اختصاصی (سازگار با آیفون و اندروید):</b>\n"
        f"<code>{link}</code>\n\n"
        f"💡 روی لینک بالا بزنید یا آن را در کانال/گروه به اشتراک بگذارید."
    )

# وب‌سرور داخلی برای حفظ پایداری در رندر
async def handle_ping(request):
    return web.Response(text="Bot is running!")

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
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
