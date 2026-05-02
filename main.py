import logging
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# مكتبات الباركود والصور
import barcode
from barcode.writer import ImageWriter
from pyzbar.pyzbar import decode
from PIL import Image

# إعداد تسجيل الأخطاء (لتسهيل معرفة المشاكل في Render)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب عند بدء البوت"""
    welcome_text = (
        "مرحباً بك! 👋\n\n"
        "أنا بوت تحويل وقراءة الباركود:\n"
        "📝 أرسل لي أي **نص** أو **رقم** وسأحوله إلى صورة باركود.\n"
        "📸 أرسل لي **صورة** تحتوي على باركود وسأقوم بقراءة النص الموجود فيها."
    )
    await update.message.reply_text(welcome_text)

async def generate_barcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحويل النص المستلم إلى صورة باركود"""
    text = update.message.text
    
    # رسالة مؤقتة
    msg = await update.message.reply_text("جاري إنشاء الباركود... ⏳")
    
    try:
        # نستخدم نوع Code128 لأنه يدعم الحروف الإنجليزية والأرقام والرموز
        code128 = barcode.get_barcode_class('code128')
        # إنشاء الباركود مع حفظه كصورة
        bc = code128(text, writer=ImageWriter())
        
        # حفظ الصورة في الذاكرة (بدون إنشاء ملف فعلي على السيرفر)
        buffer = BytesIO()
        bc.write(buffer)
        buffer.seek(0)
        
        # إرسال الصورة للمستخدم
        await update.message.reply_photo(photo=buffer, caption="تم إنشاء الباركود بنجاح! 🪄")
        await msg.delete() # حذف رسالة الانتظار
        
    except Exception as e:
        logging.error(f"Error generating barcode: {e}")
        await msg.edit_text("عذراً، حدث خطأ أثناء إنشاء الباركود. تأكد من إدخال نص باللغة الإنجليزية أو أرقام.")

async def read_barcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قراءة الباركود من الصورة المستلمة"""
    msg = await update.message.reply_text("جاري فحص الصورة... 🔍")
    
    try:
        # الحصول على أعلى دقة للصورة المرسلة
        photo_file = await update.message.photo[-1].get_file()
        
        # تحميل الصورة إلى الذاكرة
        buffer = BytesIO()
        await photo_file.download_to_memory(buffer)
        buffer.seek(0)
        
        # فتح الصورة باستخدام مكتبة Pillow
        img = Image.open(buffer)
        
        # محاولة فك تشفير الباركود
        decoded_objects = decode(img)
        
        if not decoded_objects:
            await msg.edit_text("لم أتمكن من العثور على أي باركود أو QR Code في هذه الصورة. 😔\nتأكد من وضوح الصورة.")
            return
            
        # استخراج النصوص من جميع الباركودات الموجودة في الصورة
        results = []
        for obj in decoded_objects:
            text_data = obj.data.decode('utf-8')
            barcode_type = obj.type
            results.append(f"النوع: {barcode_type}\nالنص: `{text_data}`")
            
        final_text = "\n\n".join(results)
        await msg.edit_text(f"**تمت القراءة بنجاح!** 🎉\n\n{final_text}", parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Error reading barcode: {e}")
        await msg.edit_text("عذراً، حدث خطأ أثناء محاولة قراءة الصورة.")

def main():
    # ضع التوكن الخاص بك هنا
    TOKEN = "8767255327:AAFWQFrJSHvABSZUF2x_OYg9sUTzNKUar8Q"
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # إضافة أوامر البوت
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_barcode))
    app.add_handler(MessageHandler(filters.PHOTO, read_barcode))
    
    # تشغيل البوت
    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == '__main__':
    main()
