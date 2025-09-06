# main.py - نسخه نهایی و تمیز شده

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
# ما ادمین آیدی را به عدد صحیح تبدیل می‌کنیم و برای جلوگیری از خطا در صورت عدم وجود، یک مقدار پیش‌فرض می‌گذاریم
try:
    ADMIN_ID = int(os.getenv('ADMIN_ID'))
except (TypeError, ValueError):
    ADMIN_ID = None # اگر تعریف نشده بود، None باشد

# --- فاز ۳: تنظیمات و متن‌های ثابت ---
SUPPORT_USERNAME = "@Jaber_far"
CHANNEL_IDS = {
    "10": -1002400466668,
    "11": -1002800050525,
    "12": -1002781513755,
}
DB_NAME = "membership_data.db"
BTN_COURSES = "🛍️ خرید دوره انیمیشن"
BTN_AI_IMAGES = "🎨 تصاویر هوش مصنوعی"
BTN_SUPPORT = "📞 پشتیبانی"
BTN_GRADE_10 = "پایه دهم"
BTN_GRADE_11 = "پایه یازدهم"
BTN_GRADE_12 = "پایه دوازدهم"
BTN_BUNDLE = "🎁 هر سه پایه (با تخفیف)"
BTN_BACK = "🔙 بازگشت به منوی اصلی"
MSG_WELCOME = "سلام! به ربات ما خوش آمدید. لطفا یکی از گزینه‌های زیر را انتخاب کنید:"
MSG_SELECT_COURSE = "عالی! لطفا دوره مورد نظر خود را انتخاب کنید:"
MSG_SUPPORT = f"در صورت نیاز به پشتیبانی، می‌توانید با آیدی {SUPPORT_USERNAME} در ارتباط باشید."
MSG_AI_IMAGES = "این بخش به زودی فعال خواهد شد. منتظر خبرهای هیجان‌انگیز ما باشید!"

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
    await update.message.reply_text(MSG_SELECT_COURSE, reply_markup=reply_markup)

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
    product_choice = product_map.get(user_text)
    context.user_data['selected_product'] = product_choice
    await update.message.reply_text(
        f"شما «{user_text}» را انتخاب کردید.\n\n"
        "لطفا تصویر رسید پرداخت خود را ارسال کنید."
    )

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

    await update.message.reply_text("✅ رسید شما دریافت و برای مدیر ارسال شد. لطفا تا زمان تایید صبور باشید.")
    
    keyboard = [[
        InlineKeyboardButton("✅ تایید", callback_data=f'approve_{user.id}'),
        InlineKeyboardButton("❌ رد", callback_data=f'reject_{user.id}')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption_text = f"📬 رسید جدید\n\nکاربر: @{user.username} (ID: {user.id})\nمحصول: {product}"
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file_id, caption=caption_text, reply_markup=reply_markup)
    del context.user_data['selected_product']

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id_str = query.data.split('_')
    user_id = int(user_id_str)
    
    cursor.execute("SELECT product, username FROM payments WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        await query.edit_message_caption(caption="خطا: کاربر یافت نشد.")
        return
        
    product, username = result

    if action == "approve":
        try:
            if product == "bundle":
                bundle_products = ["10", "11", "12"]
                invite_links = []
                for grade in bundle_products:
                    channel_id = CHANNEL_IDS.get(grade)
                    if channel_id:
                        expire_date = datetime.now() + timedelta(days=1)
                        link = await context.bot.create_chat_invite_link(chat_id=channel_id, member_limit=1, expire_date=expire_date)
                        invite_links.append(f"لینک پایه {grade}م: {link.invite_link}")
                
                if len(invite_links) == 3:
                    links_text = "\n".join(invite_links)
                    welcome_message = f"✅ پرداخت شما برای بسته کامل تایید شد!\n\nلینک‌های عضویت شما:\n\n{links_text}\n\n⚠️ هر لینک یکبار مصرف است."
                    await context.bot.send_message(chat_id=user_id, text=welcome_message)
                    await query.edit_message_caption(caption=f"✅ کاربر @{username} (بسته کامل) تایید شد و ۳ لینک ارسال گردید.")
                else:
                    await query.edit_message_caption(caption="❌ خطا: مشکلی در ساخت لینک برای بسته کامل رخ داد.")
            else:
                channel_id = CHANNEL_IDS.get(product)
                if not channel_id:
                    await query.edit_message_caption(caption=f"❌ خطا: شناسه کانال برای محصول «{product}» تعریف نشده.")
                    return

                expire_date = datetime.now() + timedelta(days=1)
                invite_link = await context.bot.create_chat_invite_link(chat_id=channel_id, member_limit=1, expire_date=expire_date)
                welcome_message = f"✅ پرداخت شما تایید شد!\n\nلینک عضویت شما:\n{invite_link.invite_link}\n\n⚠️ این لینک یکبار مصرف است."
                await context.bot.send_message(chat_id=user_id, text=welcome_message)
                await query.edit_message_caption(caption=f"✅ کاربر @{username} (محصول: {product}) تایید شد.")

            cursor.execute("UPDATE payments SET status = ? WHERE user_id = ?", ("تایید شده", user_id))
            conn.commit()

        except Forbidden:
            await query.edit_message_caption(caption=f"❌ خطا: کاربر @{username} ربات را بلاک کرده است.")
        except Exception as e:
            logger.error(f"خطا در تایید کاربر {user_id}: {e}")
            await query.edit_message_caption(caption="❌ خطا در ساخت لینک. آیا ربات در تمام کانال‌ها ادمین است؟")
            
    elif action == "reject":
        cursor.execute("UPDATE payments SET status = ? WHERE user_id = ?", ("رد شده", user_id))
        conn.commit()
        await context.bot.send_message(chat_id=user_id, text="❌ متاسفانه پرداخت شما تایید نشد.")
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