# main.py - نسخه نهایی و کامل با لاگ‌گیری دقیق برای عیب‌یابی

# --- فاز ۱: وارد کردن تمام کتابخانه‌های لازم ---
import logging
import sqlite3
import os
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from telegram.error import Forbidden

# --- فاز ۲: خواندن اطلاعات حساس از متغیرهای محیطی ---
TOKEN = os.getenv('TOKEN')
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID'))
except (TypeError, ValueError):
    ADMIN_ID = None

# --- فاز ۳: تنظیمات، قیمت‌ها و متن‌های ثابت ---
SUPPORT_USERNAME = "@Jaber_far"
CARD_NUMBER = "6219-8619-3064-7200"
CARD_HOLDER_NAME = "جابر حسنی فر"
CHANNEL_IDS = {
    "10": -1002400466668,
    "11": -1002800050525,
    "12": -1002781513755,
}
DB_NAME = "medical_data.db"

# --- قیمت‌ها (به تومان) ---
PRICE_GRADE_SINGLE_FULL = "500,000"
PRICE_GRADE_SINGLE_DISCOUNT = "399,000"
PRICE_BUNDLE_FULL = "1,500,000"
PRICE_BUNDLE_DISCOUNT = "599,000"

# --- متن دکمه‌ها ---
BTN_COURSES = "🛍️ مشاهده و خرید دوره‌ها"
BTN_AI_IMAGES = "🎨 تصاویر هوش مصنوعی"
BTN_SUPPORT = "📞 پشتیبانی و مشاوره"
BTN_GRADE_10 = "پایه دهم"
BTN_GRADE_11 = "پایه یازدهم"
BTN_GRADE_12 = "پایه دوازدهم"
BTN_BUNDLE = "🎁 پکیج کامل (هر سه پایه)"
BTN_BACK = "🔙 بازگشت"

# --- متن‌های حرفه‌ای و باکلاس ---
MSG_WELCOME = "✨ به مدیکال مود خوش آمدید!\n\nدر اینجا، یادگیری برات آسون تر میشه. آماده‌اید تا شروع کنیم؟\n\nلطفا برای شروع، یکی از گزینه‌ها را انتخاب کنید."

MSG_SELECT_COURSE = f"""
یک قدم تا خلق شگفتی فاصله دارید! 🚀

دوره‌های تخصصی ما با **تخفیف استثنایی** برای مدت محدود ارائه می‌شوند:

- **دوره تخصصی پایه دهم**
  ~قیمت اصلی: {PRICE_GRADE_SINGLE_FULL} تومان~
  ✅ **با تخفیف: {PRICE_GRADE_SINGLE_DISCOUNT} تومان**

- **دوره تخصصی پایه یازدهم**
  ~قیمت اصلی: {PRICE_GRADE_SINGLE_FULL} تومان~
  ✅ **با تخفیف: {PRICE_GRADE_SINGLE_DISCOUNT} تومان**

- **دوره تخصصی پایه دوازدهم**
  ~قیمت اصلی: {PRICE_GRADE_SINGLE_FULL} تومان~
  ✅ **با تخفیف: {PRICE_GRADE_SINGLE_DISCOUNT} تومان**

- **🎁 پکیج جامع (هر سه پایه با هم)**
  ~قیمت اصلی: {PRICE_BUNDLE_FULL} تومان~
  💎 **فرصت طلایی: {PRICE_BUNDLE_DISCOUNT} تومان**

لطفا دوره مورد نظر خود را برای ادامه فرآیند ثبت‌نام انتخاب کنید.
"""

MSG_PAYMENT_INSTRUCTION = """
سپاس از انتخاب شما! ✨

برای نهایی کردن ثبت‌نام، لطفا مبلغ مشخص شده را به شماره کارت زیر واریز نموده و سپس **تصویر واضح رسید پرداخت** را در همین صفحه ارسال فرمایید.

💳 **شماره کارت:**
`{card_number}`
(بانک سامان - به نام {card_holder_name})

**مبلغ قابل پرداخت: {price} تومان**

پس از ارسال رسید، درخواست شما توسط تیم پشتیبانی بررسی و لینک‌های دوره بلافاصله برای شما ارسال خواهد شد.
"""

MSG_SUPPORT = f"در هر مرحله از مسیر، همراه شما هستیم. برای ارتباط مستقیم با تیم پشتیبانی و مشاوره, به آیدی زیر پیام دهید:\n\n👤 {SUPPORT_USERNAME}"
MSG_AI_IMAGES = "این بخش در حال آماده‌سازی است. به زودی از ابزارهای هوش مصنوعی خلاقانه ما شگفت‌زده خواهید شد!"

# --- فاز ۴: تنظیمات لاگ‌گیری و دیتابیس ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def setup_database():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            product TEXT,
            status TEXT,
            submission_date TEXT
        )
    ''')
    conn.commit()
    return conn, cursor

conn, cursor = setup_database()

# --- فاز ۵: تمام توابع ربات تلگرام ---

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(BTN_COURSES)],
        [KeyboardButton(BTN_AI_IMAGES), KeyboardButton(BTN_SUPPORT)],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(MSG_WELCOME, reply_markup=reply_markup)

async def show_courses_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(BTN_GRADE_10), KeyboardButton(BTN_GRADE_11), KeyboardButton(BTN_GRADE_12)],
        [KeyboardButton(BTN_BUNDLE)],
        [KeyboardButton(BTN_BACK)],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(MSG_SELECT_COURSE, reply_markup=reply_markup, parse_mode='HTML')

async def handle_support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MSG_SUPPORT)

async def handle_ai_images_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MSG_AI_IMAGES)

async def handle_grade_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    product_map = {
        BTN_GRADE_10: "10", BTN_GRADE_11: "11",
        BTN_GRADE_12: "12", BTN_BUNDLE: "bundle"
    }
    price_map = {
        BTN_GRADE_10: PRICE_GRADE_SINGLE_DISCOUNT,
        BTN_GRADE_11: PRICE_GRADE_SINGLE_DISCOUNT,
        BTN_GRADE_12: PRICE_GRADE_SINGLE_DISCOUNT,
        BTN_BUNDLE: PRICE_BUNDLE_DISCOUNT
    }
    
    product_choice = product_map.get(user_text)
    selected_price = price_map.get(user_text)

    context.user_data['selected_product'] = product_choice
    
    payment_message = MSG_PAYMENT_INSTRUCTION.format(
        card_number=CARD_NUMBER,
        card_holder_name=CARD_HOLDER_NAME,
        price=selected_price
    )
    
    await update.message.reply_text(payment_message, parse_mode='HTML')

async def handle_receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if 'selected_product' not in context.user_data:
        await update.message.reply_text("لطفا ابتدا دوره مورد نظر خود را از منو انتخاب کنید.")
        return
        
    product = context.user_data['selected_product']
    photo_file_id = update.message.photo[-1].file_id
    
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO payments (user_id, username, product, status, submission_date) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username or "None", product, "در انتظار", datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"خطای دیتابیس: {e}")
        await update.message.reply_text("خطایی در ثبت اطلاعات رخ داد. لطفا دوباره تلاش کنید.")
        return

    await update.message.reply_text("✅ رسید شما دریافت شد. تیم ما در اسرع وقت آن را بررسی خواهد کرد. از صبوری شما سپاسگزاریم.")
    
    keyboard = [[
        InlineKeyboardButton("✅ تایید پرداخت", callback_data=f'approve_{user.id}'),
        InlineKeyboardButton("❌ رد پرداخت", callback_data=f'reject_{user_id}')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption_text = f"📬 رسید جدید\n\nکاربر: @{user.username} (ID: {user.id})\nمحصول: {product}"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=caption_text, reply_markup=reply_markup)
    del context.user_data['selected_product']

# --- تابع ادمین بازنویسی شده با لاگ‌گیری بسیار دقیق برای عیب‌یابی ---
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id_str = query.data.split('_')
    user_id = int(user_id_str)
    
    logger.info(f"ادمین عملیات '{action}' را برای کاربر {user_id} آغاز کرد.")
    
    cursor.execute("SELECT product, username FROM payments WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if not result:
        await query.edit_message_caption(caption="خطا: کاربر یافت نشد (احتمالا قبلا پردازش شده).")
        return
        
    product_from_db = result[0]
    username = result[1]
    
    # --- بخش عیب‌یابی ---
    logger.info(f"مقدار 'product' خام از دیتابیس: '{product_from_db}'")
    logger.info(f"نوع داده 'product' خام: {type(product_from_db)}")
    
    product_cleaned = product_from_db.strip()
    logger.info(f"مقدار 'product' پس از strip: '{product_cleaned}'")
    
    # مقایسه و لاگ کردن نتیجه
    is_bundle = (product_cleaned == "bundle")
    logger.info(f"آیا محصول برابر 'bundle' است؟ نتیجه: {is_bundle}")
    # --- پایان بخش عیب‌یابی ---

    if action == "approve":
        try:
            if is_bundle: # استفاده از نتیجه مقایسه
                logger.info(f"شرط 'bundle' صحیح است. در حال پردازش برای @{username}.")
                bundle_grades = ["10", "11", "12"]
                invite_links = []
                for grade in bundle_grades:
                    channel_id = CHANNEL_IDS.get(grade)
                    if channel_id:
                        expire_date = datetime.now() + timedelta(days=1)
                        link = await context.bot.create_chat_invite_link(chat_id=channel_id, member_limit=1, expire_date=expire_date)
                        invite_links.append(f"🔗 لینک ورود به دوره پایه {grade}م: {link.invite_link}")
                
                if len(invite_links) == len(bundle_grades):
                    links_text = "\n\n".join(invite_links)
                    welcome_message = f"✅ ثبت‌نام شما در پکیج جامع با موفقیت انجام شد!\n\nبا افتخار لینک‌های دسترسی به هر سه دوره را تقدیم می‌کنیم:\n\n{links_text}\n\n⚠️ توجه: هر لینک یکبار مصرف بوده و پس از ۱ روز منقضی می‌شود."
                    await context.bot.send_message(chat_id=user_id, text=welcome_message)
                    await query.edit_message_caption(caption=f"✅ کاربر @{username} (پکیج جامع) تایید شد و ۳ لینک ارسال گردید.")
                else:
                    await query.edit_message_caption(caption="❌ خطا: مشکلی در ساخت تمام لینک‌ها برای پکیج جامع رخ داد.")
            else:
                logger.info(f"شرط 'bundle' غلط است. در حال پردازش محصول تکی: '{product_cleaned}'")
                channel_id = CHANNEL_IDS.get(product_cleaned) # استفاده از نسخه تمیز شده
                if not channel_id:
                    await query.edit_message_caption(caption=f"❌ خطا: شناسه کانال برای محصول «{product_cleaned}» تعریف نشده.")
                    return

                expire_date = datetime.now() + timedelta(days=1)
                invite_link = await context.bot.create_chat_invite_link(chat_id=channel_id, member_limit=1, expire_date=expire_date)
                welcome_message = f"✅ ثبت‌نام شما با موفقیت تایید شد!\n\nلینک ورود به دوره:\n{invite_link.invite_link}\n\n⚠️ این لینک یکبار مصرف است."
                await context.bot.send_message(chat_id=user_id, text=welcome_message)
                await query.edit_message_caption(caption=f"✅ کاربر @{username} (محصول: {product_cleaned}) تایید شد.")

            cursor.execute("UPDATE payments SET status = ? WHERE user_id = ?", ("تایید شده", user_id))
            conn.commit()

        except Forbidden:
            await query.edit_message_caption(caption=f"❌ خطا: کاربر @{username} ربات را بلاک کرده است.")
        except Exception as e:
            logger.error(f"خطای پیش‌بینی نشده در تایید کاربر {user_id}: {e}", exc_info=True)
            await query.edit_message_caption(caption="❌ خطای پیش‌بینی نشده. لاگ‌ها را بررسی کنید.")
            
    elif action == "reject":
        cursor.execute("UPDATE payments SET status = ? WHERE user_id = ?", ("رد شده", user_id))
        conn.commit()
        await context.bot.send_message(chat_id=user_id, text="❌ پرداخت شما تایید نشد. لطفا در صورت لزوم با پشتیبانی تماس بگیرید.")
        await query.edit_message_caption(caption=f"❌ کاربر @{username} رد شد.")

# --- فاز ۶: تابع اصلی برای اجرای همه چیز ---
def main():
    if not TOKEN or not ADMIN_ID:
        logger.error("خطا: توکن ربات یا ادمین آیدی تعریف نشده! آنها را در متغیرهای محیطی سرور وارد کنید.")
        return

    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_BACK}$"), start_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_COURSES}$"), show_courses_menu_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_SUPPORT}$"), handle_support_handler))
    application.add_handler(MessageHandler(filters.Regex(f"^{BTN_AI_IMAGES}$"), handle_ai_images_handler))
    
    grade_buttons_regex = f"^({BTN_GRADE_10}|{BTN_GRADE_11}|{BTN_GRADE_12}|{BTN_BUNDLE})$"
    application.add_handler(MessageHandler(filters.Regex(grade_buttons_regex), handle_grade_selection_handler))
    
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt_handler))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^(approve_|reject_)'))

    logger.info("ربات با موفقیت راه‌اندازی شد و در حال اجرا است...")
    application.run_polling()

if __name__ == '__main__':
    main()