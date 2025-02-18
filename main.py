from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# إعداد البوت
TOKEN = "7663686008:AAGOH3ixgEqNfz4fEyRJYW8obYQYWhQU94w"  # استبدلها بتوكن البوت الخاص بك
CHANNEL_ID = "@mlfatwbot1"  # استبدلها باسم القناة الخاصة بك
bot = Bot(token=TOKEN)

# دالة لمعالجة الأمر عند بدء البوت
async def start(update: Update, context):
    await update.message.reply_text("مرحباً! اكتب الكلمة المفتاحية للملف الذي تبحث عنه.")

# دالة لسحب الملفات من القناة
async def send_file_from_channel(update: Update, context):
    keyword = update.message.text.lower()  # الكلمة المفتاحية التي أرسلها المستخدم
    
    # الحصول على جميع الرسائل في القناة (يتم معالجتها عبر الAPI)
    updates = await bot.get_chat_history(chat_id=CHANNEL_ID, limit=100)  # تحديد العدد، يمكنك زيادته
    
    # البحث عن الملفات التي تتطابق مع الكلمة المفتاحية
    found_files = []
    for message in updates:
        if message.document and keyword in message.document.file_name.lower():
            found_files.append(message.document)
    
    # إرسال الملفات إذا تم العثور عليها
    if found_files:
        for file in found_files:
            await bot.send_document(chat_id=update.message.chat_id, document=file.file_id)
        await update.message.reply_text(f"تم العثور على {len(found_files)} ملفات تتطابق مع الكلمة المفتاحية.")
    else:
        await update.message.reply_text("لم أتمكن من العثور على ملفات تتطابق مع الكلمة المفتاحية.")

# إعداد وتسجيل المعالجين
async def main():
    application = Application.builder().token(TOKEN).build()

    # إضافة معالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_file_from_channel))

    # بدء البوت
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())