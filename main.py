import asyncio
import nest_asyncio
from telethon import TelegramClient
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
from datetime import datetime, timedelta

# جعل asyncio يعمل في جوجل كولاب
nest_asyncio.apply()

# إعدادات Telethon
api_id = "29405098"
api_hash = "67da39040e095ba514d2bdd6e330e30f"
session_name = "new_session"
telethon_client = TelegramClient(session_name, api_id, api_hash)

# إعدادات بوت Aiogram
BOT_TOKEN = "7841700990:AAF5gdyCJDs3vJWW78wYWvZk3QlCDD-fQDA"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# user_id الخاص بالمشرف (استبدل هذا بـ user_id الفعلي الخاص بك)
ADMIN_USER_ID = 5293942600  # استبدل هذا بالـ user_id الخاص بك، وليس الـ username

# ملف المستخدمين
USERS_FILE = "users.txt"

# إعدادات السجل (للتسجيل الأخطاء)
logging.basicConfig(filename="bot_errors.log", level=logging.ERROR)


# إضافة مستخدم جديد إلى الملف
def add_user(user_id: int, username: str):
    try:
        with open(USERS_FILE, "a") as file:
            file.write(f"{user_id}\n")

        # إرسال إشعار للمشرف عند دخول مستخدم جديد
        notify_admin_new_user(user_id, username)

    except Exception as e:
        log_error(e)


def log_error(e: Exception):
    logging.error(f"Error: {str(e)}")


# التحقق إذا كان المستخدم مشرفًا
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID  # التحقق باستخدام user_id فقط


# إرسال إشعار للمشرف عند دخول مستخدم جديد
def notify_admin_new_user(user_id: int, username: str):
    try:
        # قراءة جميع المستخدمين من الملف
        with open(USERS_FILE, "r") as file:
            users = file.readlines()

        # إزالة الأسطر الفارغة
        users = [user.strip() for user in users if user.strip()]

        # الحصول على عدد المستخدمين
        user_count = len(set(users))  # استخدام set لتصفية المستخدمين المكررين

        # إرسال الإشعار للمشرف باستخدام user_id
        admin_message = f"🔔 تم دخول مستخدم جديد! 🆕\n\nالاسم: {username}\nعدد المستخدمين الكلي: {user_count}"
        bot.send_message(ADMIN_USER_ID, admin_message)
    except Exception as e:
        log_error(e)


# إرسال رسالة ترحيب مع الزر
@dp.message(Command("start"))
async def send_welcome(message: Message):
    add_user(message.from_user.id,
             message.from_user.username)  # إضافة المستخدم مع اسم المستخدم

    # إرسال إشعار للمشرف عند الضغط على /start (التعديل هنا)
    await bot.send_message(ADMIN_USER_ID, f"👤 مستخدم ضغط على /start:\n"
                           f"الاسم: {message.from_user.full_name}\n"
                           f"اليوزر: @{message.from_user.username}\n"
                           f"الايدي: `{message.from_user.id}`",
                           parse_mode="Markdown")

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="بحث عن ملفات PDF",
                             callback_data="search_pdf"))

    # إضافة زر الإحصائيات وزر إرسال رسالة للجميع إذا كان المستخدم هو المشرف
    if is_admin(message.from_user.id):
        builder.add(
            InlineKeyboardButton(text="عرض الإحصائيات",
                                 callback_data="show_stats"))
        builder.add(
            InlineKeyboardButton(text="إرسال رسالة للجميع",
                                 callback_data="send_message_to_all"))

    await message.answer(
        f"👋 مرحبًا {message.from_user.first_name}!\n"
        "أنا بوت البحث في قنوات تيليجرام 📚🔍\n"
        "اضغط على الزر للبحث عن ملفات PDF في القنوات.",
        reply_markup=builder.as_markup())


# التفاعل مع الضغط على الزر
@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if callback_query.data == "search_pdf":
        await callback_query.message.answer(
            "🔍 من فضلك، اكتب الكلمة المفتاحية للبحث عن ملفات PDF.")

    elif callback_query.data == "show_stats":
        await send_stats(callback_query.message)

    elif callback_query.data == "send_message_to_all":
        if is_admin(user_id):
            # تفعيل حالة انتظار لكتابة رسالة
            admin_waiting_for_message[user_id] = True
            await callback_query.message.answer(
                "📝 من فضلك، اكتب الرسالة التي ترغب في إرسالها إلى جميع المستخدمين."
            )
        else:
            await callback_query.message.answer(
                "❌ أنت لست المشرف، لا يمكنك إرسال رسالة للجميع.")


# إضافة متغير لتتبع حالة إرسال الرسائل للجميع
admin_waiting_for_message = {}


# التعامل مع الرسائل بشكل عام
@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id

    # تحقق من ما إذا كان المشرف في حالة انتظار رسالة
    if user_id in admin_waiting_for_message and admin_waiting_for_message[
            user_id]:
        broadcast_message = message.text.strip()
        if not broadcast_message:
            await message.reply("❌ الرجاء إدخال رسالة لإرسالها.")
            return

        try:
            with open(USERS_FILE, "r") as file:
                users = file.readlines()

            users = [user.strip() for user in users if user.strip()]
            unique_users = set(users)

            for user_id in unique_users:
                try:
                    await bot.send_message(user_id, broadcast_message)
                except Exception as e:
                    log_error(e)

            await message.reply("✅ تم إرسال الرسالة لجميع المستخدمين.")

        except FileNotFoundError:
            await message.reply("❌ لم يتم العثور على بيانات المستخدمين.")

        # إعادة تعيين الحالة بعد إرسال الرسالة
        admin_waiting_for_message[user_id] = False
        return

    # تحقق مما إذا كانت الرسالة تتعلق بالبحث
    if message.text.startswith("/start") or message.text.startswith("/stats"):
        return  # تجاهل هذه الأوامر

    query = message.text.strip()
    if not query:
        await message.reply("❌ الرجاء إدخال الكلمة المفتاحية للبحث.")
        return

    await message.reply(f"🔍 البحث عن ملفات PDF تحتوي على: {query} ...")
    await telethon_search_pdfs(query, message.chat.id)


# البحث عن ملفات PDF باستخدام Telethon
async def telethon_search_pdfs(keyword: str, user_id: int, limit: int = 10):
    async with telethon_client:
        dialogs = await telethon_client.get_dialogs()
        channels = [dialog for dialog in dialogs if dialog.is_channel]

        results_found = 0
        sent_files = set()

        for channel in channels:
            try:
                channel_entity = await telethon_client.get_entity(channel.id)

                async for message in telethon_client.iter_messages(
                        channel, search=keyword, limit=limit):
                    if message.document and message.document.mime_type == "application/pdf":
                        file_name = message.document.attributes[
                            0].file_name if message.document.attributes else "ملف غير معروف"

                        if file_name in sent_files:
                            continue

                        sent_files.add(file_name)

                        if hasattr(channel_entity,
                                   "username") and channel_entity.username:
                            message_link = f"https://t.me/{channel_entity.username}/{message.id}"
                            await bot.send_message(
                                user_id,
                                f"📂 *تم العثور على:* `{file_name}`\n🔗 [رابط التحميل]({message_link})",
                                parse_mode="Markdown")
                        else:
                            invite_link = await telethon_client.export_invite_link(
                                channel.id)
                            await bot.send_message(
                                user_id,
                                f"📂 *تم العثور على:* `{file_name}`\n⚠️ القناة خاصة! يجب الانضمام أولًا عبر الرابط:\n🔗 {invite_link}"
                            )

                        results_found += 1
            except Exception as e:
                log_error(e)

        if results_found == 0:
            await bot.send_message(user_id,
                                   "❌ لم يتم العثور على أي ملف PDF مطابق.")


# إحصائيات البوت
async def send_stats(message: Message):
    try:
        with open(USERS_FILE, "r") as file:
            users = file.readlines()

        users = [user.strip() for user in users if user.strip()]
        unique_users = set(users)
        user_count = len(unique_users)

        stats_message = f"""
📊 إحصائيات البوت:
- عدد المستخدمين الكلي: {user_count}
"""
        await message.reply(stats_message)

    except FileNotFoundError:
        await message.reply("❌ لم يتم العثور على بيانات المستخدمين.")


# تشغيل Telethon و Aiogram معًا
async def main():
    print("🚀 بدء تشغيل Telethon...")
    await telethon_client.start()
    print("✅ Telethon متصل بحسابك!")

    print("🤖 بدء تشغيل بوت Aiogram...")
    try:
        await dp.start_polling(bot)
    finally:
        print("❌ حدث خطأ أثناء تشغيل البوت!")
        await telethon_client.disconnect()


if __name__ == "__main__":
    print("🔄 تشغيل البوت...")
    asyncio.run(main())
