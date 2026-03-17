import os
import asyncio
import logging
import sqlite3
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# 1. إعدادات البوت والمسؤول
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "8722121336:AAFT2Grwg5aysIe0Vcg3sSM2IQR9lG3UA0c"
ADMIN_ID = 5504483293  # آيدي حسابك
CHANNEL_ID = "@gdudhd90" # معرف قناتك (يجب أن يكون البوت مشرفاً فيها)
DB_NAME = "bot_database.db"
DOWNLOAD_DIR = "downloads"

# 2. وظائف قاعدة البيانات
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

init_db()

# 3. التحقق من الاشتراك الإجباري
async def is_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # التحقق إذا كان العضو موجوداً (مالك، مشرف، أو عضو عادي)
        return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

# 4. واجهة البوت الرئيسية
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)

    # فحص الاشتراك
    if not await is_subscribed(context, user.id):
        keyboard = [
            [InlineKeyboardButton("📢 اشترك في القناة أولاً", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
            [InlineKeyboardButton("✅ تم الاشتراك، فعل البوت", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            f"⚠️ عذراً عزيزي، يجب عليك الاشتراك في قناة البوت أولاً لتتمكن من استخدامه!\n\nقناتنا: {CHANNEL_ID}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    welcome_text = (
        f"👻┆ أهلاً بك عزيزي، في بوت التحميل الشامل \n"
        f"📥┆ **المنصات المدعومة:**\n"
        f"🔺 يوتيوب | 🎵 تيك توك | 📷 انستقرام | 🔵 فيسبوك \n\n"
        f"- أرسل الرابط الآن للبدء ♡"
    )
    keyboard = [[InlineKeyboardButton("❗┆ كيفية الاستخدام", callback_data='help')]]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# 5. معالجة الروابط (مع فحص اشتراك)
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_subscribed(context, user_id):
        await update.message.reply_text(f"❌ يجب عليك الاشتراك في القناة أولاً: {CHANNEL_ID}")
        return

    url = update.message.text
    if not url.startswith("http"): return

    status_msg = await update.message.reply_text("جاري التحميل... ⏳")
    
    try:
        ydl_opts = {'format': 'best', 'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s', 'quiet': True}
        
        def dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await asyncio.to_thread(dl)
        
        await status_msg.edit_text("جاري الرفع... 📤")
        with open(file_path, 'rb') as video:
            await update.message.reply_video(video=video, caption="تم التحميل بواسطة @YourBot ✅")
        
        os.remove(file_path)
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text("❌ فشل التحميل، تأكد من الرابط.")

# 6. معالجة ضغطات الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "check_sub":
        if await is_subscribed(context, query.from_user.id):
            await query.message.delete()
            await start(update, context) # إعادة تشغيل البوت للمشترك
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text="❌ لم تشترك بعد! فضلاً اشترك ثم اضغط زر التحقق.")

# 7. تشغيل البوت
if __name__ == '__main__':
    if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    print("البوت يعمل مع خاصية الاشتراك الإجباري...")
    app.run_polling()
