from flask import Flask
from threading import Thread
import telebot
from telebot import types
import requests
import random
import string
import re
import database as db

# =================== تنظیمات ===================
BOT_TOKEN = "8773215261:AAF67pQ9AHZrzvMOZlNbsnaG2-uoTo3HHyk"
ADMIN_ID = 7374971382
ADMIN_USERNAME = "AIireza_1383"
GROUP_ID = -1004294169429
CARD_NUMBER = "5892101542283284"
CARD_OWNER = "علیرضا وحدانی اصل"
REFERRAL_INVITEE_DISCOUNT = 5
REFERRAL_REFERRER_DISCOUNT = 7
REFERRAL_REWARD_EVERY = 10
REFERRAL_REWARD_GB = 5

# =================== پاسارگاد ===================
PASARGUARD_URL = "https://panel.foodchains.com.tr"
PASARGUARD_USER = "moein"
PASARGUARD_PASS = "P6blW82Wv161!"
# ================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_states = {}
group_msg_to_wallet_req = {}
group_msg_to_purchase = {}

PLANS = {
    "plan_10gb": {"name": "۱۰ گیگابایت", "price": 150000, "gb": 10},
    "plan_20gb": {"name": "۲۰ گیگابایت", "price": 300000, "gb": 20},
    "plan_30gb": {"name": "۳۰ گیگابایت", "price": 400000, "gb": 30},
    "plan_40gb": {"name": "۴۰ گیگابایت", "price": 520000, "gb": 40},
}

def price_fmt(p):
    return f"{p:,}".replace(",", "،") + " تومان"

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web():
    app.run(host='0.0.0.0', port=7860)


# ══════════════════════════════════════════════
# API پاسارگاد
# ══════════════════════════════════════════════
_pg_token = None

def pg_login():
    """لاگین به پاسارگاد و گرفتن توکن"""
    global _pg_token
    try:
        resp = requests.post(
            f"{PASARGUARD_URL}/api/admin/token",
            data={"username": PASARGUARD_USER, "password": PASARGUARD_PASS},
            timeout=10
        )
        if resp.status_code == 200:
            _pg_token = resp.json().get("access_token")
            return _pg_token
    except Exception as e:
        print(f"[PG Login Error] {e}")
    return None

def pg_headers():
    """هدر با توکن"""
    if not _pg_token:
        pg_login()
    return {"Authorization": f"Bearer {_pg_token}"}

def pg_create_user(username, data_limit_gb):
    """ساخت کاربر جدید در پاسارگاد"""
    if not _pg_token:
        pg_login()

    data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024

    payload = {
        "username": username,
        "proxies": {},
        "inbounds": {},
        "expire": None,
        "data_limit": data_limit_bytes,
        "data_limit_reset_strategy": "no_reset",
        "status": "active",
        "note": f"Created by bot - {data_limit_gb}GB plan"
    }

    try:
        resp = requests.post(
            f"{PASARGUARD_URL}/api/user",
            json=payload,
            headers=pg_headers(),
            timeout=10
        )

        if resp.status_code == 401:
            pg_login()
            resp = requests.post(
                f"{PASARGUARD_URL}/api/user",
                json=payload,
                headers=pg_headers(),
                timeout=10
            )

        if resp.status_code in (200, 201):
            return resp.json()
        else:
            print(f"[PG Create User Error] {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        print(f"[PG Create User Exception] {e}")
        return None

def pg_get_subscription_link(username):
    """گرفتن لینک سابسکریپشن کاربر"""
    try:
        resp = requests.get(
            f"{PASARGUARD_URL}/api/user/{username}",
            headers=pg_headers(),
            timeout=10
        )
        if resp.status_code == 200:
            user_data = resp.json()
            sub_url = user_data.get("subscription_url")
            if sub_url:
                if sub_url.startswith("/"):
                    sub_url = PASARGUARD_URL + sub_url
                return sub_url
    except Exception as e:
        print(f"[PG Get Sub Error] {e}")
    return None


# ─── منوی اصلی ───
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 خرید سرویس"),
        types.KeyboardButton("👛 کیف پول"),
        types.KeyboardButton("👤 حساب کاربری"),
        types.KeyboardButton("👨‍💻 پشتیبانی"),
    )
    return markup

def gen_referral_code(uid):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

def ensure_user(message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user:
        code = gen_referral_code(uid)
        db.create_user(uid, message.from_user.first_name, message.from_user.username, code)
        user = db.get_user(uid)
    return user


# ══════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.chat.type != 'private':
        return

    uid = message.from_user.id
    user_states.pop(uid, None)

    args = message.text.split()
    referred_by = None
    if len(args) > 1:
        ref_code = args[1]
        referrer = db.get_user_by_referral(ref_code)
        if referrer and referrer['uid'] != uid:
            referred_by = referrer['uid']

    existing = db.get_user(uid)
    if not existing:
        code = gen_referral_code(uid)
        db.create_user(uid, message.from_user.first_name, message.from_user.username, code, referred_by)

    user = db.get_user(uid)
    ref_link = f"https://t.me/{bot.get_me().username}?start={user['referral_code']}"

    welcome = (
        f"🎉 <b>سلام {message.from_user.first_name} عزیز، خوش اومدی!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌐 <b>VPN حرفه‌ای | سرعت بالا | بدون محدودیت</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 <b>پلن‌های نامحدود با قیمت باورنکردنی!</b>\n"
        "✅ کاربر نامحدود | ✅ مدت نامحدود\n"
        "✅ سازگار با V2Ray، V2Box، NPVtunnel، HIDDEFY\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 لینک دعوت اختصاصی تو:\n<code>{ref_link}</code>\n\n"
        f"👥 هر دوستی که با لینک تو بیاد و خرید کنه:\n"
        f" ➡️ <b>دوستت {REFERRAL_INVITEE_DISCOUNT}٪ تخفیف</b> روی اولین خریدش می‌گیره\n"
        f" ➡️ <b>تو {REFERRAL_REFERRER_DISCOUNT}٪ تخفیف</b> روی خرید بعدیت می‌گیری\n\n"
        f"🏆 <b>هر {REFERRAL_REWARD_EVERY} نفر = {REFERRAL_REWARD_GB} گیگابایت رایگان!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 از منو زیر شروع کن:"
    )
    bot.send_message(message.chat.id, welcome, parse_mode="HTML", reply_markup=main_menu())


# ══════════════════════════════════════════════
# هندلر پیام‌های پرایوت
# ══════════════════════════════════════════════
@bot.message_handler(
    func=lambda m: m.chat.type == 'private',
    content_types=['text', 'photo', 'document', 'sticker', 'voice', 'video', 'audio']
)
def handle_private(message):
    uid = message.from_user.id
    state = user_states.get(uid, {}).get('state', '')
    ensure_user(message)

    if message.content_type == 'text':
        txt = message.text.strip()

        if txt == "🛒 خرید سرویس":
            user_states.pop(uid, None)
            show_plans(message.chat.id, uid)
            return

        if txt == "👛 کیف پول":
            user_states.pop(uid, None)
            show_wallet(message.chat.id, uid)
            return

        if txt == "👤 حساب کاربری":
            user_states.pop(uid, None)
            show_account(message.chat.id, uid)
            return

        if txt == "👨‍💻 پشتیبانی":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💬 ارتباط با پشتیبانی", url=f"https://t.me/{ADMIN_USERNAME}"))
            bot.send_message(message.chat.id,
                "👨‍💻 <b>پشتیبانی</b>\n\nبرای سوال یا پیگیری سفارش روی دکمه زیر بزنید:", parse_mode="HTML", reply_markup=markup)
            return

        if state == 'waiting_config_name':
            handle_config_name(message, uid)
            return

        if state == 'waiting_wallet_amount':
            handle_wallet_amount(message, uid)
            return

        if state in ('waiting_receipt', 'waiting_wallet_receipt'):
            bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> پرداخت را ارسال کنید.", parse_mode="HTML")
            return

        bot.send_message(uid, "برای شروع /start بزنید یا از منوی پایین استفاده کنید.", reply_markup=main_menu())
        return

    if message.content_type == 'photo':
        if state == 'waiting_receipt':
            handle_purchase_receipt(message, uid)
        elif state == 'waiting_wallet_receipt':
            handle_wallet_receipt(message, uid)
        else:
            bot.send_message(uid, "❌ ابتدا یک پلن انتخاب کنید.", reply_markup=main_menu())
        return

    if state in ('waiting_receipt', 'waiting_wallet_receipt'):
        bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> پرداخت را ارسال کنید.", parse_mode="HTML")


# ══════════════════════════════════════════════
# خرید سرویس
# ══════════════════════════════════════════════
def show_plans(chat_id, uid):
    user = db.get_user(uid)
    has_referrer = user['referred_by'] is not None if user else False

    markup = types.InlineKeyboardMarkup()
    for key, plan in PLANS.items():
        price = plan['price']
        if has_referrer:
            disc_price = int(price * (1 - REFERRAL_INVITEE_DISCOUNT / 100))
            label = f"📦 {plan['name']} ─ {price_fmt(disc_price)} 🎁{REFERRAL_INVITEE_DISCOUNT}٪"
        else:
            label = f"📦 {plan['name']} ─ {price_fmt(price)}"
        markup.add(types.InlineKeyboardButton(text=label, callback_data=f"plan_{key.split('_', 1)[1]}"))

    markup.add(types.InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_main"))

    note = f"\n🎁 <b>شما {REFERRAL_INVITEE_DISCOUNT}٪ تخفیف دعوت‌شده دارید!</b>" if has_referrer else ""
    text = (
        "💎 <b>پلن‌های موجود:</b>\n\n"
        "✅ تعداد کاربر: <b>نامحدود</b>\n"
        "✅ مدت زمان: <b>نامحدود</b>\n\n"
        "🚀 <b>سازگار با:</b> V2RAY | V2BOX | NPVtunnel | HIDDEFY\n"
        f"{note}\n\n"
        "👇 پلن مورد نظر خود را انتخاب کنید:"
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
def cb_plan(call):
    uid = call.from_user.id
    plan_key = "plan_" + call.data[5:]
    plan = PLANS.get(plan_key)
    if not plan:
        bot.answer_callback_query(call.id, "❌ پلن یافت نشد!")
        return

    user = db.get_user(uid)
    discount = REFERRAL_INVITEE_DISCOUNT if (user and user['referred_by']) else 0
    final_price = int(plan['price'] * (1 - discount / 100))

    user_states[uid] = {
        'state': 'waiting_config_name',
        'plan_key': plan_key,
        'discount': discount,
        'final_price': final_price,
    }

    bot.answer_callback_query(call.id, f"✅ {plan['name']} انتخاب شد")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 بازگشت به پلن‌ها", callback_data="back_plans"))
    
    text = (
        f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
        "📝 لطفاً یک <b>نام انگلیسی</b> برای کانفیگ خود وارد کنید:\n"
        "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)


def handle_config_name(message, uid):
    name = message.text.strip()
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
        bot.send_message(uid,
            "❌ نام باید فقط از <b>حروف انگلیسی</b> باشد (بدون فاصله).\n"
            "مثال: <code>Alireza</code>\n\nدوباره وارد کنید:",
            parse_mode="HTML")
        return

    st = user_states[uid]
    st['config_name'] = name
    plan = PLANS[st['plan_key']]
    final_price = st['final_price']
    user = db.get_user(uid)
    wallet = user['wallet'] if user else 0

    markup = types.InlineKeyboardMarkup()
    if wallet > 0:
        wallet_label = f"💰 کیف پول ({price_fmt(wallet)})"
        if wallet >= final_price:
            wallet_label += " ✅"
        else:
            wallet_label += f" — کمبود {price_fmt(final_price - wallet)}"
        markup.add(types.InlineKeyboardButton(wallet_label, callback_data="pay_wallet"))
        
    markup.add(types.InlineKeyboardButton("💳 پرداخت کارت به کارت", callback_data="pay_card"))
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_plans"))

    disc_txt = f"\n🎁 تخفیف دعوت: <b>{st['discount']}٪</b>" if st['discount'] else ""
    text = (
        "╔══════════════════════╗\n"
        " 🛒 <b>خلاصه سفارش شما</b>\n"
        "╚══════════════════════╝\n\n"
        f"📦 پلن: <b>{plan['name']}</b>\n"
        f"💰 قیمت اصلی: <b>{price_fmt(plan['price'])}</b>{disc_txt}\n"
        f"✅ مبلغ نهایی: <b>{price_fmt(final_price)}</b>\n"
        f"🏷️ نام کانفیگ: <code>{name}</code>\n"
        f"👛 موجودی کیف پول: <b>{price_fmt(wallet)}</b>\n\n"
        "👇 روش پرداخت را انتخاب کنید:"
    )
    bot.send_message(uid, text, parse_mode="HTML", reply_markup=markup)
    st['state'] = 'choosing_payment'


@bot.callback_query_handler(func=lambda c: c.data == "pay_wallet")
def cb_pay_wallet(call):
    uid = call.from_user.id
    st = user_states.get(uid, {})
    if not st:
        bot.answer_callback_query(call.id, "❌ خطا، دوباره شروع کنید.")
        return

    plan = PLANS[st['plan_key']]
    final_price = st['final_price']
    user = db.get_user(uid)

    if not user or user['wallet'] < final_price:
        bot.answer_callback_query(call.id, "❌ موجودی کافی نیست! لطفاً کیف پول را شارژ کنید.")
        return

    db.deduct_wallet(uid, final_price)
    bot.answer_callback_query(call.id, "✅ پرداخت موفق! در حال ساخت کانفیگ...")

    bot.edit_message_text(
        "✅ <b>پرداخت موفق!</b>\n\n⏳ در حال ساخت کانفیگ اتوماتیک...",
        call.message.chat.id, call.message.message_id, parse_mode="HTML"
    )

    _create_and_send_config(uid, call.from_user.first_name, call.from_user.username,
                            st, plan, final_price, wallet_paid=True)


def _create_and_send_config(uid, first_name, username, st, plan, final_price, wallet_paid=False):
    """ساخت کانفیگ در پاسارگاد و ارسال به کاربر"""
    config_name = st['config_name']
    pg_username = f"{config_name}_{uid}"

    pg_user = pg_create_user(pg_username, plan['gb'])

    if pg_user:
        sub_link = pg_get_subscription_link(pg_username)
        if sub_link:
            purchase_id = db.save_purchase(
                uid, st['plan_key'], plan['name'], final_price,
                config_name, wallet_paid, st['discount'], None
            )
            db.save_config_to_purchase(purchase_id, sub_link)
            st['state'] = 'done'

            bot.send_message(uid,
                "🎉 <b>کانفیگ شما آماده است!</b>\n\n"
                f"📦 پلن: <b>{plan['name']}</b>\n"
                f"🏷️ نام: <code>{config_name}</code>\n\n"
                "🔗 <b>لینک سابسکریپشن:</b>\n"
                f"<code>{sub_link}</code>\n\n"
                "✅ این لینک را در V2Ray / V2Box / NPVtunnel وارد کنید.\n"
                "🙏 ممنون از خرید شما!",
                parse_mode="HTML", reply_markup=main_menu()
            )

            uname = f"@{username}" if username else f"آیدی: {uid}"
            bot.send_message(GROUP_ID,
                f"✅ <b>خرید اتوماتیک انجام شد!</b>\n\n"
                f"👤 {first_name} | {uname}\n"
                f"🔢 آیدی: <code>{uid}</code>\n"
                f"📦 پلن: {plan['name']} — {price_fmt(final_price)}\n"
                f"🏷️ نام: <code>{config_name}</code>\n"
                f"💰 روش: {'کیف پول' if wallet_paid else 'کارت به کارت'}\n\n"
                f"🔗 لینک: <code>{sub_link}</code>",
                parse_mode="HTML"
            )
            check_referral_reward(uid, plan['name'], config_name)
            return

    st['state'] = 'done'
    uname = f"@{username}" if username else "ندارد"
    bot.send_message(uid,
        "✅ <b>پرداخت ثبت شد!</b>\n\n"
        "⏳ کانفیگ به زودی توسط ادمین ارسال می‌شود.\n"
        "🙏 ممنون از خرید شما!",
        parse_mode="HTML", reply_markup=main_menu()
    )
    bot.send_message(GROUP_ID,
        f"⚠️ <b>خرید ثبت شد ولی API پاسارگاد خطا داد!</b>\n\n"
        f"👤 {first_name} | {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"📦 پلن: {plan['name']} — {price_fmt(final_price)}\n"
        f"🏷️ نام: <code>{config_name}</code>\n\n"
        "لطفاً دستی کانفیگ بسازید و ریپلای کنید.",
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda c: c.data == "pay_card")
def cb_pay_card(call):
    uid = call.from_user.id
    st = user_states.get(uid, {})
    if not st:
        bot.answer_callback_query(call.id, "❌ خطا، دوباره شروع کنید.")
        return

    st['state'] = 'waiting_receipt'
    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_config_name"))
    
    text = (
        "╔══════════════════════╗\n"
        " 💳 <b>اطلاعات پرداخت</b>\n"
        "╚══════════════════════╝\n\n"
        f"💰 مبلغ: <b>{price_fmt(st['final_price'])}</b>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 پس از واریز، <b>عکس رسید</b> را در همین چت ارسال کنید:"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)


def handle_purchase_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_receipt':
        return

    plan = PLANS[st['plan_key']]
    config_name = st['config_name']
    user_obj = message.from_user
    uname = f"@{user_obj.username}" if user_obj.username else "ندارد"

    caption = (
        "🚨 <b>سفارش جدید — تایید کنید!</b>\n\n"
        f"📦 پلن: <b>{plan['name']} — {price_fmt(st['final_price'])}</b>\n"
        f"🏷️ نام کانفیگ: <code>{config_name}</code>\n"
        f"👤 نام: <b>{user_obj.first_name}</b>\n"
        f"🆔 یوزرنیم: {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"🎁 تخفیف: {st['discount']}٪\n\n"
        "✅ برای تایید و ساخت <b>اتوماتیک</b> کانفیگ، ریپلای کنید: <code>ok</code>"
    )

    try:
        sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        purchase_id = db.save_purchase(
            uid, st['plan_key'], plan['name'], st['final_price'],
            config_name, False, st['discount'], sent.message_id
        )
        group_msg_to_purchase[sent.message_id] = {
            'purchase_id': purchase_id,
            'uid': uid,
            'first_name': user_obj.first_name,
            'username': user_obj.username,
            'st': dict(st),
            'plan': plan,
            'final_price': st['final_price']
        }
        st['state'] = 'done'
        bot.send_message(uid,
            "✅ <b>رسید شما با موفقیت ثبت شد!</b>\n\n"
            "⏳ در حال بررسی توسط ادمین...\n"
            "پس از تایید، کانفیگ <b>اتوماتیک</b> ارسال می‌شود.\n\n"
            "🙏 ممنون از خرید شما!",
            parse_mode="HTML", reply_markup=main_menu())
    except Exception as e:
        print(f"[ERROR receipt] {e}")
        bot.send_message(uid, "⚠️ خطا در ثبت سفارش. لطفاً دوباره رسید را ارسال کنید.")


def check_referral_reward(buyer_uid, plan_name, config_name):
    user = db.get_user(buyer_uid)
    if not user or not user['referred_by']:
        return

    referrer_uid = user['referred_by']
    result = db.increment_referral_count(referrer_uid)
    if not result:
        return

    referral_count = result['referral_count']
    rewarded_sets = result['rewarded_sets']

    try:
        bot.send_message(referrer_uid,
            f"🎉 <b>یک نفر با لینک دعوت شما خرید کرد!</b>\n\n"
            f"👥 تعداد دعوت‌های موفق شما: <b>{referral_count}</b>\n"
            f"🎁 {REFERRAL_REWARD_EVERY - (referral_count % REFERRAL_REWARD_EVERY)} نفر دیگر تا جایزه!",
            parse_mode="HTML")
    except:
        pass

    if referral_count > 0 and referral_count % REFERRAL_REWARD_EVERY == 0:
        current_set = referral_count // REFERRAL_REWARD_EVERY
        if current_set > rewarded_sets:
            db.mark_rewarded_set(referrer_uid)
            referrer = db.get_user(referrer_uid)
            uname = f"@{referrer['username']}" if referrer and referrer['username'] else f"آیدی: {referrer_uid}"
            try:
                bot.send_message(GROUP_ID,
                    f"🏆 <b>کاربر برنده جایزه شد!</b>\n\n"
                    f"👤 {uname} | آیدی: <code>{referrer_uid}</code>\n"
                    f"👥 دعوت موفق: <b>{referral_count}</b>\n"
                    f"🎁 جایزه: <b>{REFERRAL_REWARD_GB} گیگابایت رایگان</b>",
                    parse_mode="HTML")
            except:
                pass
            try:
                bot.send_message(referrer_uid,
                    f"🏆🎉 <b>تبریک! {REFERRAL_REWARD_GB} گیگابایت رایگان بردید!</b>\n\n"
                    "⏳ ادمین به زودی کانفیگ جایزه ارسال می‌کند. ❤️",
                    parse_mode="HTML")
            except:
                pass


# ══════════════════════════════════════════════
# کیف پول
# ══════════════════════════════════════════════
def show_wallet(chat_id, uid):
    user = db.get_user(uid)
    wallet_bal = user['wallet'] if user else 0
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("💰 موجودی", callback_data="wallet_balance"),
        types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge")
    )
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
    
    bot.send_message(chat_id,
        f"👛 <b>کیف پول شما</b>\n\n💰 موجودی: <b>{price_fmt(wallet_bal)}</b>\n\nیک گزینه را انتخاب کنید:",
        reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data == "wallet_balance")
def cb_wallet_balance(call):
    uid = call.from_user.id
    user = db.get_user(uid)
    wallet_bal = user['wallet'] if user else 0
    bot.answer_callback_query(call.id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge"))
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_wallet"))
    
    bot.edit_message_text(f"💰 <b>موجودی کیف پول:</b>\n\n<b>{price_fmt(wallet_bal)}</b>", 
                          call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data == "wallet_charge")
def cb_wallet_charge(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_states[uid] = {'state': 'waiting_wallet_amount'}
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_wallet"))
    
    text = (
        "➕ <b>شارژ کیف پول</b>\n\n"
        "💬 مبلغ شارژ را <b>به تومان</b> وارد کن:\nمثال: <code>100000</code>"
    )
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)


def handle_wallet_amount(message, uid):
    txt = message.text.strip().replace(",", "").replace("،", "")
    if not txt.isdigit() or int(txt) < 10000:
        bot.send_message(uid, "❌ مبلغ نامعتبر. حداقل <b>۱۰,۰۰۰ تومان</b>:", parse_mode="HTML")
        return

    amount = int(txt)
    user_states[uid]['amount'] = amount
    user_states[uid]['state'] = 'waiting_wallet_receipt'

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_wallet"))
    
    text = (
        "╔══════════════════════╗\n 💳 <b>اطلاعات پرداخت</b>\n╚══════════════════════╝\n\n"
        f"💰 مبلغ شارژ: <b>{price_fmt(amount)}</b>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "📸 پس از واریز، <b>عکس رسید</b> را ارسال کنید:"
    )
    bot.send_message(uid, text, parse_mode="HTML", reply_markup=markup)


def handle_wallet_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_wallet_receipt':
        return

    amount = st['amount']
    user_obj = message.from_user
    uname = f"@{user_obj.username}" if user_obj.username else "ندارد"

    caption = (
        "💳 <b>درخواست شارژ کیف پول</b>\n\n"
        f"👤 {user_obj.first_name} | {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"💰 مبلغ: <b>{price_fmt(amount)}</b>\n\n"
        f"✅ برای تایید، ریپلای کنید: <code>{amount}</code>"
    )

    try:
        sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        req_id = db.save_wallet_request(uid, amount)
        db.set_wallet_request_msg(req_id, sent.message_id)
        group_msg_to_wallet_req[sent.message_id] = req_id
        st['state'] = 'done'
        bot.send_message(uid,
            "✅ <b>رسید شارژ ثبت شد!</b>\n\n⏳ پس از تایید ادمین، موجودی اضافه می‌شود.",
            parse_mode="HTML", reply_markup=main_menu())
    except Exception as e:
        print(f"[ERROR wallet receipt] {e}")
        bot.send_message(uid, "⚠️ خطا در ثبت. دوباره رسید را ارسال کنید.")


# ══════════════════════════════════════════════
# حساب کاربری
# ══════════════════════════════════════════════
def show_account(chat_id, uid):
    user = db.get_user(uid)
    purchases = db.get_purchases_by_user(uid) or []
    wallet_bal = user['wallet'] if user else 0
    ref_count = user['referral_count'] if user else 0
    ref_code = user['referral_code'] if user else ""
    ref_link = f"https://t.me/{bot.get_me().username}?start={ref_code}"

    markup = types.InlineKeyboardMarkup()
    for p in purchases:
        markup.add(types.InlineKeyboardButton(f"📦 {p['config_name']} — {p['plan_name']}", callback_data=f"reconfig_{p['id']}"))
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))

    text = (
        "👤 <b>حساب کاربری</b>\n\n"
        f"👥 دعوت موفق: <b>{ref_count}</b>\n"
        f"🛒 تعداد خرید: <b>{len(purchases)}</b>\n"
        f"👛 موجودی: <b>{price_fmt(wallet_bal)}</b>\n\n"
        f"🔗 لینک دعوت:\n<code>{ref_link}</code>\n\n"
        "📋 <b>کانفیگ‌های خریداری‌شده:</b>"
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("reconfig_"))
def cb_reconfig(call):
    purchase_id = int(call.data.split("_")[1])
    purchase = db.get_purchase_by_id(purchase_id)
    uid = call.from_user.id

    if not purchase or purchase['uid'] != uid:
        bot.answer_callback_query(call.id, "❌ کانفیگ یافت نشد!")
        return

    if not purchase['config_data']:
        bot.answer_callback_query(call.id, "⏳ کانفیگ هنوز آماده نشده!")
        return

    bot.answer_callback_query(call.id, "✅ ارسال شد")
    bot.send_message(uid,
        f"✅ <b>کانفیگ شما:</b>\n\n"
        f"📦 پلن: {purchase['plan_name']}\n"
        f"🏷️ نام: {purchase['config_name']}\n\n"
        f"🔗 لینک سابسکریپشن:\n<code>{purchase['config_data']}</code>",
        parse_mode="HTML")


# ══════════════════════════════════════════════
# دکمه‌های بازگشت
# ══════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("back_"))
def cb_back(call):
    uid = call.from_user.id
    dest = call.data[5:]
    bot.answer_callback_query(call.id)

    if dest == "main":
        user_states.pop(uid, None)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🏠 منوی اصلی:", reply_markup=main_menu())

    elif dest == "plans":
        user_states.pop(uid, None)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_plans(call.message.chat.id, uid)

    elif dest == "wallet":
        user_states.pop(uid, None)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_wallet(call.message.chat.id, uid)

    elif dest == "config_name":
        st = user_states.get(uid, {})
        if st.get('plan_key'):
            plan = PLANS[st['plan_key']]
            st['state'] = 'waiting_config_name'
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔙 بازگشت به پلن‌ها", callback_data="back_plans"))
            
            text = (
                f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
                "📝 یک <b>نام انگلیسی</b> برای کانفیگ وارد کنید:\n"
                "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>"
            )
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_plans(call.message.chat.id, uid)


# ══════════════════════════════════════════════
# ریپلای ادمین در گروه
# ══════════════════════════════════════════════
@bot.message_handler(
    func=lambda m: m.chat.id == GROUP_ID and m.reply_to_message is not None
)
def handle_group_reply(message):
    replied_id = message.reply_to_message.message_id

    # ── شارژ کیف پول ──
    req = db.get_wallet_request_by_group_msg(replied_id)
    if req is not None:
        txt = message.text.strip() if message.text else ""
        clean = txt.replace(",", "").replace("،", "")
        if not clean.isdigit():
            bot.reply_to(message, "❌ عدد مبلغ را ریپلای کنید.\nمثال: <code>150000</code>", parse_mode="HTML")
            return
        confirmed_amount = int(clean)
        db.add_wallet(req['uid'], confirmed_amount)
        db.confirm_wallet_request(req['id'])
        try:
            bot.send_message(req['uid'],
                f"✅ <b>کیف پول شارژ شد!</b>\n\n"
                f"💰 مبلغ: <b>{price_fmt(confirmed_amount)}</b>\n"
                f"👛 موجودی جدید: <b>{price_fmt(db.get_user(req['uid'])['wallet'])}</b>",
                parse_mode="HTML", reply_markup=main_menu())
            bot.reply_to(message, f"✅ کیف پول کاربر <code>{req['uid']}</code> به مبلغ {price_fmt(confirmed_amount)} شارژ شد.", parse_mode="HTML")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: <code>{e}</code>", parse_mode="HTML")
        return

    # ── تایید خرید و ساخت اتوماتیک کانفیگ ──
    purchase = db.get_purchase_by_group_msg(replied_id)
    if purchase is not None:
        if purchase.get('config_data'):
            bot.reply_to(message, "⚠️ این سفارش قبلاً پردازش شده.")
            return

        txt = message.text.strip().lower() if message.text else ""
        if txt != "ok":
            bot.reply_to(message, "برای تایید بنویسید: <code>ok</code>", parse_mode="HTML")
            return

        bot.reply_to(message, "⏳ در حال ساخت کانفیگ اتوماتیک در پاسارگاد...")

        uid = purchase['uid']
        plan_key = purchase['plan_key']
        plan = PLANS.get(plan_key)
        if not plan:
            bot.reply_to(message, "❌ پلن یافت نشد!")
            return

        st = {
            'plan_key': plan_key,
            'config_name': purchase['config_name'],
            'discount': purchase['discount'],
            'final_price': purchase['price'],
        }

        user_info = db.get_user(uid)
        first_name = user_info['first_name'] if user_info else "کاربر"
        username = user_info['username'] if user_info else None

        _create_and_send_config(uid, first_name, username, st, plan, purchase['price'], wallet_paid=False)
        bot.reply_to(message, "✅ کانفیگ اتوماتیک ساخته و ارسال شد!")
        return


# ══════════════════════════════════════════════
# پیام همگانی (فقط ادمین)
# ══════════════════════════════════════════════
broadcast_state = {}

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.chat.type != 'private':
        bot.reply_to(message, "این دستور فقط در پیوی کار می‌کند.")
        return
    broadcast_state[ADMIN_ID] = True
    bot.send_message(ADMIN_ID,
        "📢 <b>پیام همگانی</b>\n\n"
        "پیام خود را ارسال کنید (متن، عکس، یا ویدیو):\n"
        "برای لغو: /cancel",
        parse_mode="HTML")

@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    if message.from_user.id != ADMIN_ID:
        return
    broadcast_state.pop(ADMIN_ID, None)
    bot.send_message(ADMIN_ID, "❌ عملیات لغو شد.", reply_markup=main_menu())

@bot.message_handler(
    func=lambda m: m.chat.type == 'private' and m.from_user.id == ADMIN_ID and broadcast_state.get(ADMIN_ID),
    content_types=['text', 'photo', 'video']
)
def handle_broadcast_message(message):
    if not broadcast_state.get(ADMIN_ID):
        return

    broadcast_state.pop(ADMIN_ID, None)

    all_users = db.get_all_users()
    success = 0
    fail = 0

    bot.send_message(ADMIN_ID, f"⏳ در حال ارسال به {len(all_users)} کاربر...")

    for user in all_users:
        try:
            if message.content_type == 'text':
                bot.send_message(user['uid'], message.text, parse_mode="HTML")
            elif message.content_type == 'photo':
                caption = message.caption or ""
                bot.send_photo(user['uid'], message.photo[-1].file_id, caption=caption, parse_mode="HTML")
            elif message.content_type == 'video':
                caption = message.caption or ""
                bot.send_video(user['uid'], message.video.file_id, caption=caption, parse_mode="HTML")
            success += 1
        except Exception:
            fail += 1

    bot.send_message(ADMIN_ID,
        f"✅ <b>پیام همگانی ارسال شد!</b>\n\n"
        f"✔️ موفق: <b>{success}</b>\n"
        f"❌ ناموفق: <b>{fail}</b>",
        parse_mode="HTML", reply_markup=main_menu())


# ─── اجرا ───
if __name__ == "__main__":
    db.init_db()
    pg_login()  # لاگین اولیه به پاسارگاد
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🤖 Bot started (polling)...")
    bot.infinity_polling()
                timeout=10
            )

        if resp.status_code in (200, 201):
            return resp.json()
        else:
            print(f"[PG Create User Error] {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        print(f"[PG Create User Exception] {e}")
        return None

def pg_get_subscription_link(username):
    """گرفتن لینک سابسکریپشن کاربر"""
    try:
        resp = requests.get(
            f"{PASARGUARD_URL}/api/user/{username}",
            headers=pg_headers(),
            timeout=10
        )
        if resp.status_code == 200:
            user_data = resp.json()
            sub_url = user_data.get("subscription_url")
            if sub_url:
                if sub_url.startswith("/"):
                    sub_url = PASARGUARD_URL + sub_url
                return sub_url
    except Exception as e:
        print(f"[PG Get Sub Error] {e}")
    return None


# ══════════════════════════════════════════════
# ارسال پیام با دکمه‌های رنگی
# ══════════════════════════════════════════════
def send_colored_message(chat_id, text, reply_markup_json, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": reply_markup_json
    }
    resp = requests.post(url, json=payload)
    data = resp.json()
    if data.get("ok"):
        return data["result"]["message_id"]
    return None

def edit_colored_message(chat_id, message_id, text, reply_markup_json, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode,
        "reply_markup": reply_markup_json
    }
    requests.post(url, json=payload)

def green_btn(text, callback_data):
    return {"text": text, "callback_data": callback_data, "style": "success"}

def red_btn(text, callback_data):
    return {"text": text, "callback_data": callback_data, "style": "danger"}

def url_btn(text, url):
    return {"text": text, "url": url}

def inline_kb(*rows):
    return {"inline_keyboard": list(rows)}


# ─── منوی اصلی ───
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 خرید سرویس"),
        types.KeyboardButton("👛 کیف پول"),
        types.KeyboardButton("👤 حساب کاربری"),
        types.KeyboardButton("👨‍💻 پشتیبانی"),
    )
    return markup

def gen_referral_code(uid):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

def ensure_user(message):
    uid = message.from_user.id
    user = db.get_user(uid)
    if not user:
        code = gen_referral_code(uid)
        db.create_user(uid, message.from_user.first_name, message.from_user.username, code)
        user = db.get_user(uid)
    return user


# ══════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.chat.type != 'private':
        return

    uid = message.from_user.id
    user_states.pop(uid, None)

    args = message.text.split()
    referred_by = None
    if len(args) > 1:
        ref_code = args[1]
        referrer = db.get_user_by_referral(ref_code)
        if referrer and referrer['uid'] != uid:
            referred_by = referrer['uid']

    existing = db.get_user(uid)
    if not existing:
        code = gen_referral_code(uid)
        db.create_user(uid, message.from_user.first_name, message.from_user.username, code, referred_by)

    user = db.get_user(uid)
    ref_link = f"https://t.me/{bot.get_me().username}?start={user['referral_code']}"

    welcome = (
        f"🎉 <b>سلام {message.from_user.first_name} عزیز، خوش اومدی!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌐 <b>VPN حرفه‌ای | سرعت بالا | بدون محدودیت</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔥 <b>پلن‌های نامحدود با قیمت باورنکردنی!</b>\n"
        "✅ کاربر نامحدود | ✅ مدت نامحدود\n"
        "✅ سازگار با V2Ray، V2Box، NPVtunnel، HIDDEFY\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 لینک دعوت اختصاصی تو:\n<code>{ref_link}</code>\n\n"
        f"👥 هر دوستی که با لینک تو بیاد و خرید کنه:\n"
        f" ➡️ <b>دوستت {REFERRAL_INVITEE_DISCOUNT}٪ تخفیف</b> روی اولین خریدش می‌گیره\n"
        f" ➡️ <b>تو {REFERRAL_REFERRER_DISCOUNT}٪ تخفیف</b> روی خرید بعدیت می‌گیری\n\n"
        f"🏆 <b>هر {REFERRAL_REWARD_EVERY} نفر = {REFERRAL_REWARD_GB} گیگابایت رایگان!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 از منو زیر شروع کن:"
    )
    bot.send_message(message.chat.id, welcome, parse_mode="HTML", reply_markup=main_menu())


# ══════════════════════════════════════════════
# هندلر پیام‌های پرایوت
# ══════════════════════════════════════════════
@bot.message_handler(
    func=lambda m: m.chat.type == 'private',
    content_types=['text', 'photo', 'document', 'sticker', 'voice', 'video', 'audio']
)
def handle_private(message):
    uid = message.from_user.id
    state = user_states.get(uid, {}).get('state', '')
    ensure_user(message)

    if message.content_type == 'text':
        txt = message.text.strip()

        if txt == "🛒 خرید سرویس":
            user_states.pop(uid, None)
            show_plans(message.chat.id, uid)
            return

        if txt == "👛 کیف پول":
            user_states.pop(uid, None)
            show_wallet(message.chat.id, uid)
            return

        if txt == "👤 حساب کاربری":
            user_states.pop(uid, None)
            show_account(message.chat.id, uid)
            return

        if txt == "👨‍💻 پشتیبانی":
            kb = inline_kb([url_btn("💬 ارتباط با پشتیبانی", f"https://t.me/{ADMIN_USERNAME}")])
            send_colored_message(message.chat.id,
                "👨‍💻 <b>پشتیبانی</b>\n\nبرای سوال یا پیگیری سفارش روی دکمه زیر بزنید:", kb)
            return

        if state == 'waiting_config_name':
            handle_config_name(message, uid)
            return

        if state == 'waiting_wallet_amount':
            handle_wallet_amount(message, uid)
            return

        if state in ('waiting_receipt', 'waiting_wallet_receipt'):
            bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> پرداخت را ارسال کنید.", parse_mode="HTML")
            return

        bot.send_message(uid, "برای شروع /start بزنید یا از منوی پایین استفاده کنید.", reply_markup=main_menu())
        return

    if message.content_type == 'photo':
        if state == 'waiting_receipt':
            handle_purchase_receipt(message, uid)
        elif state == 'waiting_wallet_receipt':
            handle_wallet_receipt(message, uid)
        else:
            bot.send_message(uid, "❌ ابتدا یک پلن انتخاب کنید.", reply_markup=main_menu())
        return

    if state in ('waiting_receipt', 'waiting_wallet_receipt'):
        bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> پرداخت را ارسال کنید.", parse_mode="HTML")


# ══════════════════════════════════════════════
# خرید سرویس
# ══════════════════════════════════════════════
def show_plans(chat_id, uid):
    user = db.get_user(uid)
    has_referrer = user['referred_by'] is not None

    rows = []
    for key, plan in PLANS.items():
        price = plan['price']
        if has_referrer:
            disc_price = int(price * (1 - REFERRAL_INVITEE_DISCOUNT / 100))
            label = f"📦 {plan['name']} ─ {price_fmt(disc_price)} 🎁{REFERRAL_INVITEE_DISCOUNT}٪"
        else:
            label = f"📦 {plan['name']} ─ {price_fmt(price)}"
        rows.append([green_btn(label, f"plan_{key.split('_',1)[1]}")])

    rows.append([red_btn("🔙 بازگشت", "back_main")])

    note = f"\n🎁 <b>شما {REFERRAL_INVITEE_DISCOUNT}٪ تخفیف دعوت‌شده دارید!</b>" if has_referrer else ""
    send_colored_message(chat_id,
        "💎 <b>پلن‌های موجود:</b>\n\n"
        "✅ تعداد کاربر: <b>نامحدود</b>\n"
        "✅ مدت زمان: <b>نامحدود</b>\n\n"
        "🚀 <b>سازگار با:</b> V2RAY | V2BOX | NPVtunnel | HIDDEFY\n"
        f"{note}\n\n"
        "👇 پلن مورد نظر خود را انتخاب کنید:",
        {"inline_keyboard": rows}
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
def cb_plan(call):
    uid = call.from_user.id
    plan_key = "plan_" + call.data[5:]
    plan = PLANS.get(plan_key)
    if not plan:
        bot.answer_callback_query(call.id, "❌ پلن یافت نشد!")
        return

    user = db.get_user(uid)
    discount = REFERRAL_INVITEE_DISCOUNT if (user and user['referred_by']) else 0
    final_price = int(plan['price'] * (1 - discount / 100))

    user_states[uid] = {
        'state': 'waiting_config_name',
        'plan_key': plan_key,
        'discount': discount,
        'final_price': final_price,
    }

    bot.answer_callback_query(call.id, f"✅ {plan['name']} انتخاب شد")
    kb = inline_kb([red_btn("🔙 بازگشت به پلن‌ها", "back_plans")])
    edit_colored_message(call.message.chat.id, call.message.message_id,
        f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
        "📝 لطفاً یک <b>نام انگلیسی</b> برای کانفیگ خود وارد کنید:\n"
        "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>",
        kb
    )


def handle_config_name(message, uid):
    name = message.text.strip()
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
        bot.send_message(uid,
            "❌ نام باید فقط از <b>حروف انگلیسی</b> باشد (بدون فاصله).\n"
            "مثال: <code>Alireza</code>\n\nدوباره وارد کنید:",
            parse_mode="HTML")
        return

    st = user_states[uid]
    st['config_name'] = name
    plan = PLANS[st['plan_key']]
    final_price = st['final_price']
    user = db.get_user(uid)
    wallet = user['wallet']

    rows = []
    if wallet > 0:
        wallet_label = f"💰 کیف پول ({price_fmt(wallet)})"
        if wallet >= final_price:
            wallet_label += " ✅"
        else:
            wallet_label += f" — کمبود {price_fmt(final_price - wallet)}"
        rows.append([green_btn(wallet_label, "pay_wallet")])
    rows.append([green_btn("💳 پرداخت کارت به کارت", "pay_card")])
    rows.append([red_btn("🔙 بازگشت", "back_plans")])

    disc_txt = f"\n🎁 تخفیف دعوت: <b>{st['discount']}٪</b>" if st['discount'] else ""
    send_colored_message(uid,
        "╔══════════════════════╗\n"
        " 🛒 <b>خلاصه سفارش شما</b>\n"
        "╚══════════════════════╝\n\n"
        f"📦 پلن: <b>{plan['name']}</b>\n"
        f"💰 قیمت اصلی: <b>{price_fmt(plan['price'])}</b>{disc_txt}\n"
        f"✅ مبلغ نهایی: <b>{price_fmt(final_price)}</b>\n"
        f"🏷️ نام کانفیگ: <code>{name}</code>\n"
        f"👛 موجودی کیف پول: <b>{price_fmt(wallet)}</b>\n\n"
        "👇 روش پرداخت را انتخاب کنید:",
        {"inline_keyboard": rows}
    )
    st['state'] = 'choosing_payment'


@bot.callback_query_handler(func=lambda c: c.data == "pay_wallet")
def cb_pay_wallet(call):
    uid = call.from_user.id
    st = user_states.get(uid, {})
    if not st:
        bot.answer_callback_query(call.id, "❌ خطا، دوباره شروع کنید.")
        return

    plan = PLANS[st['plan_key']]
    final_price = st['final_price']
    user = db.get_user(uid)

    if user['wallet'] < final_price:
        bot.answer_callback_query(call.id, "❌ موجودی کافی نیست! لطفاً کیف پول را شارژ کنید.")
        return

    db.deduct_wallet(uid, final_price)
    bot.answer_callback_query(call.id, "✅ پرداخت موفق! در حال ساخت کانفیگ...")

    edit_colored_message(call.message.chat.id, call.message.message_id,
        "✅ <b>پرداخت موفق!</b>\n\n⏳ در حال ساخت کانفیگ اتوماتیک...",
        inline_kb()
    )

    # ساخت اتوماتیک کانفیگ
    _create_and_send_config(uid, call.from_user.first_name, call.from_user.username,
                            st, plan, final_price, wallet_paid=True)


def _create_and_send_config(uid, first_name, username, st, plan, final_price, wallet_paid=False):
    """ساخت کانفیگ در پاسارگاد و ارسال به کاربر"""
    config_name = st['config_name']
    pg_username = f"{config_name}_{uid}"

    pg_user = pg_create_user(pg_username, plan['gb'])

    if pg_user:
        sub_link = pg_get_subscription_link(pg_username)
        if sub_link:
            purchase_id = db.save_purchase(
                uid, st['plan_key'], plan['name'], final_price,
                config_name, wallet_paid, st['discount'], None
            )
            db.save_config_to_purchase(purchase_id, sub_link)
            st['state'] = 'done'

            bot.send_message(uid,
                "🎉 <b>کانفیگ شما آماده است!</b>\n\n"
                f"📦 پلن: <b>{plan['name']}</b>\n"
                f"🏷️ نام: <code>{config_name}</code>\n\n"
                "🔗 <b>لینک سابسکریپشن:</b>\n"
                f"<code>{sub_link}</code>\n\n"
                "✅ این لینک را در V2Ray / V2Box / NPVtunnel وارد کنید.\n"
                "🙏 ممنون از خرید شما!",
                parse_mode="HTML", reply_markup=main_menu()
            )

            uname = f"@{username}" if username else f"آیدی: {uid}"
            bot.send_message(GROUP_ID,
                f"✅ <b>خرید اتوماتیک انجام شد!</b>\n\n"
                f"👤 {first_name} | {uname}\n"
                f"🔢 آیدی: <code>{uid}</code>\n"
                f"📦 پلن: {plan['name']} — {price_fmt(final_price)}\n"
                f"🏷️ نام: <code>{config_name}</code>\n"
                f"💰 روش: {'کیف پول' if wallet_paid else 'کارت به کارت'}\n\n"
                f"🔗 لینک: <code>{sub_link}</code>",
                parse_mode="HTML"
            )
            check_referral_reward(uid, plan['name'], config_name)
            return

    st['state'] = 'done'
    uname = f"@{username}" if username else "ندارد"
    bot.send_message(uid,
        "✅ <b>پرداخت ثبت شد!</b>\n\n"
        "⏳ کانفیگ به زودی توسط ادمین ارسال می‌شود.\n"
        "🙏 ممنون از خرید شما!",
        parse_mode="HTML", reply_markup=main_menu()
    )
    bot.send_message(GROUP_ID,
        f"⚠️ <b>خرید ثبت شد ولی API پاسارگاد خطا داد!</b>\n\n"
        f"👤 {first_name} | {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"📦 پلن: {plan['name']} — {price_fmt(final_price)}\n"
        f"🏷️ نام: <code>{config_name}</code>\n\n"
        "لطفاً دستی کانفیگ بسازید و ریپلای کنید.",
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda c: c.data == "pay_card")
def cb_pay_card(call):
    uid = call.from_user.id
    st = user_states.get(uid, {})
    if not st:
        bot.answer_callback_query(call.id, "❌ خطا، دوباره شروع کنید.")
        return

    st['state'] = 'waiting_receipt'
    bot.answer_callback_query(call.id)

    kb = inline_kb([red_btn("🔙 بازگشت", "back_config_name")])
    edit_colored_message(call.message.chat.id, call.message.message_id,
        "╔══════════════════════╗\n"
        " 💳 <b>اطلاعات پرداخت</b>\n"
        "╚══════════════════════╝\n\n"
        f"💰 مبلغ: <b>{price_fmt(st['final_price'])}</b>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 پس از واریز، <b>عکس رسید</b> را در همین چت ارسال کنید:",
        kb
    )


def handle_purchase_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_receipt':
        return

    plan = PLANS[st['plan_key']]
    config_name = st['config_name']
    user_obj = message.from_user
    uname = f"@{user_obj.username}" if user_obj.username else "ندارد"

    caption = (
        "🚨 <b>سفارش جدید — تایید کنید!</b>\n\n"
        f"📦 پلن: <b>{plan['name']} — {price_fmt(st['final_price'])}</b>\n"
        f"🏷️ نام کانفیگ: <code>{config_name}</code>\n"
        f"👤 نام: <b>{user_obj.first_name}</b>\n"
        f"🆔 یوزرنیم: {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"🎁 تخفیف: {st['discount']}٪\n\n"
        "✅ برای تایید و ساخت <b>اتوماتیک</b> کانفیگ، ریپلای کنید: <code>ok</code>"
    )

    try:
        sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        purchase_id = db.save_purchase(
            uid, st['plan_key'], plan['name'], st['final_price'],
            config_name, False, st['discount'], sent.message_id
        )
        group_msg_to_purchase[sent.message_id] = {
            'purchase_id': purchase_id,
            'uid': uid,
            'first_name': user_obj.first_name,
            'username': user_obj.username,
            'st': dict(st),
            'plan': plan,
            'final_price': st['final_price']
        }
        st['state'] = 'done'
        bot.send_message(uid,
            "✅ <b>رسید شما با موفقیت ثبت شد!</b>\n\n"
            "⏳ در حال بررسی توسط ادمین...\n"
            "پس از تایید، کانفیگ <b>اتوماتیک</b> ارسال می‌شود.\n\n"
            "🙏 ممنون از خرید شما!",
            parse_mode="HTML", reply_markup=main_menu())
    except Exception as e:
        print(f"[ERROR receipt] {e}")
        bot.send_message(uid, "⚠️ خطا در ثبت سفارش. لطفاً دوباره رسید را ارسال کنید.")


def check_referral_reward(buyer_uid, plan_name, config_name):
    user = db.get_user(buyer_uid)
    if not user or not user['referred_by']:
        return

    referrer_uid = user['referred_by']
    result = db.increment_referral_count(referrer_uid)
    if not result:
        return

    referral_count = result['referral_count']
    rewarded_sets = result['rewarded_sets']

    try:
        bot.send_message(referrer_uid,
            f"🎉 <b>یک نفر با لینک دعوت شما خرید کرد!</b>\n\n"
            f"👥 تعداد دعوت‌های موفق شما: <b>{referral_count}</b>\n"
            f"🎁 {REFERRAL_REWARD_EVERY - (referral_count % REFERRAL_REWARD_EVERY)} نفر دیگر تا جایزه!",
            parse_mode="HTML")
    except:
        pass

    if referral_count > 0 and referral_count % REFERRAL_REWARD_EVERY == 0:
        current_set = referral_count // REFERRAL_REWARD_EVERY
        if current_set > rewarded_sets:
            db.mark_rewarded_set(referrer_uid)
            referrer = db.get_user(referrer_uid)
            uname = f"@{referrer['username']}" if referrer and referrer['username'] else f"آیدی: {referrer_uid}"
            try:
                bot.send_message(GROUP_ID,
                    f"🏆 <b>کاربر برنده جایزه شد!</b>\n\n"
                    f"👤 {uname} | آیدی: <code>{referrer_uid}</code>\n"
                    f"👥 دعوت موفق: <b>{referral_count}</b>\n"
                    f"🎁 جایزه: <b>{REFERRAL_REWARD_GB} گیگابایت رایگان</b>",
                    parse_mode="HTML")
            except:
                pass
            try:
                bot.send_message(referrer_uid,
                    f"🏆🎉 <b>تبریک! {REFERRAL_REWARD_GB} گیگابایت رایگان بردید!</b>\n\n"
                    "⏳ ادمین به زودی کانفیگ جایزه ارسال می‌کند. ❤️",
                    parse_mode="HTML")
            except:
                pass


# ══════════════════════════════════════════════
# کیف پول
# ══════════════════════════════════════════════
def show_wallet(chat_id, uid):
    user = db.get_user(uid)
    kb = inline_kb(
        [green_btn("💰 موجودی", "wallet_balance"), green_btn("➕ شارژ کیف پول", "wallet_charge")],
        [red_btn("🔙 بازگشت", "back_main")]
    )
    send_colored_message(chat_id,
        f"👛 <b>کیف پول شما</b>\n\n💰 موجودی: <b>{price_fmt(user['wallet'])}</b>\n\nیک گزینه را انتخاب کنید:",
        kb)


@bot.callback_query_handler(func=lambda c: c.data == "wallet_balance")
def cb_wallet_balance(call):
    uid = call.from_user.id
    user = db.get_user(uid)
    kb = inline_kb(
        [green_btn("➕ شارژ کیف پول", "wallet_charge")],
        [red_btn("🔙 بازگشت", "back_wallet")]
    )
    edit_colored_message(call.message.chat.id, call.message.message_id,
        f"💰 <b>موجودی کیف پول:</b>\n\n<b>{price_fmt(user['wallet'])}</b>", kb)


@bot.callback_query_handler(func=lambda c: c.data == "wallet_charge")
def cb_wallet_charge(call):
    uid = call.from_user.id
    user_states[uid] = {'state': 'waiting_wallet_amount'}
    kb = inline_kb([red_btn("🔙 بازگشت", "back_wallet")])
    edit_colored_message(call.message.chat.id, call.message.message_id,
        "➕ <b>شارژ کیف پول</b>\n\n"
        "💬 مبلغ شارژ را <b>به تومان</b> وارد کن:\nمثال: <code>100000</code>", kb)


def handle_wallet_amount(message, uid):
    txt = message.text.strip().replace(",", "").replace("،", "")
    if not txt.isdigit() or int(txt) < 10000:
        bot.send_message(uid, "❌ مبلغ نامعتبر. حداقل <b>۱۰,۰۰۰ تومان</b>:", parse_mode="HTML")
        return

    amount = int(txt)
    user_states[uid]['amount'] = amount
    user_states[uid]['state'] = 'waiting_wallet_receipt'

    kb = inline_kb([red_btn("🔙 بازگشت", "back_wallet")])
    send_colored_message(uid,
        "╔══════════════════════╗\n 💳 <b>اطلاعات پرداخت</b>\n╚══════════════════════╝\n\n"
        f"💰 مبلغ شارژ: <b>{price_fmt(amount)}</b>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "📸 پس از واریز، <b>عکس رسید</b> را ارسال کنید:", kb)


def handle_wallet_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_wallet_receipt':
        return

    amount = st['amount']
    user_obj = message.from_user
    uname = f"@{user_obj.username}" if user_obj.username else "ندارد"

    caption = (
        "💳 <b>درخواست شارژ کیف پول</b>\n\n"
        f"👤 {user_obj.first_name} | {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"💰 مبلغ: <b>{price_fmt(amount)}</b>\n\n"
        f"✅ برای تایید، ریپلای کنید: <code>{amount}</code>"
    )

    try:
        sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        req_id = db.save_wallet_request(uid, amount)
        db.set_wallet_request_msg(req_id, sent.message_id)
        group_msg_to_wallet_req[sent.message_id] = req_id
        st['state'] = 'done'
        bot.send_message(uid,
            "✅ <b>رسید شارژ ثبت شد!</b>\n\n⏳ پس از تایید ادمین، موجودی اضافه می‌شود.",
            parse_mode="HTML", reply_markup=main_menu())
    except Exception as e:
        print(f"[ERROR wallet receipt] {e}")
        bot.send_message(uid, "⚠️ خطا در ثبت. دوباره رسید را ارسال کنید.")


# ══════════════════════════════════════════════
# حساب کاربری
# ══════════════════════════════════════════════
def show_account(chat_id, uid):
    user = db.get_user(uid)
    purchases = db.get_purchases_by_user(uid)
    ref_link = f"https://t.me/{bot.get_me().username}?start={user['referral_code']}"

    rows = []
    for p in purchases:
        rows.append([green_btn(f"📦 {p['config_name']} — {p['plan_name']}", f"reconfig_{p['id']}")])
    rows.append([red_btn("🔙 بازگشت", "back_main")])

    send_colored_message(chat_id,
        "👤 <b>حساب کاربری</b>\n\n"
        f"👥 دعوت موفق: <b>{user['referral_count']}</b>\n"
        f"🛒 تعداد خرید: <b>{len(purchases)}</b>\n"
        f"👛 موجودی: <b>{price_fmt(user['wallet'])}</b>\n\n"
        f"🔗 لینک دعوت:\n<code>{ref_link}</code>\n\n"
        "📋 <b>کانفیگ‌های خریداری‌شده:</b>",
        {"inline_keyboard": rows}
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("reconfig_"))
def cb_reconfig(call):
    purchase_id = int(call.data.split("_")[1])
    purchase = db.get_purchase_by_id(purchase_id)
    uid = call.from_user.id

    if not purchase or purchase['uid'] != uid:
        bot.answer_callback_query(call.id, "❌ کانفیگ یافت نشد!")
        return

    if not purchase['config_data']:
        bot.answer_callback_query(call.id, "⏳ کانفیگ هنوز آماده نشده!")
        return

    bot.answer_callback_query(call.id, "✅ ارسال شد")
    bot.send_message(uid,
        f"✅ <b>کانفیگ شما:</b>\n\n"
        f"📦 پلن: {purchase['plan_name']}\n"
        f"🏷️ نام: {purchase['config_name']}\n\n"
        f"🔗 لینک سابسکریپشن:\n<code>{purchase['config_data']}</code>",
        parse_mode="HTML")


# ══════════════════════════════════════════════
# دکمه‌های بازگشت
# ══════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("back_"))
def cb_back(call):
    uid = call.from_user.id
    dest = call.data[5:]

    if dest == "main":
        user_states.pop(uid, None)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🏠 منوی اصلی:", reply_markup=main_menu())

    elif dest == "plans":
        user_states.pop(uid, None)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_plans(call.message.chat.id, uid)

    elif dest == "wallet":
        user_states.pop(uid, None)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_wallet(call.message.chat.id, uid)

    elif dest == "config_name":
        st = user_states.get(uid, {})
        if st.get('plan_key'):
            plan = PLANS[st['plan_key']]
            st['state'] = 'waiting_config_name'
            kb = inline_kb([red_btn("🔙 بازگشت به پلن‌ها", "back_plans")])
            edit_colored_message(call.message.chat.id, call.message.message_id,
                f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
                "📝 یک <b>نام انگلیسی</b> برای کانفیگ وارد کنید:\n"
                "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>", kb)
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_plans(call.message.chat.id, uid)

    bot.answer_callback_query(call.id)


# ══════════════════════════════════════════════
# ریپلای ادمین در گروه
# ══════════════════════════════════════════════
@bot.message_handler(
    func=lambda m: m.chat.id == GROUP_ID and m.reply_to_message is not None
)
def handle_group_reply(message):
    replied_id = message.reply_to_message.message_id

    # ── شارژ کیف پول ──
    req = db.get_wallet_request_by_group_msg(replied_id)
    if req is not None:
        txt = message.text.strip() if message.text else ""
        clean = txt.replace(",", "").replace("،", "")
        if not clean.isdigit():
            bot.reply_to(message, "❌ عدد مبلغ را ریپلای کنید.\nمثال: <code>150000</code>", parse_mode="HTML")
            return
        confirmed_amount = int(clean)
        db.add_wallet(req['uid'], confirmed_amount)
        db.confirm_wallet_request(req['id'])
        try:
            bot.send_message(req['uid'],
                f"✅ <b>کیف پول شارژ شد!</b>\n\n"
                f"💰 مبلغ: <b>{price_fmt(confirmed_amount)}</b>\n"
                f"👛 موجودی جدید: <b>{price_fmt(db.get_user(req['uid'])['wallet'])}</b>",
                parse_mode="HTML", reply_markup=main_menu())
            bot.reply_to(message, f"✅ کیف پول کاربر <code>{req['uid']}</code> به مبلغ {price_fmt(confirmed_amount)} شارژ شد.", parse_mode="HTML")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: <code>{e}</code>", parse_mode="HTML")
        return

    # ── تایید خرید و ساخت اتوماتیک کانفیگ ──
    purchase = db.get_purchase_by_group_msg(replied_id)
    if purchase is not None:
        if purchase.get('config_data'):
            bot.reply_to(message, "⚠️ این سفارش قبلاً پردازش شده.")
            return

        txt = message.text.strip().lower() if message.text else ""
        if txt != "ok":
            bot.reply_to(message, "برای تایید بنویسید: <code>ok</code>", parse_mode="HTML")
            return

        bot.reply_to(message, "⏳ در حال ساخت کانفیگ اتوماتیک در پاسارگاد...")

        uid = purchase['uid']
        plan_key = purchase['plan_key']
        plan = PLANS.get(plan_key)
        if not plan:
            bot.reply_to(message, "❌ پلن یافت نشد!")
            return

        st = {
            'plan_key': plan_key,
            'config_name': purchase['config_name'],
            'discount': purchase['discount'],
            'final_price': purchase['price'],
        }

        user_info = db.get_user(uid)
        first_name = user_info['first_name'] if user_info else "کاربر"
        username = user_info['username'] if user_info else None

        _create_and_send_config(uid, first_name, username, st, plan, purchase['price'], wallet_paid=False)
        bot.reply_to(message, "✅ کانفیگ اتوماتیک ساخته و ارسال شد!")
        return


# ══════════════════════════════════════════════
# پیام همگانی (فقط ادمین)
# ══════════════════════════════════════════════
broadcast_state = {}

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.chat.type != 'private':
        bot.reply_to(message, "این دستور فقط در پیوی کار می‌کند.")
        return
    broadcast_state[ADMIN_ID] = True
    bot.send_message(ADMIN_ID,
        "📢 <b>پیام همگانی</b>\n\n"
        "پیام خود را ارسال کنید (متن، عکس، یا ویدیو):\n"
        "برای لغو: /cancel",
        parse_mode="HTML")

@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    if message.from_user.id != ADMIN_ID:
        return
    broadcast_state.pop(ADMIN_ID, None)
    bot.send_message(ADMIN_ID, "❌ عملیات لغو شد.", reply_markup=main_menu())

@bot.message_handler(
    func=lambda m: m.chat.type == 'private' and m.from_user.id == ADMIN_ID and broadcast_state.get(ADMIN_ID),
    content_types=['text', 'photo', 'video']
)
def handle_broadcast_message(message):
    if not broadcast_state.get(ADMIN_ID):
        return

    broadcast_state.pop(ADMIN_ID, None)

    all_users = db.get_all_users()
    success = 0
    fail = 0

    bot.send_message(ADMIN_ID, f"⏳ در حال ارسال به {len(all_users)} کاربر...")

    for user in all_users:
        try:
            if message.content_type == 'text':
                bot.send_message(user['uid'], message.text, parse_mode="HTML")
            elif message.content_type == 'photo':
                caption = message.caption or ""
                bot.send_photo(user['uid'], message.photo[-1].file_id, caption=caption, parse_mode="HTML")
            elif message.content_type == 'video':
                caption = message.caption or ""
                bot.send_video(user['uid'], message.video.file_id, caption=caption, parse_mode="HTML")
            success += 1
        except Exception:
            fail += 1

    bot.send_message(ADMIN_ID,
        f"✅ <b>پیام همگانی ارسال شد!</b>\n\n"
        f"✔️ موفق: <b>{success}</b>\n"
        f"❌ ناموفق: <b>{fail}</b>",
        parse_mode="HTML", reply_markup=main_menu())


# ─── اجرا ───
if __name__ == "__main__":
    db.init_db()
    pg_login()  # لاگین اولیه به پاسارگاد
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🤖 Bot started (polling)...")
    bot.infinity_polling()
