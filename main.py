import os
import sqlite3
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread

# ----------------- تنظیمات اختصاصی شما -----------------
BOT_TOKEN = "8623315494:AAEQLWDt-IUC39TIUJIVnRRZGgVvo83Pepw" 
ADMIN_ID = 7374971382        
ADMIN_GROUP_ID = -1004294169429  # 🔴 آیدی عددی گروه ادمینت رو اینجا بذار (حتما با منفی شروع بشه)

CARD_NUMBER = "5892101542283284"
ACCOUNT_NAME = "علیرضا واحدانی"
# -------------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)
telebot.apihelper.API_URL = "https://api.telegram.org/bot{0}/{1}"
app = Flask('')

# --- دیتابیس هوشمند فروشگاه ---
def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, name TEXT, balance INTEGER DEFAULT 0, referred_by INTEGER, gifts_claimed INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders 
                      (order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, plan_name TEXT, config_data TEXT DEFAULT '')''')
    conn.commit()
    conn.close()

init_db()

PLANS = {
    "10gb": {"name": "🩵 ۱۰ گیگابایت نامحدود", "price": 175000, "discount_price": 166250},
    "20gb": {"name": "💙 ۲۰ گیگابایت نامحدود", "price": 325000, "discount_price": 308750},
    "30gb": {"name": "🩷 ۳۰ گیگابایت نامحدود", "price": 430000, "discount_price": 408500},
    "40gb": {"name": "❤️‍🔥 ۴۰ گیگابایت نامحدود", "price": 560000, "discount_price": 532000}
}

def get_main_markup():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛒 فروشگاه و خرید", callback_data="store"), InlineKeyboardButton("👤 حساب کاربری", callback_data="profile"))
    markup.row(InlineKeyboardButton("💼 کیف پول من", callback_data="wallet"), InlineKeyboardButton("🔗 دریافت لینک دعوت", callback_data="invite"))
    markup.row(InlineKeyboardButton("👨‍💻 پشتیبانی آنلاین", callback_data="support"))
    return markup

@app.route('/')
def home(): return "Bot is Active"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    bot.clear_step_handler_by_chat_id(user_id) # پاک کردن مراحل قبلی در صورت استارت مجدد
    username = message.from_user.username or "ندارد"
    name = message.from_user.first_name
    
    args = message.text.split()
    referrer = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    if referrer == user_id: referrer = None

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username, name, referred_by) VALUES (?, ?, ?, ?)", (user_id, username, name, referrer))
        conn.commit()
    conn.close()
    
    text = (
        "🚀 <b>سلام رفیق! به دنیای اینترنت آزاد و بدون قطعی خوش اومدی!</b> 😎\n\n"
        "اینجا می‌تونی با خیال راحت کانفیگ‌های V2Ray قدرتمند و نامحدود (از نظر کاربر و زمان) رو تهیه کنی.\n\n"
        "🔥 <b>طرح تخفیف و درآمدزایی:</b>\n"
        "دوستات رو به ربات دعوت کن!\n"
        "🎁 دوستت همون اول <b>۵٪ تخفیف</b> می‌گیره.\n"
        "💰 تو هم <b>۷٪ از مبلغ خریدش</b> مستقیم میاد تو کیف پولت!\n"
        "🏆 <b>و اما جایزه بزرگ:</b> اگه هر ۱۰ نفر با لینک تو خرید کنن، یه کانفیگ ۵ گیگابایتی رایگان از من جایزه می‌گیری!"
    )
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=get_main_markup())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data
    
    # دکمه‌های بازگشت و لغو مراحل
    bot.clear_step_handler_by_chat_id(user_id) 

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    if data == "main_menu":
        bot.edit_message_text("🏠 <b>به منوی اصلی برگشتیم.</b> یک گزینه رو انتخاب کن:", user_id, msg_id, parse_mode="HTML", reply_markup=get_main_markup())
        
    elif data == "store":
        cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
        ref = cursor.fetchone()[0]
        has_discount = ref is not None
        
        text = "🛍️ <b>لیست پلن‌های VIP (تعداد کاربر نامحدود / زمان نامحدود ⚠️)</b>\n\n"
        if has_discount: text += "🌟 <b>۵٪ تخفیف معرف برای شما فعال است!</b>\n\n"
        
        markup = InlineKeyboardMarkup()
        for key, info in PLANS.items():
            final_price = info["discount_price"] if has_discount else info["price"]
            text += f"▪️ {info['name']} 👈 <b>{final_price:,}</b> تومان\n"
            markup.add(InlineKeyboardButton(f"خرید {info['name']}", callback_data=f"select_{key}"))
        markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu"))
        
        bot.edit_message_text(text, user_id, msg_id, parse_mode="HTML", reply_markup=markup)

    elif data.startswith("select_"):
        plan_key = data.split("_")[1]
        info = PLANS[plan_key]
        
        cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
        ref = cursor.fetchone()[0]
        final_price = info["discount_price"] if ref else info["price"]
        
        text = f"🛒 <b>انتخاب روش پرداخت برای {info['name']}</b>\n\nمبلغ قابل پرداخت: <b>{final_price:,} تومان</b>\n\nلطفاً یکی از روش‌های زیر رو برای پرداخت انتخاب کن:"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("💳 پرداخت کارت به کارت (مستقیم)", callback_data=f"directpay_{plan_key}_{final_price}"))
        markup.row(InlineKeyboardButton("💼 پرداخت از طریق موجودی کیف پول", callback_data=f"walletpay_{plan_key}_{final_price}"))
        markup.add(InlineKeyboardButton("🔙 بازگشت به فروشگاه", callback_data="store"))
        bot.edit_message_text(text, user_id, msg_id, parse_mode="HTML", reply_markup=markup)

    elif data == "profile":
        cursor.execute("SELECT COUNT(DISTINCT orders.user_id) FROM users JOIN orders ON users.user_id = orders.user_id WHERE users.referred_by = ?", (user_id,))
        successful_invites = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(order_id) FROM orders WHERE user_id = ?", (user_id,))
        total_purchases = cursor.fetchone()[0]
        cursor.execute("SELECT order_id, plan_name FROM orders WHERE user_id = ?", (user_id,))
        history = cursor.fetchall()
        
        text = (f"👤 <b>حساب کاربری شما:</b>\n\n👥 تعداد دعوت‌های موفق (با خرید): <b>{successful_invites} نفر</b>\n"
                f"📦 تعداد کل خریدهای شما: <b>{total_purchases} بار</b>\n\n📜 <b>لیست کانفیگ‌های شما:</b>\n")
        
        markup = InlineKeyboardMarkup()
        if history:
            text += "روی هرکدام کلیک کنید تا مجدداً ارسال شود 👇"
            for idx, item in history:
                markup.add(InlineKeyboardButton(f"🔑 {item[1]} (کد {idx})", callback_data=f"view_{idx}"))
        else:
            text += "هیچ کانفیگی خریداری نشده است."
        markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu"))
        bot.edit_message_text(text, user_id, msg_id, parse_mode="HTML", reply_markup=markup)

    elif data.startswith("view_"):
        order_id = int(data.split("_")[1])
        cursor.execute("SELECT plan_name, config_data FROM orders WHERE order_id = ? AND user_id = ?", (order_id, user_id))
        res = cursor.fetchone()
        if res and res[1]:
            bot.send_message(user_id, f"📦 <b>کانفیگ شما برای پلن {res[0]}:</b>\n\n<code>{res[1]}</code>", parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "❌ این کانفیگ هنوز صادر نشده است.", show_alert=True)

    elif data == "wallet":
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = cursor.fetchone()[0]
        
        text = f"💼 <b>کیف پول من</b>\n\n💵 موجودی فعلی شما: <b>{balance:,}</b> تومان\n\nبرای خرید سریع‌تر و خودکار می‌تونی حسابتو شارژ کنی."
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 شارژ موجودی کیف پول", callback_data="charge_req"))
        markup.add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu"))
        bot.edit_message_text(text, user_id, msg_id, parse_mode="HTML", reply_markup=markup)

    elif data == "invite":
        bot.send_message(user_id, f"🎉 <b>لینک دعوت اختصاصی شما:</b>\n\nhttps://t.me/{bot.get_me().username}?start={user_id}\n\nاین لینک رو پخش کن و با هر خرید دوستات <b>۷٪ پورسانت مستقیم</b> بگیر! هر ۱۰ خرید = یک کانفیگ هدیه ۵ گیگابایتی. 🚀", parse_mode="HTML")

    elif data == "support":
        bot.send_message(user_id, "💬 رفیق برای حل مشکلات، خرید عمده یا مشاوره مستقیم به آیدی زیر پیام بده:\n🆔 @AIireza_1383")

    # ----- پردازش پرداخت مستقیم و شارژ کیف پول -----
    elif data.startswith("directpay_"):
        _, plan_key, final_price = data.split("_")
        text = (f"💵 <b>پرداخت مستقیم (کارت به کارت)</b>\n\nمبلغ واریزی: <b>{int(final_price):,} تومان</b>\n\n"
                f"💳 شماره کارت:\n<code>{CARD_NUMBER}</code>\n👤 به نام: {ACCOUNT_NAME}\n\n"
                f"📥 <b>لطفاً عکس رسید پرداخت رو همینجا ارسال کن:</b>")
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 انصراف و بازگشت", callback_data="store"))
        msg = bot.edit_message_text(text, user_id, msg_id, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, receive_direct_receipt, plan_key, int(final_price))

    elif data.startswith("walletpay_"):
        _, plan_key, final_price = data.split("_")
        final_price = int(final_price)
        info = PLANS[plan_key]
        
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = cursor.fetchone()[0]
        
        if balance >= final_price:
            cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (final_price, user_id))
            cursor.execute("INSERT INTO orders (user_id, plan_name) VALUES (?, ?)", (user_id, info["name"]))
            order_id = cursor.lastrowid
            conn.commit()
            
            # اطلاع رسانی به ادمین جهت دریافت کانفیگ
            bot.send_message(ADMIN_GROUP_ID, f"🛒 <b>خرید با کیف پول (منتظر کانفیگ)</b>\n\n👤 آیدی: <code>{user_id}</code>\n📦 پلن: {info['name']}\n💵 کسر شده: {final_price:,} تومان\n🆔 شماره سفارش: <code>{order_id}</code>\n\n🔴 <b>ادمین: برای ارسال خودکار، لطفا کانفیگ رو روی همین پیام ریپلای کن.</b>", parse_mode="HTML")
            bot.edit_message_text(f"✅ <b>خرید از کیف پول موفق بود!</b> مبلغ کسر شد.\nسفارش شما به دست ادمین رسید و به زودی کانفیگ ارسال میشه.", user_id, msg_id, parse_mode="HTML", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")))
        else:
            bot.answer_callback_query(call.id, "❌ موجودی کیف پول کافی نیست! اول شارژ کن.", show_alert=True)

    elif data == "charge_req":
        text = "💳 <b>درخواست شارژ حساب</b>\n\n💰 لطفاً مبلغ مورد نظرت رو دقیقاً به تومان (فقط عدد) تایپ کن و بفرست:\nمثال: 175000"
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 انصراف و بازگشت", callback_data="wallet"))
        msg = bot.edit_message_text(text, user_id, msg_id, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, get_charge_amount)

    # ----- دکمه‌های شیشه‌ای تایید و رد برای گروه ادمین -----
    elif data.startswith("admin_approve_charge_"):
        _, target_id, amount = data.split("_", 3)[1:] # extract target_id and amount
        target_id, amount = int(target_id), int(amount)
        
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
        bot.edit_message_caption(f"✅ <b>این رسید توسط ادمین تایید شد و کیف پول کاربر {amount:,} تومان شارژ گردید.</b>", call.message.chat.id, msg_id, parse_mode="HTML")
        bot.send_message(target_id, f"🎉 <b>کیف پول شما شارژ شد!</b>\nمبلغ {amount:,} تومان به حساب شما اضافه شد.", parse_mode="HTML")

    elif data == "admin_reject_charge":
        bot.edit_message_caption("❌ <b>رسید توسط ادمین نامعتبر تشخیص داده شد و رد شد.</b>", call.message.chat.id, msg_id, parse_mode="HTML")

    conn.close()
    try: bot.answer_callback_query(call.id)
    except: pass

# --- مراحل دریافت ورودی از کاربر ---
def get_charge_amount(message):
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "❌ خطا: لطفاً مبلغ را فقط به صورت عدد بفرستید:")
        bot.register_next_step_handler(msg, get_charge_amount)
        return
        
    amount = int(message.text)
    text = (f"💵 <b>مبلغ درخواست شارژ: {amount:,} تومان</b>\n\n💳 شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
            f"👤 به نام: {ACCOUNT_NAME}\n\n📥 <b>لطفاً عکس رسید پرداخت رو اینجا بفرست:</b>")
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 انصراف", callback_data="wallet"))
    msg = bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(msg, receive_charge_receipt, amount)

def receive_charge_receipt(message, amount):
    if message.content_type == 'photo':
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ تایید و شارژ خودکار", callback_data=f"admin_approve_charge_{message.chat.id}_{amount}"))
        markup.add(InlineKeyboardButton("❌ رد کردن رسید", callback_data="admin_reject_charge"))
        
        bot.send_photo(ADMIN_GROUP_ID, message.photo[-1].file_id, caption=f"💰 <b>درخواست شارژ کیف پول</b>\n\n👤 آیدی: <code>{message.chat.id}</code>\n💵 مبلغ واریزی اعلامی: <b>{amount:,} تومان</b>", parse_mode="HTML", reply_markup=markup)
        bot.send_message(message.chat.id, "✅ رسید شما دریافت شد و به محض تایید ادمین، حسابتون شارژ میشه.")
    else:
        msg = bot.send_message(message.chat.id, "❌ فقط عکس رسید قابل قبول است. مجددا عکس بفرستید:")
        bot.register_next_step_handler(msg, receive_charge_receipt, amount)

def receive_direct_receipt(message, plan_key, price):
    if message.content_type == 'photo':
        info = PLANS[plan_key]
        bot.send_photo(ADMIN_GROUP_ID, message.photo[-1].file_id, caption=f"💳 <b>خرید مستقیم (منتظر کانفیگ)</b>\n\n👤 آیدی: <code>{message.chat.id}</code>\n📦 پلن: {info['name']}\n💵 مبلغ اعلامی: {price:,} تومان\n\n🔴 <b>ادمین: در صورت صحت رسید، کانفیگ رو روی همین عکس ریپلای کن تا مستقیم ارسال بشه.</b>", parse_mode="HTML")
        bot.send_message(message.chat.id, "✅ رسید و سفارش شما ثبت شد! پس از رویت توسط علیرضا، کانفیگ همینجا براتون ارسال میشه.")
    else:
        msg = bot.send_message(message.chat.id, "❌ فقط عکس رسید قابل قبول است. لطفا عکس را بفرستید:")
        bot.register_next_step_handler(msg, receive_direct_receipt, plan_key, price)

# --- تابع پردازش پورسانت معرف و اهدای جایزه ---
def process_referral_rewards(user_id, purchase_amount):
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if not res or not res[0]:
        conn.close()
        return
        
    ref = res[0]
    # واریز 7 درصد پورسانت
    reward = int(purchase_amount * 0.07)
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, ref))
    
    # شمارش افراد منحصر به فردی که خرید کرده اند
    cursor.execute("SELECT COUNT(DISTINCT orders.user_id) FROM users JOIN orders ON users.user_id = orders.user_id WHERE users.referred_by = ?", (ref,))
    distinct_buyers = cursor.fetchone()[0]
    
    cursor.execute("SELECT gifts_claimed FROM users WHERE user_id = ?", (ref,))
    gifts_claimed = cursor.fetchone()[0]
    
    # اگر تعداد خریداران به ضریب 10 جدیدی رسیده باشد
    if distinct_buyers // 10 > gifts_claimed:
        new_gift_count = distinct_buyers // 10
        cursor.execute("UPDATE users SET gifts_claimed = ? WHERE user_id = ?", (new_gift_count, ref))
        bot.send_message(ADMIN_GROUP_ID, f"🎁🏆 <b>کاربر برنده جایزه دعوت شد!</b>\n\n👤 کاربر آیدی: <code>{ref}</code> موفق شد <b>{new_gift_count * 10} نفر خریدار واقعی</b> دعوت کنه!\n🔴 لطفاً روی همین پیام <u>کانفیگ هدیه ۵ گیگابایتی</u> رو ریپلای کنید تا خودکار براش با متن تشکر ارسال بشه.", parse_mode="HTML")

    conn.commit()
    conn.close()
    
    try: bot.send_message(ref, f"🎉 یکی از دعوت‌شدگان شما خرید انجام داد و مبلغ <b>{reward:,} تومان</b> سود خالص به کیف پول شما واریز شد!", parse_mode="HTML")
    except: pass

# --- هندلر جامع ریپلای‌های ادمین در گروه (فقط برای کانفیگ) ---
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_GROUP_ID and m.reply_to_message is not None)
def handle_admin_replies(message):
    orig_caption = message.reply_to_message.caption or ""
    orig_text = message.reply_to_message.text or ""
    admin_text = message.text
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()

    # حالت اول: ارسال کانفیگ خرید مستقیم کارت به کارت
    if "خرید مستقیم (منتظر کانفیگ)" in orig_caption:
        target_user = int(orig_caption.split('<code>')[1].split('</code>')[0])
        plan_name = orig_caption.split('📦 پلن: ')[1].split('\n')[0]
        paid_amount = int(orig_caption.split('💵 مبلغ اعلامی: ')[1].split(' تومان')[0].replace(',', ''))
        
        cursor.execute("INSERT INTO orders (user_id, plan_name, config_data) VALUES (?, ?, ?)", (target_user, plan_name, admin_text))
        conn.commit()
        process_referral_rewards(target_user, paid_amount) # پرداخت پورسانت معرف
        
        bot.send_message(target_user, f"🚀 <b>کانفیگ شما با موفقیت صادر شد!</b>\n\n📦 پلن: {plan_name}\n\n<code>{admin_text}</code>\n\nتوی منوی (حساب کاربری) هم ذخیره شد.", parse_mode="HTML")
        bot.reply_to(message, "✅ کانفیگ مستقیم دلیور و پورسانت معرف در صورت وجود اعمال شد.")

    # حالت دوم: ارسال کانفیگ خرید با کیف پول
    elif "خرید با کیف پول (منتظر کانفیگ)" in orig_text:
        target_user = int(orig_text.split('<code>')[1].split('</code>')[0])
        order_id = int(orig_text.split('شناسه سفارش: <code>')[1].split('</code>')[0]) if 'شناسه سفارش:' in orig_text else int(orig_text.split('شماره سفارش: <code>')[1].split('</code>')[0])
        paid_amount = int(orig_text.split('💵 کسر شده: ')[1].split(' تومان')[0].replace(',', ''))
        
        cursor.execute("UPDATE orders SET config_data = ? WHERE order_id = ?", (admin_text, order_id))
        conn.commit()
        process_referral_rewards(target_user, paid_amount) # پرداخت پورسانت معرف

        bot.send_message(target_user, f"🚀 <b>سفارش کیف پول شما آماده شد!</b>\n\n<code>{admin_text}</code>", parse_mode="HTML")
        bot.reply_to(message, "✅ کانفیگ برای خرید کیف پول دلیور شد.")

    # حالت سوم: تحویل جایزه ۱۰ دعوت
    elif "🎁🏆 کاربر برنده جایزه دعوت شد!" in orig_text:
        target_user = int(orig_text.split('<code>')[1].split('</code>')[0])
        
        thanks_msg = (f"❤️ <b>هدیه ویژه علیرضا تقدیم به تو رفیق با معرفت!</b> 🥰\n\n"
                      f"دمت گرم که ربات ما رو به دوستات معرفی کردی و باعث شدی خانواده‌مون بزرگتر بشه.\n"
                      f"این کانفیگ هدیه ۵ گیگابایتی ناقابل، به پاس قدردانی از حمایت‌های بی‌دریغ شماست:\n\n"
                      f"<code>{admin_text}</code>\n\nامیدوارم از سرعتش لذت ببری! 😉✨")
        bot.send_message(target_user, thanks_msg, parse_mode="HTML")
        bot.reply_to(message, "✅ هدیه با پیام تشکر گرم برای معرف ارسال شد.")

    conn.close()

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=7860)).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
