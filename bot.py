import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# دیک، پیام شمارش معکوس میده و دقیقاً بعد از ۳۰ ثانیه برای جلوگیری از فوروارد یا ذخیره، ویدیو و پیامش رو خودکار حذف (Auto-delete) می‌کنه! کاملاً درکت کردم و این حرکت برای جذب ممبر به کانال هم عالیه. 👏💛

برای اینکه دقیقا همین پیاده بشه، سیستمش به این صورت کار می‌کنه:
1. خودت ویدیو رو برای ربات فوروارد یا ارسال می‌کنی؛ ربات اون رو ذخیره می‌کنه و بهت یک **لینک مخصوص** (مثلاً `t.me/FreecondomVideoUploader_bot?start=video_123`) تحویل میده.
2. تو اون لینک رو می‌ذاری داخل کانالت.
3. کاربر روی لینک می‌زنه، ربات Start می‌خوره، ویدیو رو برای کاربر می‌فرسته + پیام هشدار «این ویدیو بعد از ۳۰ ثانیه حذف خواهد شد!».
4. سر ۳۰ ثانیه، هم ویدیو و هم پیام هشدار برای اون کاربر پاک می‌شن!

---

### کد کامل و آماده `bot.py`

کافیه وارد گیت‌هاب بشی، فایل `bot.py` رو ادیت کنی، کل متنش رو پاک کنی و این کد تمیز و آماده رو بذاری:
```python
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# دیکشنری موقت برای نگهداری آی‌دی ویدیوها
# در حافظه ربات ذخیره می‌شود
videos_db = {}

@dp.message(CommandStart(deep_link=True))
async def start_with_link(message: Message, command: CommandObject):
"""وقتی کاربر با لینک مخصوص از کانال وارد ربات می‌شود"""
file_keyتا برای ویدیو
link_key = f"vid_{message.message_id}"
videos_db[link_key] = video_id

bot_info = await bot.get_me()
share_link = f"https://t.me/{bot_info.username}?start={link_key}"

# همچنین در صورت تمایل ویدیو را در کانال هم آپلود می‌کند
if TARGET_CHAT_ID:
try:
await bot.send_video(
chat_id=TARGET_CHAT_ID,
video=video_id,
caption=f"🔗 برای تماشای این ویدیو کلیک کنید:\n{share_link}"
)
except Exception as e:
logging.error(f"Could not forward to channel: {e}")

await message.reply(
f"✅ ویدیو دریافت شد!\n\n"
f"🔗 **لینک اشتراک‌گذاری در کانال:**\n`{share_link}`\n\n"
f"این لینک رو توی کانال بذار؛ کاربر که روش بزنه، ویدیو براش میاد و بعد از ۳۰ ثانیه حذف میشه."
)

async def main():
await dp.start_polling(bot)

if __name__ == "__main__":
asyncio.run(main())
