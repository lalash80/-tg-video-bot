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

# لیست ادمین‌های ربات
ADMIN_IDS = [214838628, 8729143361]

# دریافت ادمین‌های اضافی از متغیرهای محیطی در صورت وجود
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

# مسیر دیتابیس فایل‌ها
DB_FILE = "media_db.json"

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

# بارگذاری دیتابیس
media_db = load_db()

async def delete_message_later(chat_id: int, message_id: int, delay: int = 30):
    """حذف پیام پس از ۳۰ ثانیه"""
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

@dp.message(CommandStart())
async def handle_start(message: Message, command: CommandObject):
    """هندلر استارت با پشتیبانی کامل از iOS و Android"""
    args = command.args

    if args:
        short_id = args.strip()
        item = media_db.get(short_id)

        if item:
            # خواندن اطلاعات فایل ذخیره‌شده
            if isinstance(item, dict):
                file_id = item.get("file_id")
                file_type = item.get("type", "video")
                custom_caption = item.get("caption", "")
            else:
                file_id = item
                file_type = "video"
                custom_caption = ""

            # ساخت متن نهایی همراه با کپشن ادمین
            caption_parts = []
            if custom_caption:
                caption_parts.append(custom_caption)
            caption_parts.append("⚠️ این فایل پس از ۳۰ ثانیه به صورت خودکار حذف خواهد شد.")
            final_caption = "\n\n".join(caption_parts)

            try:
                if file_type == "photo":
                    sent_msg = await message.answer_photo(photo=file_id, caption=final_caption)
                else:
                    sent_msg = await message.answer_video(video=file_id, caption=final_caption)

                asyncio.create_task(delete_message_later(message.chat.id, sent_msg.message_id, delay=30))
                return
            except Exception:
                await message.answer("❌ متأسفانه در ارسال فایل خطایی رخ داد.")
                return
        else:
            await message.answer("❌ این لینک معتبر نیست یا منقضی شده است.")
            return

    # پیام راهنما برای استارت عادی
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            "سلام ادمین عزیز! 👋\n\n"
            "برای ساخت لینک، کافیست **عکس** یا **ویدیو** را بفرستید.\n"
            "💡 <i>اگر متنی (کپشن) همراه عکس/ویدیو بنویسید، همان متن برای کاربران نیز نمایش داده خواهد شد.</i>"
        )
    else:
        await message.answer(
            "سلام! 👋\n"
            "برای دریافت فایل‌ها لطفاً از لینک‌های اختصاصی استفاده کنید."
        )

@dp.message(F.video | F.photo)
async def handle_media_upload(message: Message):
    """دریافت رسانه و ذخیره متن/کپشن اختصاصی"""
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⛔️ شما دسترسی لازم برای آپلود فایل و ساخت لینک را ندارید.")
        return

    # گرفتن کپشن ارسالی توسط ادمین (در صورت وجود)
    custom_caption = message.caption or ""

    if message.video:
        file_id = message.video.file_id
        media_type = "video"
        type_fa = "ویدیو"
    elif message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
        type_fa = "عکس"
    else:
        return

    # ساخت شناسه کوتاه یکتا
    short_id = uuid.uuid4().hex[:8]
    media_db[short_id] = {
        "file_id": file_id,
        "type": media_type,
        "caption": custom_caption
    }
    save_db(media_db)

    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={short_id}"

    status_text = f"✅ <b>{type_fa} با موفقیت ذخیره شد!</b>\n\n"
    if custom_caption:
        status_text += f"📝 <b>متن ثبت شده:</b>\n<i>{custom_caption}</i>\n\n"

    status_text += (
        f"🔗 <b>لینک اختصاصی:</b>\n"
        f"<code>{link}</code>\n\n"
        f"💡 روی لینک بزنید یا آن را به اشتراک بگذارید."
    )

    await message.reply(status_text)

# وب‌سرور برای زنده نگه داشتن سرویس
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
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
