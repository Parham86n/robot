# main.py - نسخه نهایی و ساده‌سازی شده

# --- وارد کردن کتابخانه‌ها و تنظیمات اولیه ---
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

# --- خواندن متغیرهای محیطی ---
TOKEN = os.getenv('TOKEN')
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID'))
except (TypeError, ValueError):
    ADMIN_ID = None

# --- تنظیمات ثابت ربات ---
SUPPORT_USERNAME = "@Jaber_far"
CARD_NUMBER = "6219-8619-3064-7200"
CARD_HOLDER_NAME = "جابر حسنی فر"
CHANNEL_IDS = {
    "10": -1002400466668,
    "11": -1002800050525,
    "12": -1002781513755,
}
DB_NAME = "final_medical_db.db" # استفاده از نام جدید برای اطمینان از تمیز بودن دیتابیس

# قیمت‌ها
PRICE_GRADE_SINGLE_DISCOUNT = "399,000"
PRICE_BUNDLE_DISCOUNT = "599,000"

# متن دکمه‌ها
BTN_COURSES = "🛍️ مشاهده و خرید دوره‌ها"
BTN_AI_IMAGES = "🎨 تصاویر هوش مصنوعی"
BTN_SUPPORT = "📞 پشتیبانی و مشاوره"
BTN_GRADE_10 = "پایه دهم"
BTN_GRADE_11 = "پایه یازدهم"
BTN_GRADE_12 = "پایه دوازدهم"
BTN_BUNDLE = "🎁 پکیج کامل (هر سه پایه)"
BTN_BACK = "🔙 بازگشت"

# متن پیام‌ها
MSG_WELCOME = "✨ به مدیکال مود خوش آمدید!\n\nدر اینجا، یادگیری برات آسون تر میشه. آماده‌اید تا شروع کنیم؟\n\nلطفا برای شروع، یکی از گزینه‌ها را انتخاب کنید."
MSG_SELECT_COURSE = "یک قدم تا موفقیت فاصله دارید! 🚀\n\nلطفا دوره مورد نظر خود را برای ادامه فرآیند ثبت‌نام انتخاب کنید."
MSG_PAYMENT_INSTRUCTION = """
سپاس از انتخاب شما! ✨

برای نهایی کردن ثبت‌نام، لطفا مبلغ مشخص شده را به شماره کارت زیر واریز نموده و سپس **تصویر واضح رسید پرداخت** را در همین صفحه ارسال فرمایید.

💳 **شماره کارت:**
`{card_number}`
(بانک سامان - به نام {card_holder_name})

**مبلغ قابل پرداخت: {price} تومان**

پس از ارسال رسید، درخواست شما بررسی و لینک‌های دوره بلافاصله برای شما ارسال خواهد شد.
"""
MSG_SUPPORT = f"برای ارتباط مستقیم با تیم پشتیبانی و مشاوره, به آیدی زیر پیام دهید:\n\n👤 {SUPPORT_USERNAME}"
MSG_AI_IMAGES = "این بخش در حال آماده‌سازی است."

# --- راه‌اندازی دیتابیس و لاگ ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS payments (user_id INTEGER PRIMARY KEY, username TEXT, product TEXT, status TEXT, submission_date TEXT)')
    conn.commit()
    return conn, cursor

conn, cursor = setup_database()

# --- توابع اصلی ربات ---

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی را نمایش می‌دهد."""
    keyboard = [[KeyboardButton(BTN_COURSES)], [KeyboardButton(BTN_AI_IMAGES), KeyboardButton(BTN_SUPPORT)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(MSG_WELCOME, reply_markup=reply_markup)

async def show_courses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی دوره‌ها را نمایش می‌دهد."""
    keyboard = [[KeyboardButton(BTN_GRADE_10), KeyboardButton(BTN_GRADE_11), KeyboardButton(BTN_GRADE_12)], [KeyboardButton(BTN_BUNDLE)], [KeyboardButton(BTN_BACK)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(MSG_SELECT_COURSE, reply_markup=reply_markup)

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """یک تابع واحد برای مدیریت تمام پیام‌های متنی و دکمه‌ها."""
    user_text = update.message.text
    user_id = update.effective_user.id

    # گزینه‌های منوی اصلی
    if user_text == BTN_COURSES:
        await show_courses_menu(update, context)
    elif user_text == BTN_SUPPORT:
        await update.message.reply_text(MSG_SUPPORT)
    elif user_text == BTN_AI_IMAGES:
        await update.message.reply_text(MSG_AI_IMAGES)
    elif user_text == BTN_BACK:
        await start_handler(update, context)

    # گزینه‌های انتخاب دوره
    elif user_text in [BTN_GRADE_10, BTN_GRADE_11, BTN_GRADE_12, BTN_BUNDLE]:
        product_map = {
            BTN_GRADE_10: "10",
            BTN_GRADE_11: "11",
            BTN_GRADE_12: "12",
            BTN_BUNDLE: "bundle"
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
        logger.info(f"کاربر {user_id} محصول '{product_choice}' را انتخاب کرد و در حافظه موقت ذخیره شد.")

        payment_message = MSG_PAYMENT_INSTRUCTION.format(
            card_number=CARD_NUMBER,
            card_holder_name=CARD_HOLDER_NAME,
            price=selected_price
        )
        await update.message.reply_text(payment_message, parse_mode='HTML')
    
    else:
        await update.message.reply_text("لطفا از دکمه‌های موجود استفاده کنید.")


async def handle_receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسید کاربر را مدیریت می‌کند."""
    user = update.message.from_user
    if 'selected_product' not in context.user_data:
        await update.message.reply_text("خطا: لطفا ابتدا یکی از دوره‌ها را انتخاب کنید و سپس رسید را ارسال نمایید.")
        return
        
    product = context.user_data['selected_product']
    
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO payments (user_id, username, product, status, submission_date) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username or "None", product.strip(), "در انتظار", datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"خطای دیتابیس: {e}")
        await update.message.reply_text("خطایی در ثبت اطلاعات رخ داد.")
        return

    await update.message.reply_text("✅ رسید شما با موفقیت دریافت شد و برای پشتیبانی ارسال گردید.")
    
    keyboard = [[InlineKeyboardButton("✅ تایید", callback_data=f'approve_{user.id}'), InlineKeyboardButton("❌ رد", callback_data=f'reject_{user.id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption_text = f"📬 رسید جدید\n\nکاربر: @{user.username} ({user.id})\nمحصول: {product}"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=caption_text, reply_markup=reply_markup)
    del context.user_data['selected_product']


async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """کلیک‌های ادمین را مدیریت می‌کند."""
    query = update.callback_query
    await query.answer()
    
    action, user_id_str = query.data.split('_')
    user_id = int(user_id_str)
    
    cursor.execute("SELECT product, username FROM payments WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        await query.edit_message_caption(caption="خطا: کاربر یافت نشد.")
        return
        
    product, username = result[0].strip(), result[1]

    if action == "approve":
        try:
            if product == "bundle":
                bundle_grades = ["10", "11", "12"]
                invite_links = []
                for grade in bundle_grades:
                    channel_id = CHANNEL_IDS.get(grade)
                    if channel_id:
                        expire_date = datetime.now() + timedelta(days=1)
                        link = await context.bot.create_chat_invite_link(chat_id=channel_id, member_limit=1, expire_date=expire_date)
                        invite_links.append(f"🔗 لینک دوره پایه {grade}م: {link.invite_link}")
                
                if len(invite_links) == len(bundle_grades):
                    links_text = "\n\n".join(invite_links)
                    welcome_message = f"✅ ثبت‌نام شما در پکیج جامع با موفقیت انجام شد!\n\nلینک‌های دسترسی به هر سه دوره:\n\n{links_text}\n\n⚠️ هر لینک یکبار مصرف است."
                    await context.bot.send_message(chat_id=user_id, text=welcome_message)
                    await query.edit_message_caption(caption=f"✅ کاربر @{username} (پکیج جامع) تایید شد.")
                else:
                    await query.edit_message_caption(caption="❌ خطا در ساخت لینک‌های پکیج.")
            else:
                channel_id = CHANNEL_IDS.get(product)
                if not channel_id:
                    await query.edit_message_caption(caption=f"❌ خطا: شناسه کانال برای «{product}» تعریف نشده.")
                    return

                expire_date = datetime.now() + timedelta(days=1)
                invite_link = await context.bot.create_chat_invite_link(chat_id=channel_id, member_limit=1, expire_date=expire_date)
                welcome_message = f"✅ ثبت‌نام شما تایید شد!\n\nلینک ورود به دوره:\n{invite_link.invite_link}\n\n⚠️ این لینک یکبار مصرف است."
                await context.bot.send_message(chat_id=user_id, text=welcome_message)
                await query.edit_message_caption(caption=f"✅ کاربر @{username} (محصول: {product}) تایید شد.")

            cursor.execute("UPDATE payments SET status = ? WHERE user_id = ?", ("تایید شده", user_id))
            conn.commit()
        except Exception as e:
            logger.error(f"خطا در تایید کاربر {user_id}: {e}", exc_info=True)
            await query.edit_message_caption(caption="❌ خطای پیش‌بینی نشده. لاگ‌ها را بررسی کنید.")
            
    elif action == "reject":
        cursor.execute("UPDATE payments SET status = ? WHERE user_id = ?", ("رد شده", user_id))
        conn.commit()
        await context.bot.send_message(chat_id=user_id, text="❌ پرداخت شما تایید نشد.")
        await query.edit_message_caption(caption=f"❌ کاربر @{username} رد شد.")

# --- تابع اصلی برای اجرای ربات ---
def main():
    if not TOKEN or not ADMIN_ID:
        logger.error("خطا: توکن یا ادمین آیدی تعریف نشده!")
        return

    application = Application.builder().token(TOKEN).build()
    
    # ثبت دستورات اصلی
    application.add_handler(CommandHandler('start', start_handler))
    
    # ثبت یک Handler واحد برای تمام پیام‌های متنی
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    # ثبت Handler برای عکس‌ها (رسید)
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt_handler))
    
    # ثبت Handler برای دکمه‌های ادمین
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^(approve_|reject_)'))

    logger.info("ربات با موفقیت راه‌اندازی شد و در حال اجرا است...")
    application.run_polling()

if __name__ == '__main__':
    main()