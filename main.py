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
# ================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
user_states = {}

PLANS = {
    "plan_10gb": {"name": "۱۰ گیگابایت", "price": 150000},
    "plan_20gb": {"name": "۲۰ گیگابایت", "price": 300000},
    "plan_30gb": {"name": "۳۰ گیگابایت", "price": 400000},
    "plan_40gb": {"name": "۴۰ گیگابایت", "price": 520000},
}

def price_fmt(p):
    return f"{p:,}".replace(",", "،") + " تومان"

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web():
    app.run(host='0.0.0.0', port=7860)

# ══════════════════════════════════════════════
# ارسال پیام با دکمه‌های رنگی (مستقیم به Bot API)
# ══════════════════════════════════════════════
def send_msg(chat_id, text, markup=None, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if markup:
        payload["reply_markup"] = markup
    r = requests.post(url, json=payload)
    data = r.json()
    if data.get("ok"):
        return data["result"]["message_id"]
    print(f"[send_msg error] {data}")
    return None

def edit_msg(chat_id, msg_id, text, markup=None, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": parse_mode}
    if markup:
        payload["reply_markup"] = markup
    r = requests.post(url, json=payload)
    data = r.json()
    if not data.get("ok"):
        print(f"[edit_msg error] {data}")

def send_reply_keyboard(chat_id, text, markup, parse_mode="HTML"):
    """ارسال پیام با ReplyKeyboard از طریق telebot"""
    bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=markup)

# ── سازنده دکمه‌های رنگی ──
def gbtn(text, cb):
    """دکمه سبز"""
    return {"text": text, "callback_data": cb, "style": "success"}

def bbtn(text, cb):
    """دکمه آبی (بازگشت)"""
    return {"text": text, "callback_data": cb, "style": "primary"}

def ubtn(text, url):
    """دکمه لینک"""
    return {"text": text, "url": url}

def ikb(*rows):
    """ساخت InlineKeyboard"""
    return {"inline_keyboard": [list(row) for row in rows]}

# ── منوی اصلی ──
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 خرید سرویس"),
        types.KeyboardButton("👛 کیف پول"),
        types.KeyboardButton("👤 حساب کاربری"),
        types.KeyboardButton("👨‍💻 پشتیبانی"),
    )
    return markup

def ensure_user(message):
    uid = message.from_user.id
    if not db.get_user(uid):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        db.create_user(uid, message.from_user.first_name, message.from_user.username, code)
    return db.get_user(uid)

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
        referrer = db.get_user_by_referral(args[1])
        if referrer and referrer['uid'] != uid:
            referred_by = referrer['uid']

    if not db.get_user(uid):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        db.create_user(uid, message.from_user.first_name, message.from_user.username, code, referred_by)

    user = db.get_user(uid)
    me = bot.get_me()
    ref_link = f"https://t.me/{me.username}?start={user['referral_code']}"

    text = (
        f"🎉 <b>سلام {message.from_user.first_name} عزیز، خوش اومدی!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌐 <b>VPN حرفه‌ای | سرعت بالا | بدون محدودیت</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ سازگار با V2Ray، V2Box، NPVtunnel، HIDDEFY\n\n"
        f"🔗 لینک دعوت اختصاصی تو:\n<code>{ref_link}</code>\n\n"
        f"🎁 هر دوستی که خرید کنه:\n"
        f"  ➡️ دوستت <b>{REFERRAL_INVITEE_DISCOUNT}٪ تخفیف</b> می‌گیره\n"
        f"  ➡️ تو <b>{REFERRAL_REFERRER_DISCOUNT}٪ تخفیف</b> روی خرید بعدی\n\n"
        f"🏆 هر {REFERRAL_REWARD_EVERY} دعوت موفق = <b>{REFERRAL_REWARD_GB} گیگ رایگان!</b>\n\n"
        "👇 از منو زیر شروع کن:"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=main_menu())

# ══════════════════════════════════════════════
# هندلر پیام‌های خصوصی
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
            send_msg(message.chat.id,
                "👨‍💻 <b>پشتیبانی</b>\n\nبرای سوال یا پیگیری سفارش روی دکمه زیر بزنید:",
                ikb([ubtn("💬 ارتباط با پشتیبانی", f"https://t.me/{ADMIN_USERNAME}")]))
            return

        if state == 'waiting_config_name':
            handle_config_name(message, uid)
            return

        if state == 'waiting_wallet_amount':
            handle_wallet_amount(message, uid)
            return

        if state in ('waiting_receipt', 'waiting_wallet_receipt'):
            bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> ارسال کنید.", parse_mode="HTML")
            return

        bot.send_message(uid, "برای شروع /start بزنید.", reply_markup=main_menu())
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
        bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> ارسال کنید.", parse_mode="HTML")

# ══════════════════════════════════════════════
# خرید سرویس
# ══════════════════════════════════════════════
def show_plans(chat_id, uid):
    user = db.get_user(uid)
    has_ref = bool(user and user['referred_by'])

    rows = []
    for key, plan in PLANS.items():
        price = plan['price']
        short_key = key.split('_', 1)[1]  # 10gb, 20gb, ...
        if has_ref:
            disc = int(price * (1 - REFERRAL_INVITEE_DISCOUNT / 100))
            label = f"📦 {plan['name']} ─ {price_fmt(disc)} 🎁{REFERRAL_INVITEE_DISCOUNT}٪"
        else:
            label = f"📦 {plan['name']} ─ {price_fmt(price)}"
        rows.append([gbtn(label, f"buyplan_{short_key}")])

    rows.append([bbtn("🔙 بازگشت", "back_main")])

    note = f"\n🎁 <b>شما {REFERRAL_INVITEE_DISCOUNT}٪ تخفیف دعوت‌شده دارید!</b>" if has_ref else ""
    send_msg(chat_id,
        "💎 <b>پلن‌های موجود:</b>\n\n"
        "✅ تعداد کاربر: <b>نامحدود</b>\n"
        "✅ مدت زمان: <b>نامحدود</b>\n\n"
        "🚀 V2RAY | V2BOX | NPVtunnel | HIDDEFY\n"
        f"{note}\n\n"
        "👇 پلن مورد نظر را انتخاب کنید:",
        {"inline_keyboard": rows}
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("buyplan_"))
def cb_plan(call):
    uid = call.from_user.id
    short_key = call.data[8:]          # 10gb, 20gb, ...
    plan_key = "plan_" + short_key     # plan_10gb, ...
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

    bot.answer_callback_query(call.id)
    edit_msg(call.message.chat.id, call.message.message_id,
        f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
        "📝 یک <b>نام انگلیسی</b> برای کانفیگ وارد کنید:\n"
        "⚠️ <i>فقط حروف انگلیسی بدون فاصله — مثال: Alireza</i>",
        ikb([bbtn("🔙 بازگشت به پلن‌ها", "back_plans")])
    )

def handle_config_name(message, uid):
    name = message.text.strip()
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
        bot.send_message(uid,
            "❌ نام باید فقط <b>حروف انگلیسی</b> باشد (بدون فاصله).\n"
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
    if wallet >= final_price:
        rows.append([gbtn(f"💰 کیف پول — موجودی: {price_fmt(wallet)} ✅", "pay_wallet")])
    elif wallet > 0:
        rows.append([gbtn(f"💰 کیف پول — موجودی: {price_fmt(wallet)} (کمبود {price_fmt(final_price-wallet)})", "pay_wallet_low")])

    rows.append([gbtn("💳 پرداخت کارت به کارت", "pay_card")])
    rows.append([bbtn("🔙 بازگشت به پلن‌ها", "back_plans")])

    disc_txt = f"\n🎁 تخفیف دعوت: <b>{st['discount']}٪</b>" if st['discount'] else ""
    send_msg(uid,
        "╔══════════════════════╗\n"
        " 🛒 <b>خلاصه سفارش شما</b>\n"
        "╚══════════════════════╝\n\n"
        f"📦 پلن: <b>{plan['name']}</b>\n"
        f"💰 قیمت: <b>{price_fmt(plan['price'])}</b>{disc_txt}\n"
        f"✅ مبلغ نهایی: <b>{price_fmt(final_price)}</b>\n"
        f"🏷️ نام کانفیگ: <code>{name}</code>\n"
        f"👛 موجودی کیف پول: <b>{price_fmt(wallet)}</b>\n\n"
        "👇 روش پرداخت را انتخاب کنید:",
        {"inline_keyboard": rows}
    )
    st['state'] = 'choosing_payment'

@bot.callback_query_handler(func=lambda c: c.data == "pay_wallet_low")
def cb_wallet_low(call):
    bot.answer_callback_query(call.id, "❌ موجودی کافی نیست! ابتدا کیف پول را شارژ کنید.", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "pay_wallet")
def cb_pay_wallet(call):
    uid = call.from_user.id
    st = user_states.get(uid, {})
    if not st:
        bot.answer_callback_query(call.id, "❌ خطا، دوباره از /start شروع کنید.")
        return

    plan = PLANS[st['plan_key']]
    final_price = st['final_price']
    user = db.get_user(uid)

    if user['wallet'] < final_price:
        bot.answer_callback_query(call.id, "❌ موجودی کافی نیست!", show_alert=True)
        return

    db.deduct_wallet(uid, final_price)
    bot.answer_callback_query(call.id, "✅ پرداخت موفق!")

    uname = f"@{call.from_user.username}" if call.from_user.username else "ندارد"
    group_text = (
        "💰 <b>خرید از کیف پول!</b>\n\n"
        f"📦 پلن: <b>{plan['name']} — {price_fmt(final_price)}</b>\n"
        f"🏷️ نام کانفیگ: <code>{st['config_name']}</code>\n"
        f"👤 نام: <b>{call.from_user.first_name}</b>\n"
        f"🆔 یوزرنیم: {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"🎁 تخفیف: {st['discount']}٪\n\n"
        "✅ روی این پیام <b>ریپلای</b> کنید تا کانفیگ ارسال شود."
    )

    try:
        sent = bot.send_message(GROUP_ID, group_text, parse_mode="HTML")
        db.save_purchase(uid, st['plan_key'], plan['name'], final_price,
                         st['config_name'], True, st['discount'], sent.message_id)
        st['state'] = 'done'

        edit_msg(call.message.chat.id, call.message.message_id,
            "✅ <b>پرداخت از کیف پول انجام شد!</b>\n\n"
            "⏳ ادمین در حال آماده‌سازی کانفیگ...\n"
            "🙏 ممنون از خرید شما!",
            ikb([gbtn("🛒 خرید مجدد", "back_plans")])
        )
        check_referral_reward(uid, plan['name'], st['config_name'])

    except Exception as e:
        db.add_wallet(uid, final_price)
        print(f"[ERROR pay_wallet] {e}")
        bot.answer_callback_query(call.id, "❌ خطا! مبلغ برگشت داده شد.", show_alert=True)

@bot.callback_query_handler(func=lambda c: c.data == "pay_card")
def cb_pay_card(call):
    uid = call.from_user.id
    st = user_states.get(uid, {})
    if not st:
        bot.answer_callback_query(call.id, "❌ خطا، دوباره از /start شروع کنید.")
        return

    st['state'] = 'waiting_receipt'
    bot.answer_callback_query(call.id)

    edit_msg(call.message.chat.id, call.message.message_id,
        "╔══════════════════════╗\n"
        " 💳 <b>اطلاعات پرداخت</b>\n"
        "╚══════════════════════╝\n\n"
        f"💰 مبلغ: <b>{price_fmt(st['final_price'])}</b>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 پس از واریز، <b>عکس رسید</b> را در همین چت ارسال کنید:",
        ikb([bbtn("🔙 بازگشت به پلن‌ها", "back_plans")])
    )

def handle_purchase_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_receipt':
        return

    plan = PLANS[st['plan_key']]
    uname = f"@{message.from_user.username}" if message.from_user.username else "ندارد"

    caption = (
        "🚨 <b>سفارش جدید دریافت شد!</b>\n\n"
        f"📦 پلن: <b>{plan['name']} — {price_fmt(st['final_price'])}</b>\n"
        f"🏷️ نام کانفیگ: <code>{st['config_name']}</code>\n"
        f"👤 نام: <b>{message.from_user.first_name}</b>\n"
        f"🆔 یوزرنیم: {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"🎁 تخفیف: {st['discount']}٪\n\n"
        "✅ برای ارسال کانفیگ روی این پیام <b>ریپلای</b> کنید."
    )

    try:
        sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        db.save_purchase(uid, st['plan_key'], plan['name'], st['final_price'],
                         st['config_name'], False, st['discount'], sent.message_id)
        st['state'] = 'done'
        bot.send_message(uid,
            "✅ <b>رسید شما ثبت شد!</b>\n\n"
            "⏳ پس از تایید ادمین، کانفیگ ارسال می‌شود.\n"
            "🙏 ممنون از خرید شما!",
            parse_mode="HTML", reply_markup=main_menu())
    except Exception as e:
        print(f"[ERROR receipt] {e}")
        bot.send_message(uid, "⚠️ خطا در ثبت سفارش. دوباره رسید را ارسال کنید.")

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
        remaining = REFERRAL_REWARD_EVERY - (referral_count % REFERRAL_REWARD_EVERY)
        bot.send_message(referrer_uid,
            f"🎉 <b>یک نفر با لینک دعوت شما خرید کرد!</b>\n\n"
            f"👥 تعداد دعوت موفق: <b>{referral_count}</b>\n"
            f"🎁 {remaining} نفر دیگر تا جایزه!",
            parse_mode="HTML")
    except:
        pass
    if referral_count % REFERRAL_REWARD_EVERY == 0:
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
                    f"🎁 جایزه: <b>{REFERRAL_REWARD_GB} گیگابایت رایگان</b>\n\n"
                    "⬇️ ریپلای کنید تا کانفیگ جایزه ارسال شود.",
                    parse_mode="HTML")
                bot.send_message(referrer_uid,
                    f"🏆🎉 <b>تبریک! {REFERRAL_REWARD_GB} گیگ رایگان بردید!</b>\n\n"
                    "⏳ ادمین به زودی کانفیگ جایزه ارسال می‌کند. ❤️",
                    parse_mode="HTML")
            except:
                pass

# ══════════════════════════════════════════════
# کیف پول
# ══════════════════════════════════════════════
def show_wallet(chat_id, uid):
    user = db.get_user(uid)
    send_msg(chat_id,
        f"👛 <b>کیف پول شما</b>\n\n"
        f"💰 موجودی: <b>{price_fmt(user['wallet'])}</b>\n\n"
        "یک گزینه را انتخاب کنید:",
        ikb(
            [gbtn("💰 مشاهده موجودی", "wallet_balance"), gbtn("➕ شارژ کیف پول", "wallet_charge")],
            [bbtn("🔙 بازگشت", "back_main")]
        )
    )

@bot.callback_query_handler(func=lambda c: c.data == "wallet_balance")
def cb_wallet_balance(call):
    user = db.get_user(call.from_user.id)
    bot.answer_callback_query(call.id)
    edit_msg(call.message.chat.id, call.message.message_id,
        f"💰 <b>موجودی کیف پول:</b>\n\n<b>{price_fmt(user['wallet'])}</b>",
        ikb(
            [gbtn("➕ شارژ کیف پول", "wallet_charge")],
            [bbtn("🔙 بازگشت", "back_wallet")]
        )
    )

@bot.callback_query_handler(func=lambda c: c.data == "wallet_charge")
def cb_wallet_charge(call):
    uid = call.from_user.id
    user_states[uid] = {'state': 'waiting_wallet_amount'}
    bot.answer_callback_query(call.id)
    edit_msg(call.message.chat.id, call.message.message_id,
        "➕ <b>شارژ کیف پول</b>\n\n"
        "💬 مبلغ شارژ را <b>به تومان</b> وارد کنید:\n"
        "مثال: <code>100000</code>",
        ikb([bbtn("🔙 بازگشت", "back_wallet")])
    )

def handle_wallet_amount(message, uid):
    txt = message.text.strip().replace(",", "").replace("،", "")
    if not txt.isdigit() or int(txt) < 10000:
        bot.send_message(uid, "❌ مبلغ نامعتبر. حداقل <b>۱۰,۰۰۰ تومان</b> وارد کنید:", parse_mode="HTML")
        return
    amount = int(txt)
    user_states[uid]['amount'] = amount
    user_states[uid]['state'] = 'waiting_wallet_receipt'
    send_msg(uid,
        "╔══════════════════════╗\n"
        " 💳 <b>اطلاعات پرداخت</b>\n"
        "╚══════════════════════╝\n\n"
        f"💰 مبلغ شارژ: <b>{price_fmt(amount)}</b>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "📸 پس از واریز، <b>عکس رسید</b> را در همین چت ارسال کنید:",
        ikb([bbtn("🔙 بازگشت", "back_wallet")])
    )

def handle_wallet_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_wallet_receipt':
        return
    amount = st['amount']
    uname = f"@{message.from_user.username}" if message.from_user.username else "ندارد"
    caption = (
        "💳 <b>درخواست شارژ کیف پول</b>\n\n"
        f"👤 {message.from_user.first_name} | {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"💰 مبلغ: <b>{price_fmt(amount)}</b>\n\n"
        f"✅ برای تایید، مبلغ را ریپلای کنید: <code>{amount}</code>"
    )
    try:
        sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        req_id = db.save_wallet_request(uid, amount)
        db.set_wallet_request_msg(req_id, sent.message_id)
        st['state'] = 'done'
        bot.send_message(uid,
            "✅ <b>رسید شارژ ثبت شد!</b>\n\n"
            "⏳ پس از تایید ادمین، موجودی اضافه می‌شود.",
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
    me = bot.get_me()
    ref_link = f"https://t.me/{me.username}?start={user['referral_code']}"

    rows = []
    for p in purchases:
        rows.append([gbtn(f"📦 {p['config_name']} — {p['plan_name']}", f"reconfig_{p['id']}")])
    rows.append([bbtn("🔙 بازگشت", "back_main")])

    send_msg(chat_id,
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
        bot.answer_callback_query(call.id, "⏳ کانفیگ هنوز ارسال نشده!", show_alert=True)
        return
    bot.answer_callback_query(call.id, "✅ ارسال شد")
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
    if req:
        txt = (message.text or "").strip().replace(",", "").replace("،", "")
        if not txt.isdigit():
            bot.reply_to(message, "❌ فقط عدد مبلغ را ریپلای کنید.\nمثال: <code>150000</code>", parse_mode="HTML")
            return
        amount = int(txt)
        db.add_wallet(req['uid'], amount)
        db.confirm_wallet_request(req['id'])
        try:
            new_balance = db.get_user(req['uid'])['wallet']
            bot.send_message(req['uid'],
                f"✅ <b>کیف پول شارژ شد!</b>\n\n"
                f"💰 مبلغ اضافه‌شده: <b>{price_fmt(amount)}</b>\n"
                f"👛 موجودی جدید: <b>{price_fmt(new_balance)}</b>",
                parse_mode="HTML", reply_markup=main_menu())
            bot.reply_to(message,
                f"✅ کیف پول کاربر <code>{req['uid']}</code> به مبلغ {price_fmt(amount)} شارژ شد.",
                parse_mode="HTML")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: <code>{e}</code>", parse_mode="HTML")
        return

    # ── ارسال کانفیگ ──
    purchase = db.get_purchase_by_group_msg(replied_id)
    if purchase:
        user_id = purchase['uid']
        intro = "✅ <b>کانفیگ شما آماده است:</b>\n\n"
        try:
            ct = message.content_type
            if ct == 'text':
                db.save_config_to_purchase(purchase['id'], message.text)
                bot.send_message(user_id, intro + message.text, parse_mode="HTML")
            elif ct == 'photo':
                caption = message.caption or ""
                if caption:
                    db.save_config_to_purchase(purchase['id'], caption)
                bot.send_photo(user_id, message.photo[-1].file_id,
                               caption=intro + caption, parse_mode="HTML")
            elif ct == 'document':
                caption = message.caption or ""
                if caption:
                    db.save_config_to_purchase(purchase['id'], caption)
                bot.send_document(user_id, message.document.file_id,
                                  caption=intro + caption, parse_mode="HTML")
            else:
                bot.copy_message(user_id, GROUP_ID, message.message_id)

            bot.reply_to(message,
                f"✅ کانفیگ به کاربر <code>{user_id}</code> ارسال شد.", parse_mode="HTML")
            bot.send_message(user_id,
                "🎉 <b>ممنون از خرید شما!</b>\n\n"
                f"📦 پلن: {purchase['plan_name']}\n"
                "در صورت مشکل با پشتیبانی در تماس باشید. 🙏",
                parse_mode="HTML")
            check_referral_reward(user_id, purchase['plan_name'], purchase['config_name'])
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: <code>{e}</code>", parse_mode="HTML")

# ═════════════════════════════════════════════
# اجرا
# ══════════════════════════════════════════════
if __name__ == "__main__":
    db.init_db()
    print("🤖 Bot started...")
    bot_thread = Thread(target=lambda: bot.infinity_polling(timeout=60, long_polling_timeout=60), daemon=True)
    bot_thread.start()
    app.run(host='0.0.0.0', port=7860)
