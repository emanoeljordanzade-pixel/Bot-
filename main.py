import os
import sqlite3
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

# ----------------- تنظیمات اختصاصی علیرضا -----------------
BOT_TOKEN = "8623315494:AAEQLWDt-IUC39TIUJIVnRRZGgVvo83Pepw" 
ADMIN_ID = 7374971382        # آیدی عددی شما جهت پیام‌های مستقیم ضروری
ADMIN_GROUP_ID = -1004294169429  # 🔴 حتماً آیدی عددی گروه ادمین خودت رو اینجا بذار (با منفی شروع میشه)

CARD_NUMBER = "5892101542283284"
ACCOUNT_NAME = "علیرضا واحدانی"
# -----------------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)
telebot.apihelper.API_URL = "https://api.telegram.org/bot{0}/{1}"
app = Flask('')

# --- دیتابیس واسط برای ذخیره اطلاعات سیستم رفرال و مالی ---
def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, name TEXT, balance INTEGER DEFAULT 0, referred_by INTEGER, gift_claimed INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan_name TEXT, config_data TEXT DEFAULT '')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pending_deposits 
                      (msg_id INTEGER PRIMARY KEY, user_id INTEGER, amount INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# متون تعرفه با اعمال تخفیف رفرال (۵ درصد برای دعوت شده)
PLANS = {
    "10gb": {"name": "🩵 ۱۰ گیگابایت نامحدود", "price": 175000, "discount_price": 166250},
    "20gb": {"name": "💙 ۲۰ گیگابایت نامحدود", "price": 325000, "discount_price": 308750},
    "30gb": {"name": "🩷 ۳۰ گیگابایت نامحدود", "price": 430000, "discount_price": 408500},
    "40gb": {"name": "❤️‍🔥 ۴۰ گیگابایت نامحدود", "price": 560000, "discount_price": 532000}
}

WELCOME_TEXT = (
    "🚀 <b>سلام رفیق! به دنیای اینترنت بدون مرز خوش اومدی!</b> 😎\n\n"
    "دنبال یه اتصال پرسرعت، بدون قطعی و کاملاً پایدار می‌گردی؟ جای درستی اومدی! "
    "اینجا همه‌ی کانفیگ‌ها زمان و کاربرشون <b>نامحدوده</b> و رو همه‌ی اپ‌ها مِثِ فرفره کار می‌کنه! 🔥\n\n"
    "📣 <b>یه خبر توپ و پر از تخفیف:</b>\n"
    "با دعوت کردن دوستات به ربات، هم به اونا حال بده هم به خودت! 😉\n"
    "👥 دوستت تو اولین خریدش <b>٪۵ تخفیف</b> می‌گیره و <b>٪۷ از مبلغ خریدش</b> مستقیم میشینه تو کیف پول تو!\n"
    "🎁 جذاب‌تر از همه: <u>اگه ۱۰ نفر رو دعوت کنی که خرید کنن، یه کانفیگ ۵ گیگابایتی کاملاً رایگان از طرف علیرضا جایزه می‌گیری!</u>"
)

@app.route('/')
def home(): return "Bot is Active"

# منوی اصلی ثابت (تغییر نمی‌کند تا کاربر همیشه دسترسی داشته باشد)
def main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🛒 فروشگاه و لیست قیمت"), KeyboardButton("👤 حساب کاربری"))
    markup.add(KeyboardButton("💼 کیف پول من"), KeyboardButton("🔗 دریافت لینک دعوت"))
    markup.add(KeyboardButton("👨‍💻 پشتیبانی آنلاین"))
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    username = message.from_user.username or "ندارد"
    name = message.from_user.first_name
    
    # بررسی کد رفرال
    args = message.text.split()
    referrer = None
    if len(args) > 1 and args[1].isdigit():
        referrer = int(args[1])
        if referrer == user_id: referrer = None

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute("INSERT INTO users (user_id, username, name, referred_by) VALUES (?, ?, ?, ?)", 
                       (user_id, username, name, referrer))
        conn.commit()
    conn.close()
    
    bot.send_message(user_id, WELCOME_TEXT, parse_mode="HTML", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_menu_clicks(message):
    user_id = message.chat.id
    
    if message.text == "🛒 فروشگاه و لیست قیمت":
        send_store_menu(user_id)
    elif message.text == "👤 حساب کاربری":
        send_profile_menu(user_id)
    elif message.text == "💼 کیف پول من":
        send_wallet_menu(user_id)
    elif message.text == "🔗 دریافت لینک دعوت":
        bot.send_message(user_id, f"🎉 <b>لینک دعوت اختصاصی شما:</b>\nhttps://t.me/{bot.get_me().username}?start={user_id}\n\nاین لینک رو بفرست برای دوستات؛ اونا ۵٪ تخفیف می‌گیرن و تو هم ۷٪ سودِ مادی و شانس برنده شدن ۵ گیگابایت هدیه! 🚀", parse_mode="HTML")
    elif message.text == "👨‍💻 پشتیبانی آنلاین":
        bot.send_message(user_id, "💬 رفیق برای حل هرگونه مشکل، خرید عمده یا مشاوره مستقیم می‌تونی با آیدی زیر در ارتباط باشی:\n\n🆔 @AIireza_1383")

# --- منوی فروشگاه (Inline برای جلوگیری از شلوغی چت) ---
def send_store_menu(user_id, message_id=None):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
    ref = cursor.fetchone()[0]
    conn.close()
    
    has_discount = ref is not None
    text = "🛍️ <b>لیست پلن‌های VIP (زمان و کاربر نامحدود):</b>\n\n"
    if has_discount:
        text += "🌟 تبریک! چون با لینک دعوت اومدی، <b>۵٪ تخفیف اختصاصی</b> روی همه‌ی پلن‌ها برات اعمال شد:\n\n"
    
    markup = InlineKeyboardMarkup()
    for key, info in PLANS.items():
        final_price = info["discount_price"] if has_discount else info["price"]
        text += f"▪️ {info['name']} 👈 <b>{final_price:,}</b> تومان\n"
        markup.add(InlineKeyboardButton(f"خرید {info['name']}", callback_data=f"buy_{key}"))
        
    text += "\n📶 تست شده روی تمام اپراتورها با بالاترین پروتکل‌های امنیتی."
    
    if message_id:
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)

# --- منوی کیف پول ---
def send_wallet_menu(user_id, message_id=None):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    conn.close()
    
    text = f"💼 <b>وضعیت کیف پول شما:</b>\n\n💵 موجودی فعلی: <b>{balance:,}</b> تومان\n\nمی‌تونی کیف پولت رو شارژ کنی و خیلی راحت و خودکار خریدت رو انجام بدی!"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💳 شارژ حساب", callback_data="wallet_charge"))
    if message_id:
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)

# --- منوی حساب کاربری ---
def send_profile_menu(user_id, message_id=None):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    # شمارش کسانی که دعوت شدند و خرید کردند
    cursor.execute("""SELECT COUNT(DISTINCT users.user_id) FROM users 
                      JOIN orders ON users.user_id = orders.user_id 
                      WHERE users.referred_by = ?""", (user_id,))
    successful_invites = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(order_id) FROM orders WHERE user_id = ?", (user_id,))
    total_purchases = cursor.fetchone()[0]
    
    cursor.execute("SELECT order_id, plan_name FROM orders WHERE user_id = ?", (user_id,))
    history = cursor.fetchall()
    conn.close()
    
    text = (
        f"👤 <b>پروفایل شما:</b>\n\n"
        f"👥 تعداد دعوت‌های موفق (با خرید): <b>{successful_invites} نفر</b>\n"
        f"📦 تعداد کل خریدهای شما: <b>{total_purchases} بار</b>\n\n"
        f"📜 <b>لیست کانفیگ‌های خریداری شده شما:</b>\n"
    )
    
    markup = InlineKeyboardMarkup()
    if history:
        text += "برای دریافت و دیدن دوباره‌ی هر کانفیگ، روی دکمه‌ی مربوط به اون در زیر کلیک کن 👇"
        for idx, item in history:
            markup.add(InlineKeyboardButton(f"🔑 {item[0]} (کد {idx})", callback_data=f"view_config_{idx}"))
    else:
        text += "هیچ کانفیگی تا حالا نخریدی رفیق!"
        
    if message_id:
        bot.edit_message_text(text, user_id, message_id, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)

# --- مدیریت دکمه‌های Inline ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if call.data == "back_to_store":
        send_store_menu(user_id, msg_id)
    elif call.data == "back_to_wallet":
        send_wallet_menu(user_id, msg_id)
        
    elif call.data.startswith("buy_"):
        plan_key = call.data.split("_")[1]
        process_plan_purchase(user_id, msg_id, plan_key)
        
    elif call.data == "wallet_charge":
        text = f"💳 <b>درخواست شارژ کیف پول</b>\n\n💰 لطفاً مبلغ مورد نظرت رو به تومان وارد کن:\n(مثال: 175000)\n\n"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 برگشت", callback_data="back_to_wallet"))
        msg = bot.edit_message_text(text, user_id, msg_id, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, receive_charge_amount)
        
    elif call.data.startswith("view_config_"):
        order_id = int(call.data.split("_")[2])
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute("SELECT plan_name, config_data FROM orders WHERE order_id = ? AND user_id = ?", (order_id, user_id))
        res = cursor.fetchone()
        conn.close()
        if res and res[1]:
            bot.send_message(user_id, f"📦 <b>کانفیگ شما برای پلن {res[0]}:</b>\n\n<code>{res[1]}</code>", parse_mode="HTML")
        else:
            bot.send_message(user_id, "❌ این کانفیگ هنوز توسط ادمین صادر نشده یا در دسترس نیست.")
            
    bot.answer_callback_query(call.id)

# --- فرآیند خرید خودکار با کیف پول ---
def process_plan_purchase(user_id, msg_id, plan_key):
    info = PLANS[plan_key]
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance, referred_by FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    balance, ref = res[0], res[1]
    
    price = info["discount_price"] if ref else info["price"]
    
    if balance >= price:
        # کسر موجودی و ثبت سفارش
        new_balance = balance - price
        cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        cursor.execute("INSERT INTO orders (user_id, plan_name) VALUES (?, ?)", (user_id, info["name"]))
        order_id = cursor.lastrowid
        conn.commit()
        
        # واریز سود پورسانت رفرال برای معرف (۷ درصد قیمت کل پلن)
        if ref:
            reward = int(info["price"] * 0.07)
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, ref))
            conn.commit()
            try: bot.send_message(ref, f"🎉 یکی از دوستانی که دعوت کردی خرید انجام داد و <b>{reward:,} تومان</b> سود به کیف پولت واریز شد!", parse_mode="HTML")
            except: pass
            
            # بررسی قانون ۱۰ دعوت موفق برای هدیه ۵ گیگی
            cursor.execute("SELECT COUNT(DISTINCT users.user_id) FROM users JOIN orders ON users.user_id = orders.user_id WHERE users.referred_by = ?", (ref,))
            invites_count = cursor.fetchone()[0]
            cursor.execute("SELECT gift_claimed FROM users WHERE user_id = ?", (ref,))
            gift_claimed = cursor.fetchone()[0]
            
            if invites_count >= 10 and gift_claimed == 0:
                cursor.execute("UPDATE users SET gift_claimed = 1 WHERE user_id = ?", (ref,))
                conn.commit()
                # اعلام به ادمین در گروه برای ریپلای کانفیگ هدیه
                bot.send_message(ADMIN_GROUP_ID, f"🎁🏆 <b>کاربر برنده جایزه دعوت شد!</b>\n\nکاربر آیدی: <code>{ref}</code> موفق شد ۱۰ نفر خریدار واقعی دعوت کنه!\nلطفاً روی همین پیام <u>کانفیگ هدیه ۵ گیگابایتی</u> رو ریپلای کنید.")

        conn.close()
        
        bot.edit_message_text(f"✅ <b>خرید با موفقیت انجام شد!</b>\n💰 مبلغ {price:,} تومان از کیف پول شما کسر شد.\nسفارش شما برای ادمین جهت صادر کردن کانفیگ ارسال گردید و به زودی تحویل داده میشه.", user_id, msg_id, parse_mode="HTML")
        
        # اطلاع‌رسانی در گروه ادمین
        bot.send_message(ADMIN_GROUP_ID, f"🛒 <b>خرید جدید با کیف پول!</b>\n\n👤 خریدار: <code>{user_id}</code>\n📦 پلن: {info['name']}\n💰 کسر شده: {price:,} تومان\n\n🆔 شماره سفارش: <code>{order_id}</code>\n🔴 <b>ادمین عزیز، لطفاً کانفیگ رو روی همین پیام ریپلای کن تا برای کاربر فرستاده بشه.</b>", parse_mode="HTML")
    else:
        conn.close()
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💳 شارژ کیف پول", callback_data="wallet_charge"), InlineKeyboardButton("🔙 برگشت", callback_data="back_to_store"))
        bot.edit_message_text(f"❌ <b>موجودی کیف پول شما کافی نیست رفیق!</b>\n\n💵 قیمت پلن: {price:,} تومان\n💼 موجودی شما: {balance:,} تومان\n\nلطفاً اول کیف پولت رو شارژ کن.", user_id, msg_id, parse_mode="HTML", reply_markup=markup)

# --- مراحل دریافت مبلغ و رسید شارژ حساب ---
def receive_charge_amount(message):
    user_id = message.chat.id
    amount_text = message.text
    
    if not amount_text.isdigit():
        msg = bot.send_message(user_id, "❌ لطفا فقط عدد وارد کنید. دوباره مبلغ رو بفرستید:")
        bot.register_next_step_handler(msg, receive_charge_amount)
        return
        
    amount = int(amount_text)
    instructions = (
        f"💵 <b>درخواست شارژ حساب به مبلغ: {amount:,} تومان</b>\n\n"
        f"💳 شماره کارت جهت واریز:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: {ACCOUNT_NAME}\n\n"
        f"📥 لطفاً پس از واریز، <b>فقط عکس رسید پرداخت</b> رو برام بفرست تا ادمین تاییدش کنه."
    )
    msg = bot.send_message(user_id, instructions, parse_mode="HTML")
    bot.register_next_step_handler(msg, receive_receipt_photo, amount)

def receive_receipt_photo(message, amount):
    user_id = message.chat.id
    if message.content_type == 'photo':
        bot.send_message(user_id, "✅ رسید شما دریافت شد و برای تایید به گروه حسابداری علیرضا ارسال شد. به محض تایید حساب شما شارژ میشه!")
        
        # ارسال رسید به گروه ادمین‌ها
        admin_msg = bot.send_photo(
            ADMIN_GROUP_ID, 
            message.photo[-1].file_id, 
            caption=f"💰 <b>رسید جدید برای شارژ کیف پول!</b>\n\n👤 کاربر خریدار: <code>{user_id}</code>\n💵 مبلغ اعلامی کاربر: <b>{amount:,}</b> تومان\n\n🔴 <b>ادمین عزیز، برای تایید نهایی دقیقاً مبلغ تایید شده رو به تومان روی همین عکس ریپلای کن.</b>",
            parse_mode="HTML"
        )
        
        # ذخیره موقت درخواست در دیتابیس برای بررسی ریپلای ادمین
        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pending_deposits (msg_id, user_id, amount) VALUES (?, ?, ?)", (admin_msg.message_id, user_id, amount))
        conn.commit()
        conn.close()
    else:
        msg = bot.send_message(user_id, "❌ خطاست! لطفاً فقط فایل عکسِ رسید رو بفرستید:")
        bot.register_next_step_handler(msg, receive_receipt_photo, amount)

# --- هندلر جامع ریپلای‌های ادمین در گروه ادمین ---
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_GROUP_ID and m.reply_to_message is not None)
def handle_admin_replies(message):
    reply_id = message.reply_to_message.message_id
    admin_text = message.text
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    
    # حالت اول: تایید فیش و شارژ کیف پول
    cursor.execute("SELECT user_id, amount FROM pending_deposits WHERE msg_id = ?", (reply_id,))
    deposit = cursor.fetchone()
    
    if deposit:
        user_id, default_amount = deposit[0], deposit[1]
        final_amount = int(admin_text) if admin_text.isdigit() else default_amount
        
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (final_amount, user_id))
        cursor.execute("DELETE FROM pending_deposits WHERE msg_id = ?", (reply_id,))
        conn.commit()
        conn.close()
        
        bot.send_message(ADMIN_GROUP_ID, f"✅ حساب کاربر <code>{user_id}</code> با موفقیت به مبلغ {final_amount:,} تومان شارژ شد.")
        bot.send_message(user_id, f"🎉 <b>کیف پول شما شارژ شد!</b>\n\n💵 مبلغ <b>{final_amount:,} تومان</b> به حساب شما اضافه شد. الان می‌تونی از دکمه فروشگاه خریدت رو خودکار نهایی کنی!")
        return

    # حالت دوم: تحویل کانفیگ عادی یا تحویل جایزه ۱۰ رفرال
    orig_caption = message.reply_to_message.caption or ""
    orig_text = message.reply_to_message.text or ""
    
    # بررسی خریدهای کیف پول
    if "خرید جدید با کیف پول!" in orig_text:
        lines = orig_text.split('\n')
        target_user = None
        order_id = None
        for line in lines:
            if "خریدار:" in line: target_user = int(line.split('<code>')[1].split('</code>')[0])
            if "شماره سفارش:" in line: order_id = int(line.split('<code>')[1].split('</code>')[0])
            
        if target_user and order_id:
            cursor.execute("UPDATE orders SET config_data = ? WHERE order_id = ?", (admin_text, order_id))
            conn.commit()
            conn.close()
            bot.send_message(target_user, f"🚀 <b>کانفیگ شما صادر شد رفیق!</b>\n\n📥 هر زمان خواستید می‌تونید توی منوی «👤 حساب کاربری» هم بهش دسترسی داشته باشید.\n\n<code>{admin_text}</code>", parse_mode="HTML")
            bot.send_message(ADMIN_GROUP_ID, "✅ کانفیگ با موفقیت برای کاربر ارسال و در سوابقش ذخیره شد.")
            return

    # بررسی اهدای جایزه ۱۰ رفرال فعال
    if "🎁🏆 کاربر برنده جایزه دعوت شد!" in orig_text:
        lines = orig_text.split('\n')
        target_user = None
        for line in lines:
            if "کاربر آیدی:" in line: target_user = int(line.split('<code>')[1].split('</code>')[0])
            
        if target_user:
            conn.close()
            thanks_msg = (
                f"❤️ <b>هدیه ویژه علیرضا تقدیم به شما رفیق با معرفت!</b> 🥰\n\n"
                f"دمت گرم که ربات ما رو به دوستات معرفی کردی و باعث شدی خانواده‌مون بزرگتر بشه. "
                f"این کانفیگ ۵ گیگابایتی هدیه، به پاس قدردانی از حمایت‌های بی‌دریغ شماست:\n\n"
                f"<code>{admin_text}</code>\n\n"
                f"امیدوارم از سرعتش لذت ببری! باز هم دوستات رو دعوت کن و هدیه بگیر 😉✨"
            )
            bot.send_message(target_user, thanks_msg, parse_mode="HTML")
            bot.send_message(ADMIN_GROUP_ID, "✅ کانفیگ هدیه با متن تقدیر گرم برای کاربر ارسال شد.")
            return

    conn.close()

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=7860)).start()
    print("Advanced Bot is starting...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
