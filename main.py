from flask import Flask, send_from_directory
from threading import Thread
import telebot
from telebot import types
import random
import string
import re
import json
import os
import database as db

# =================== تنظیمات ===================
BOT_TOKEN    = "8773215261:AAF67pQ9AHZrzvMOZlNbsnaG2-uoTo3HHyk"
ADMIN_ID     = 7374971382
ADMIN_USERNAME = "AIireza_1383"
GROUP_ID     = -1004294169429
CARD_NUMBER  = "5892101542283284"
CARD_OWNER   = "علیرضا وحدانی اصل"

# آدرس Railway خودت رو اینجا بذار (بدون / آخر)
# مثال: https://bot-production-xxxx.up.railway.app
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://your-app.up.railway.app")

REFERRAL_INVITEE_DISCOUNT = 5   # درصد تخفیف برای دعوت‌شده
REFERRAL_REFERRER_DISCOUNT = 7  # درصد تخفیف برای معرف
REFERRAL_REWARD_EVERY = 10      # هر چند نفر جایزه
REFERRAL_REWARD_GB    = 5       # گیگابایت جایزه
# ================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_states = {}
group_msg_to_wallet_req = {}
group_msg_to_purchase   = {}

PLANS = {
    "plan_10gb": {"name": "۱۰ گیگابایت", "price": 150000},
    "plan_20gb": {"name": "۲۰ گیگابایت", "price": 300000},
    "plan_30gb": {"name": "۳۰ گیگابایت", "price": 400000},
    "plan_40gb": {"name": "۴۰ گیگابایت", "price": 520000},
}

def price_fmt(p):
    return f"{p:,}".replace(",", "،") + "  تومان"

# ─── Flask routes ───────────────────────────────
@app.route('/')
def home():
    return "Bot is running!", 200

@app.route('/app')
def webapp():
    """سرو کردن Mini App"""
    return send_from_directory('.', 'webapp.html')

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 7860)))

# ─── منوی اصلی با دکمه Mini App ────────────────
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(
            "🌐 باز کردن پنل VPN",
            web_app=types.WebAppInfo(url=f"{WEBAPP_URL}/app")
        )
    )
    markup.add(
        types.KeyboardButton("👤 حساب من"),
        types.KeyboardButton("👨‍💻 پشتیبانی"),
    )
    return markup

def gen_referral_code(uid):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

def ensure_user(message):
    uid  = message.from_user.id
    user = db.get_user(uid)
    if not user:
        code = gen_referral_code(uid)
        db.create_user(uid, message.from_user.first_name, message.from_user.username, code)
        user = db.get_user(uid)
    return user

def back_btn(text="🔙 بازگشت", data="back_main"):
    return types.InlineKeyboardButton(text, callback_data=data)

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

    user     = db.get_user(uid)
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
        "🎁 <b>سیستم تخفیف دوستان</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 لینک دعوت اختصاصی تو:\n<code>{ref_link}</code>\n\n"
        f"👥 هر دوستی که با لینک تو بیاد و خرید کنه:\n"
        f" ➡️ <b>دوستت {REFERRAL_INVITEE_DISCOUNT}٪ تخفیف</b> روی اولین خریدش می‌گیره\n"
        f" ➡️ <b>تو {REFERRAL_REFERRER_DISCOUNT}٪ تخفیف</b> روی خرید بعدیت می‌گیری\n\n"
        f"🏆 <b>هر {REFERRAL_REWARD_EVERY} نفر دعوت موفق = {REFERRAL_REWARD_GB} گیگابایت رایگان!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 روی دکمه سبز بزن تا پنل VPN باز بشه:"
    )
    bot.send_message(message.chat.id, welcome, parse_mode="HTML", reply_markup=main_menu())

# ══════════════════════════════════════════════
# دریافت داده از Mini App (web_app_data)
# ══════════════════════════════════════════════
@bot.message_handler(content_types=['web_app_data'])
def handle_webapp_data(message):
    uid = message.from_user.id
    ensure_user(message)

    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        bot.send_message(uid, "❌ خطا در دریافت اطلاعات.", reply_markup=main_menu())
        return

    action    = data.get('action')
    plan_key  = data.get('plan')

    if action not in ('pay_wallet', 'pay_card') or plan_key not in PLANS:
        bot.send_message(uid, "❌ درخواست نامعتبر.", reply_markup=main_menu())
        return

    plan = PLANS[plan_key]
    user = db.get_user(uid)

    # محاسبه تخفیف
    discount    = REFERRAL_INVITEE_DISCOUNT if user['referred_by'] else 0
    final_price = int(plan['price'] * (1 - discount / 100))

    user_states[uid] = {
        'plan_key':    plan_key,
        'discount':    discount,
        'final_price': final_price,
    }

    if action == 'pay_wallet':
        # ── پرداخت از کیف پول ──
        if user['wallet'] < final_price:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge"))
            bot.send_message(uid,
                f"❌ <b>موجودی کافی نیست!</b>\n\n"
                f"💰 موجودی شما: <b>{price_fmt(user['wallet'])}</b>\n"
                f"💳 مبلغ مورد نیاز: <b>{price_fmt(final_price)}</b>\n\n"
                "ابتدا کیف پول خود را شارژ کنید:",
                parse_mode="HTML", reply_markup=markup)
            return

        # نیاز به نام کانفیگ داریم
        user_states[uid]['state']  = 'waiting_config_name'
        user_states[uid]['method'] = 'wallet'
        markup = types.InlineKeyboardMarkup()
        markup.add(back_btn("🔙 بازگشت", "back_main"))
        bot.send_message(uid,
            f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
            "📝 لطفاً یک <b>نام انگلیسی</b> برای کانفیگ خود وارد کنید:\n"
            "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>",
            parse_mode="HTML", reply_markup=markup)

    elif action == 'pay_card':
        # ── پرداخت کارت به کارت ──
        user_states[uid]['state']  = 'waiting_config_name'
        user_states[uid]['method'] = 'card'
        markup = types.InlineKeyboardMarkup()
        markup.add(back_btn("🔙 بازگشت", "back_main"))
        bot.send_message(uid,
            f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
            "📝 لطفاً یک <b>نام انگلیسی</b> برای کانفیگ خود وارد کنید:\n"
            "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>",
            parse_mode="HTML", reply_markup=markup)

# ══════════════════════════════════════════════
# هندلر اصلی پیام‌های پرایوت
# ══════════════════════════════════════════════
@bot.message_handler(
    func=lambda m: m.chat.type == 'private',
    content_types=['text', 'photo', 'document', 'sticker', 'voice', 'video', 'audio']
)
def handle_private(message):
    uid   = message.from_user.id
    state = user_states.get(uid, {}).get('state', '')
    ensure_user(message)

    if message.content_type == 'text':
        txt = message.text.strip()

        # ── منوی اصلی ──
        if txt in ("🌐 باز کردن پنل VPN",):
            # کاربر روی دکمه WebApp زد (نباید به اینجا برسه ولی به عنوان fallback)
            bot.send_message(uid, "لطفاً روی دکمه سبز بزنید تا پنل باز شود.", reply_markup=main_menu())
            return

        if txt == "👤 حساب من":
            user_states.pop(uid, None)
            show_account(message.chat.id, uid)
            return

        if txt == "👨‍💻 پشتیبانی":
            mk = types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("💬 ارتباط با پشتیبانی", url=f"https://t.me/{ADMIN_USERNAME}"))
            bot.send_message(message.chat.id,
                "👨‍💻 <b>پشتیبانی</b>\n\nبرای سوال یا پیگیری سفارش روی دکمه زیر بزنید:",
                parse_mode="HTML", reply_markup=mk)
            return

        # ── مراحل خرید ──
        if state == 'waiting_config_name':
            handle_config_name(message, uid)
            return

        if state == 'waiting_wallet_amount':
            handle_wallet_amount(message, uid)
            return

        if state in ('waiting_receipt', 'waiting_wallet_receipt'):
            bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> پرداخت را ارسال کنید.", parse_mode="HTML")
            return

        bot.send_message(uid, "برای شروع /start بزنید یا از دکمه پنل استفاده کنید.", reply_markup=main_menu())
        return

    # ── عکس ──
    if message.content_type == 'photo':
        if state == 'waiting_receipt':
            handle_purchase_receipt(message, uid)
        elif state == 'waiting_wallet_receipt':
            handle_wallet_receipt(message, uid)
        else:
            bot.send_message(uid, "❌ ابتدا یک پلن از پنل انتخاب کنید.", reply_markup=main_menu())
        return

    if state in ('waiting_receipt', 'waiting_wallet_receipt'):
        bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> پرداخت را ارسال کنید.", parse_mode="HTML")

# ══════════════════════════════════════════════
# نام کانفیگ و روش پرداخت
# ══════════════════════════════════════════════
def handle_config_name(message, uid):
    name = message.text.strip()
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9 ]*$', name):
        bot.send_message(uid,
            "❌ نام باید فقط از <b>حروف انگلیسی</b> باشد.\n"
            "مثال: <code>Alireza</code>\n\nدوباره وارد کنید:",
            parse_mode="HTML")
        return

    st   = user_states[uid]
    plan = PLANS[st['plan_key']]
    st['config_name'] = name

    if st.get('method') == 'wallet':
        # پرداخت مستقیم از کیف پول
        user        = db.get_user(uid)
        final_price = st['final_price']

        if user['wallet'] < final_price:
            bot.send_message(uid, "❌ موجودی کافی نیست! لطفاً کیف پول را شارژ کنید.", reply_markup=main_menu())
            user_states.pop(uid, None)
            return

        db.deduct_wallet(uid, final_price)
        uname   = f"@{message.from_user.username}" if message.from_user.username else "ندارد"
        caption = (
            "💰 <b>خرید از کیف پول!</b>\n\n"
            f"📦 پلن: <b>{plan['name']} — {price_fmt(final_price)}</b>\n"
            f"🏷️ نام کانفیگ: <code>{name}</code>\n"
            f"👤 نام: <b>{message.from_user.first_name}</b>\n"
            f"🆔 یوزرنیم: {uname}\n"
            f"🔢 آیدی: <code>{uid}</code>\n"
            f"💸 مبلغ کسرشده از کیف پول: <b>{price_fmt(final_price)}</b>\n\n"
            "✅ روی این پیام <b>ریپلای</b> کنید تا کانفیگ ارسال شود."
        )
        try:
            sent        = bot.send_message(GROUP_ID, caption, parse_mode="HTML")
            purchase_id = db.save_purchase(
                uid, st['plan_key'], plan['name'], final_price,
                name, True, st['discount'], sent.message_id
            )
            group_msg_to_purchase[sent.message_id] = purchase_id
            st['state'] = 'done'
            bot.send_message(uid,
                "✅ <b>پرداخت از کیف پول انجام شد!</b>\n\n"
                "⏳ ادمین در حال آماده‌سازی کانفیگ شماست...\n"
                "🙏 ممنون از خرید شما!",
                parse_mode="HTML", reply_markup=main_menu())
            check_referral_reward(uid, plan['name'], name)
        except Exception as e:
            print(f"[ERROR wallet pay] {e}")
            db.add_wallet(uid, final_price)
            bot.send_message(uid, "❌ خطا رخ داد، دوباره تلاش کنید.", reply_markup=main_menu())
        return

    # روش کارت به کارت
    st['state'] = 'waiting_receipt'
    markup = types.InlineKeyboardMarkup()
    markup.add(back_btn("🔙 بازگشت", "back_main"))
    disc_txt = f"\n🎁 تخفیف دعوت: <b>{st['discount']}٪</b>" if st['discount'] else ""
    bot.send_message(uid,
        "╔══════════════════════╗\n"
        " 💳 <b>اطلاعات پرداخت</b>\n"
        "╚══════════════════════╝\n\n"
        f"📦 پلن: <b>{plan['name']}</b>\n"
        f"💰 مبلغ نهایی: <b>{price_fmt(st['final_price'])}</b>{disc_txt}\n"
        f"🏷️ نام کانفیگ: <code>{name}</code>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 پس از واریز، <b>عکس رسید</b> را در همین چت ارسال کنید:",
        parse_mode="HTML", reply_markup=markup)

def handle_purchase_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_receipt':
        return

    plan        = PLANS[st['plan_key']]
    config_name = st['config_name']
    user_obj    = message.from_user
    uname       = f"@{user_obj.username}" if user_obj.username else "ندارد"

    caption = (
        "🚨 <b>سفارش جدید دریافت شد!</b>\n\n"
        f"📦 پلن: <b>{plan['name']} — {price_fmt(st['final_price'])}</b>\n"
        f"🏷️ نام کانفیگ: <code>{config_name}</code>\n"
        f"👤 نام: <b>{user_obj.first_name}</b>\n"
        f"🆔 یوزرنیم: {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"🎁 تخفیف: {st['discount']}٪\n\n"
        "✅ برای ارسال کانفیگ روی این پیام <b>ریپلای</b> کنید."
    )
    try:
        sent        = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        purchase_id = db.save_purchase(
            uid, st['plan_key'], plan['name'], st['final_price'],
            config_name, False, st['discount'], sent.message_id
        )
        group_msg_to_purchase[sent.message_id] = purchase_id
        st['state'] = 'done'
        bot.send_message(uid,
            "✅ <b>رسید شما با موفقیت ثبت شد!</b>\n\n"
            "⏳ در حال بررسی توسط ادمین...\n"
            "پس از تایید، کانفیگ برای شما ارسال می‌شود.\n\n"
            "🙏 ممنون از خرید شما!",
            parse_mode="HTML", reply_markup=main_menu())
    except Exception as e:
        print(f"[ERROR receipt] {e}")
        bot.send_message(uid, "⚠️ خطا در ثبت سفارش. لطفاً دوباره رسید را ارسال کنید.")

# ══════════════════════════════════════════════
# کیف پول (از طریق Inline Button)
# ══════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data == "wallet_charge")
def cb_wallet_charge(call):
    uid = call.from_user.id
    user_states[uid] = {'state': 'waiting_wallet_amount'}
    markup = types.InlineKeyboardMarkup()
    markup.add(back_btn("🔙 بازگشت", "back_main"))
    bot.send_message(call.message.chat.id,
        "➕ <b>شارژ کیف پول</b>\n\n"
        "💬 مبلغی که می‌خواهی شارژ کنی را <b>به تومان</b> وارد کن:\n"
        "مثال: <code>100000</code>",
        parse_mode="HTML", reply_markup=markup)
    bot.answer_callback_query(call.id)

def handle_wallet_amount(message, uid):
    txt = message.text.strip().replace(",", "").replace("،", "")
    if not txt.isdigit() or int(txt) < 10000:
        bot.send_message(uid, "❌ مبلغ نامعتبر. حداقل <b>۱۰,۰۰۰ تومان</b> وارد کنید:", parse_mode="HTML")
        return

    amount = int(txt)
    user_states[uid]['amount'] = amount
    user_states[uid]['state']  = 'waiting_wallet_receipt'

    markup = types.InlineKeyboardMarkup()
    markup.add(back_btn("🔙 بازگشت", "back_main"))
    bot.send_message(uid,
        "╔══════════════════════╗\n"
        " 💳 <b>اطلاعات پرداخت</b>\n"
        "╚══════════════════════╝\n\n"
        f"💰 مبلغ شارژ: <b>{price_fmt(amount)}</b>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 پس از واریز، <b>عکس رسید</b> را در همین چت ارسال کنید:",
        parse_mode="HTML", reply_markup=markup)

def handle_wallet_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_wallet_receipt':
        return

    amount   = st['amount']
    user_obj = message.from_user
    uname    = f"@{user_obj.username}" if user_obj.username else "ندارد"

    caption = (
        "💳 <b>درخواست شارژ کیف پول</b>\n\n"
        f"👤 نام: <b>{user_obj.first_name}</b>\n"
        f"🆔 یوزرنیم: {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"💰 مبلغ درخواستی: <b>{price_fmt(amount)}</b>\n\n"
        f"✅ برای تایید، دقیقاً همین عدد را ریپلای کنید: <code>{amount}</code>"
    )
    try:
        sent   = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        req_id = db.save_wallet_request(uid, amount)
        db.set_wallet_request_msg(req_id, sent.message_id)
        group_msg_to_wallet_req[sent.message_id] = req_id
        st['state'] = 'done'
        bot.send_message(uid,
            "✅ <b>رسید شارژ ثبت شد!</b>\n\n"
            "⏳ ادمین در حال بررسی...\n"
            "پس از تایید، موجودی کیف پول شما افزایش می‌یابد.",
            parse_mode="HTML", reply_markup=main_menu())
    except Exception as e:
        print(f"[ERROR wallet receipt] {e}")
        bot.send_message(uid, "⚠️ خطا در ثبت. دوباره رسید را ارسال کنید.")

# ══════════════════════════════════════════════
# حساب من
# ══════════════════════════════════════════════
def show_account(chat_id, uid):
    user      = db.get_user(uid)
    purchases = db.get_purchases_by_user(uid)
    ref_link  = f"https://t.me/{bot.get_me().username}?start={user['referral_code']}"

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge"))
    for p in purchases:
        markup.add(types.InlineKeyboardButton(
            f"📦 {p['config_name']} — {p['plan_name']}",
            callback_data=f"reconfig_{p['id']}"
        ))
    markup.add(back_btn("🔙 بازگشت", "back_main"))

    bot.send_message(chat_id,
        "👤 <b>حساب من</b>\n\n"
        f"👥 تعداد دعوت موفق: <b>{user['referral_count']}</b>\n"
        f"🛒 تعداد خرید: <b>{len(purchases)}</b>\n"
        f"👛 موجودی: <b>{price_fmt(user['wallet'])}</b>\n\n"
        f"🔗 لینک دعوت:\n<code>{ref_link}</code>\n\n"
        "📋 <b>کانفیگ‌های خریداری‌شده</b> (برای ارسال مجدد کلیک کنید):",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("reconfig_"))
def cb_reconfig(call):
    purchase_id = int(call.data.split("_")[1])
    purchase    = db.get_purchase_by_id(purchase_id)
    uid         = call.from_user.id

    if not purchase or purchase['uid'] != uid:
        bot.answer_callback_query(call.id, "❌ کانفیگ یافت نشد!")
        return
    if not purchase['config_data']:
        bot.answer_callback_query(call.id, "⏳ کانفیگ هنوز ارسال نشده!")
        return

    bot.answer_callback_query(call.id, "✅ کانفیگ ارسال شد")
    bot.send_message(uid,
        f"✅ <b>کانفیگ شما:</b>\n\n"
        f"📦 پلن: {purchase['plan_name']}\n"
        f"🏷️ نام: {purchase['config_name']}\n\n"
        f"<code>{purchase['config_data']}</code>",
        parse_mode="HTML")

# ══════════════════════════════════════════════
# دکمه‌های بازگشت
# ══════════════════════════════════════════════
@bot.callback_query_handler(func=lambda c: c.data.startswith("back_"))
def cb_back(call):
    uid  = call.from_user.id
    dest = call.data[5:]
    if dest == "main":
        user_states.pop(uid, None)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id,
            "🏠 به منوی اصلی برگشتید.", reply_markup=main_menu())
    bot.answer_callback_query(call.id)

# ══════════════════════════════════════════════
# سیستم رفرال
# ═════════════════════════════════════
