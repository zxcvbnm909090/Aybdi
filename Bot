import os
import requests
import yt_dlp
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- إعدادات التحميل ---
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# دالة للتحميل من السوشيال ميديا (YouTube, TikTok, etc)
def download_social_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# دالة للتحميل من الروابط المباشرة (Files/Images)
def download_direct_file(url):
    local_filename = os.path.join(DOWNLOAD_DIR, url.split('/')[-1])
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

# --- معالجة الرسائل ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً بك! أرسل لي أي رابط (فيديو، صورة، أو ملف) وسأقوم بتحميله لك.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    msg = await update.message.reply_text("جاري المعالجة... انتظر قليلاً ⏳")
    
    try:
        # محاولة التحميل كفيديو سوشيال ميديا أولاً
        try:
            file_path = download_social_video(url)
        except:
            # إذا فشل، نحاول كتحميل مباشر للملف
            file_path = download_direct_file(url)

        # إرسال الملف للمستخدم
        with open(file_path, 'rb') as document:
            await update.message.reply_document(document=document, caption="تم التحميل بنجاح ✅")
        
        # حذف الملف من السيرفر بعد الإرسال لتوفير المساحة
        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"عذراً، حدث خطأ أثناء التحميل: {str(e)}")

# --- تشغيل البوت ---
def main():
    # ضع التوكن الخاص بك هنا
    TOKEN = "8722121336:AAFT2Grwg5aysIe0Vcg3sSM2IQR9lG3UA0c"
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == '__main__':
    main()

