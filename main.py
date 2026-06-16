from flask import Flask
from threading import Thread
import telebot
from telebot import types
import random
import string
import re
import time
import database as db

# =================== تنظیمات ===================
BOT_TOKEN = "8773215261:AAF67pQ9AHZrzvMOZlNbsnaG2-uoTo3HHyk"
ADMIN_ID = 7374971382
ADMIN_USERNAME = "AIireza_1383"
GROUP_ID = -1004294169429
CARD_NUMBER = "5892101542283284"
CARD_OWNER = "علیرضا وحدانی اصل"

REFERRAL_INVITEE_DISCOUNT = 5   # درصد تخفیف برای دعوت‌شده
REFERRAL_REFERRER_DISCOUNT = 7  # درصد تخفیف برای معرف
REFERRAL_REWARD_EVERY = 10      # هر چند نفر جایزه
REFERRAL_REWARD_GB = 5          # گیگابایت جایزه
# ================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# حالت‌های کاربر در حافظه
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
# دکمه‌های رنگی (Bot API 9.1)
# ══════════════════════════════════════════════

def green_btn(text, callback_data):
    """دکمه سبز"""
    btn = types.InlineKeyboardButton(text, callback_data=callback_data)
    btn.color = "green"
    return btn

def blue_btn(text, callback_data):
    """دکمه آبی"""
    btn = types.InlineKeyboardButton(text, callback_data=callback_data)
    btn.color = "blue"
    return btn

def back_btn(text="🔙 بازگشت", data="back_main"):
    """دکمه بازگشت آبی"""
    btn = types.InlineKeyboardButton(text, callback_data=data)
    btn.color = "blue"
    return btn

# ══════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════
@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.chat.type != 'private':
        return

    uid = message.from_user.id
    user_states.pop(uid, None)

    # بررسی لینک رفرال
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
        "🎁 <b>🎁 🎁 سیستم تخفیف دوستان 🎁 🎁 🎁</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 لینک دعوت اختصاصی تو:\n<code>{ref_link}</code>\n\n"
        f"👥 هر دوستی که با لینک تو بیاد و خرید کنه:\n"
        f" ➡️ <b>دوستت {REFERRAL_INVITEE_DISCOUNT}٪ تخفیف</b> روی اولین خریدش می‌گیره\n"
        f" ➡️ <b>تو {REFERRAL_REFERRER_DISCOUNT}٪ تخفیف</b> روی خرید بعدیت می‌گیری\n\n"
        f"🏆 <b>هر {REFERRAL_REWARD_EVERY} نفر که دعوت کنی و خرید کنن = {REFERRAL_REWARD_GB} گیگابایت رایگان هدیه!</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 از منو زیر شروع کن:"
    )
    bot.send_message(message.chat.id, welcome, parse_mode="HTML", reply_markup=main_menu())

# ══════════════════════════════════════════════
# /stats — آمار (فقط ادمین)
# ══════════════════════════════════════════════
@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    if message.from_user.id != ADMIN_ID:
        return

    stats = db.get_stats()
    text = (
        "📊 <b>آمار ربات</b>\n\n"
        f"👥 تعداد کاربران: <b>{stats['total_users']}</b>\n"
        f"🛒 کل سفارشات: <b>{stats['total_purchases']}</b>\n"
        f"✅ سفارشات تایید شده: <b>{stats['confirmed_purchases']}</b>\n"
        f"💳 شارژ کیف پول تایید شده: <b>{stats['confirmed_wallets']}</b>\n"
        f"💰 درآمد کل: <b>{price_fmt(stats['total_revenue'])}</b>"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ══════════════════════════════════════════════
# /broadcast — ارسال پیام همگانی (فقط ادمین)
# ══════════════════════════════════════════════
@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if message.from_user.id != ADMIN_ID:
        return

    user_states[ADMIN_ID] = {'state': 'waiting_broadcast'}
    bot.send_message(
        message.chat.id,
        "📢 <b>ارسال پیام همگانی</b>\n\n"
        "پیامی که می‌خوای به همه کاربران ارسال بشه رو بنویس:\n"
        "(می‌تونی از HTML استفاده کنی)\n\n"
        "برای لغو: /cancel",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['cancel'])
def cmd_cancel(message):
    uid = message.from_user.id
    if uid in user_states:
        user_states.pop(uid)
        bot.send_message(message.chat.id, "❌ عملیات لغو شد.", reply_markup=main_menu())

# ══════════════════════════════════════════════
# هندلر اصلی پیام‌های پرایوت
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

        # ── پیام همگانی ──
        if state == 'waiting_broadcast' and uid == ADMIN_ID:
            handle_broadcast(message)
            return

        # ── منوی اصلی ──
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

        bot.send_message(uid, "برای شروع /start بزنید یا از منوی پایین استفاده کنید.", reply_markup=main_menu())
        return

    # ── عکس ──
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
# ارسال پیام همگانی
# ══════════════════════════════════════════════
def handle_broadcast(message):
    user_states.pop(ADMIN_ID, None)
    all_users = db.get_all_user_ids()
    total = len(all_users)
    success = 0
    failed = 0

    status_msg = bot.send_message(ADMIN_ID, f"⏳ در حال ارسال به {total} کاربر...")

    for uid in all_users:
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
            time.sleep(0.05)  # جلوگیری از flood
        except Exception:
            failed += 1

    bot.edit_message_text(
        f"✅ <b>ارسال پیام همگانی تمام شد!</b>\n\n"
        f"👥 کل کاربران: <b>{total}</b>\n"
        f"✅ ارسال موفق: <b>{success}</b>\n"
        f"❌ ارسال ناموفق: <b>{failed}</b>",
        ADMIN_ID, status_msg.message_id,
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════
# خرید کانفیگ
# ══════════════════════════════════════════════
def show_plans(chat_id, uid):
    user = db.get_user(uid)
    has_referrer = user['referred_by'] is not None
    markup = types.InlineKeyboardMarkup(row_width=1)

    plan_emojis = ['📦', '📦', '📦', '📦']
    for i, (key, plan) in enumerate(PLANS.items()):
        price = plan['price']
        if has_referrer:
            disc_price = int(price * (1 - REFERRAL_INVITEE_DISCOUNT / 100))
            label = f"{plan_emojis[i]} {plan['name']} ─ {price_fmt(disc_price)} 🎁{REFERRAL_INVITEE_DISCOUNT}٪تخفیف"
        else:
            label = f"{plan_emojis[i]} {plan['name']} ─ {price_fmt(price)}"
        btn = types.InlineKeyboardButton(label, callback_data=f"plan_{key.split('_',1)[1]}")
        btn.color = "green"
        markup.add(btn)

    markup.add(back_btn("🔙 بازگشت", "back_main"))

    note = f"\n🎁 <b>شما {REFERRAL_INVITEE_DISCOUNT}٪ تخفیف دعوت‌شده دارید!</b>" if has_referrer else ""
    bot.send_message(chat_id,
        "💎 <b>پلن‌های موجود (نامحدود):</b>\n\n"
        "✅ تعداد کاربر: <b>نامحدود</b>\n"
        "✅ مدت زمان: <b>نامحدود</b>\n\n"
        "🚀 <b>سازگار با:</b>\n"
        "📶 V2RAY | ⚫ V2BOX\n"
        "🔐 NPVtunnel | 🔐 HIDDEFY\n"
        f"{note}\n\n"
        "👇 پلن مورد نظر خود را انتخاب کنید:",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("plan_"))
def cb_plan(call):
    uid = call.from_user.id
    plan_key = "plan_" + call.data[5:]
    plan = PLANS.get(plan_key)
    if not plan:
        bot.answer_callback_query(call.id, "❌ پلن یافت نشد!")
        return

    user = db.get_user(uid)
    discount = 0
    if user and user['referred_by']:
        discount = REFERRAL_INVITEE_DISCOUNT
    final_price = int(plan['price'] * (1 - discount / 100))

    user_states[uid] = {
        'state': 'waiting_config_name',
        'plan_key': plan_key,
        'discount': discount,
        'final_price': final_price,
    }

    bot.answer_callback_query(call.id, f"✅ {plan['name']} انتخاب شد")

    markup = types.InlineKeyboardMarkup()
    markup.add(back_btn("🔙 بازگشت به پلن‌ها", "back_plans"))

    bot.edit_message_text(
        f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
        "📝 لطفاً یک <b>نام انگلیسی</b> برای کانفیگ خود وارد کنید:\n"
        "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup)

def handle_config_name(message, uid):
    name = message.text.strip()
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9 ]*$', name):
        bot.send_message(uid,
            "❌ نام باید فقط از <b>حروف انگلیسی</b> باشد.\n"
            "مثال: <code>Alireza</code>\n\nدوباره وارد کنید:",
            parse_mode="HTML")
        return

    st = user_states[uid]
    st['config_name'] = name
    plan = PLANS[st['plan_key']]
    final_price = st['final_price']
    user = db.get_user(uid)
    wallet = user['wallet']

    markup = types.InlineKeyboardMarkup(row_width=1)
    if wallet >= final_price:
        btn_wallet = types.InlineKeyboardButton(
            f"💰 پرداخت از کیف پول ({price_fmt(wallet)} موجودی)", callback_data="pay_wallet")
        btn_wallet.color = "green"
        markup.add(btn_wallet)

    btn_card = types.InlineKeyboardButton("💳 پرداخت کارت به کارت", callback_data="pay_card")
    btn_card.color = "green"
    markup.add(btn_card)
    markup.add(back_btn("🔙 بازگشت", "back_plans"))

    disc_txt = f"\n🎁 تخفیف دعوت: <b>{st['discount']}٪</b>" if st['discount'] else ""
    bot.send_message(uid,
        "╔══════════════════════╗\n"
        " 🛒 <b>خلاصه سفارش شما</b>\n"
        "╚══════════════════════╝\n\n"
        f"📦 پلن: <b>{plan['name']}</b>\n"
        f"💰 قیمت اصلی: <b>{price_fmt(plan['price'])}</b>{disc_txt}\n"
        f"✅ مبلغ نهایی: <b>{price_fmt(final_price)}</b>\n"
        f"🏷️ نام کانفیگ: <code>{name}</code>\n"
        f"👛 موجودی کیف پول: <b>{price_fmt(wallet)}</b>\n\n"
        "👇 روش پرداخت را انتخاب کنید:",
        parse_mode="HTML", reply_markup=markup)
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
        bot.answer_callback_query(call.id, "❌ موجودی کافی نیست!")
        return

    db.deduct_wallet(uid, final_price)
    uname = f"@{call.from_user.username}" if call.from_user.username else "ندارد"

    caption = (
        "💰 <b>خرید از کیف پول!</b>\n\n"
        f"📦 پلن: <b>{plan['name']} — {price_fmt(final_price)}</b>\n"
        f"🏷️ نام کانفیگ: <code>{st['config_name']}</code>\n"
        f"👤 نام: <b>{call.from_user.first_name}</b>\n"
        f"🆔 یوزرنیم: {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"💸 مبلغ کسرشده از کیف پول: <b>{price_fmt(final_price)}</b>\n\n"
        "✅ روی این پیام <b>ریپلای</b> کنید تا کانفیگ ارسال شود."
    )

    try:
        sent = bot.send_message(GROUP_ID, caption, parse_mode="HTML")
        purchase_id = db.save_purchase(
            uid, st['plan_key'], plan['name'], final_price,
            st['config_name'], True, st['discount'], sent.message_id
        )
        st['state'] = 'done'
        bot.answer_callback_query(call.id, "✅ پرداخت موفق!")
        bot.edit_message_text(
            "✅ <b>پرداخت از کیف پول انجام شد!</b>\n\n"
            "⏳ ادمین در حال آماده‌سازی کانفیگ شماست...\n"
            "🙏 ممنون از خرید شما!",
            call.message.chat.id, call.message.message_id,
            parse_mode="HTML")
        check_referral_reward(uid, plan['name'], st['config_name'])
    except Exception as e:
        print(f"[ERROR wallet pay] {e}")
        db.add_wallet(uid, final_price)
        bot.answer_callback_query(call.id, "❌ خطا رخ داد، دوباره تلاش کنید.")

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
    markup.add(back_btn("🔙 بازگشت", "back_config_name"))

    bot.edit_message_text(
        "╔══════════════════════╗\n"
        " 💳 <b>اطلاعات پرداخت</b>\n"
        "╚══════════════════════╝\n\n"
        f"💰 مبلغ: <b>{price_fmt(st['final_price'])}</b>\n\n"
        f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
        f"👤 به نام: <b>{CARD_OWNER}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📸 پس از واریز، <b>عکس رسید</b> را در همین چت ارسال کنید:",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup)

def handle_purchase_receipt(message, uid):
    st = user_states.get(uid, {})
    if not st or st.get('state') != 'waiting_receipt':
        return

    plan = PLANS[st['plan_key']]
    config_name = st['config_name']
    user_obj = message.from_user
    uname = f"@{user_obj.username}" if user_obj.username else "ندارد"

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
        sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        db.save_purchase(
            uid, st['plan_key'], plan['name'], st['final_price'],
            config_name, False, st['discount'], sent.message_id
        )
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
            f"🎁 {REFERRAL_REWARD_EVERY - (referral_count % REFERRAL_REWARD_EVERY)} نفر دیگر تا جایزه بعدی!",
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
                    f"👤 کاربر: {uname}\n"
                    f"🔢 آیدی: <code>{referrer_uid}</code>\n"
                    f"👥 تعداد دعوت موفق: <b>{referral_count}</b>\n\n"
                    f"🎁 جایزه: <b>{REFERRAL_REWARD_GB} گیگابایت رایگان</b>\n\n"
                    f"⬇️ ادمین روی این پیام ریپلای کند تا کانفیگ جایزه ارسال شود.",
                    parse_mode="HTML")
            except:
                pass
            try:
                bot.send_message(referrer_uid,
                    f"🏆🎉 <b>تبریک! شما برنده جایزه شدید!</b> 🎉🏆\n\n"
                    f"با دعوت {referral_count} نفر که خرید کردند،\n"
                    f"<b>{REFERRAL_REWARD_GB} گیگابایت رایگان</b> به شما تعلق می‌گیره!\n\n"
                    "⏳ ادمین به زودی کانفیگ جایزه را برایتان ارسال می‌کند.\n\n"
                    "🙏 ممنون که ما را به دوستانتان معرفی کردید! ❤️",
                    parse_mode="HTML")
            except:
                pass

# ══════════════════════════════════════════════
# کیف پول
# ══════════════════════════════════════════════
def show_wallet(chat_id, uid):
    user = db.get_user(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)

    btn_balance = types.InlineKeyboardButton("💰 موجودی", callback_data="wallet_balance")
    btn_balance.color = "green"
    btn_charge = types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge")
    btn_charge.color = "green"
    markup.add(btn_balance, btn_charge)
    markup.add(back_btn("🔙 بازگشت", "back_main"))

    bot.send_message(chat_id,
        f"👛 <b>کیف پول شما</b>\n\n"
        f"💰 موجودی: <b>{price_fmt(user['wallet'])}</b>\n\n"
        "یک گزینه را انتخاب کنید:",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "wallet_balance")
def cb_wallet_balance(call):
    uid = call.from_user.id
    user = db.get_user(uid)
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge")
    btn.color = "green"
    markup.add(btn)
    markup.add(back_btn("🔙 بازگشت", "back_wallet"))
    bot.edit_message_text(
        f"💰 <b>موجودی کیف پول شما:</b>\n\n"
        f"<b>{price_fmt(user['wallet'])}</b>",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "wallet_charge")
def cb_wallet_charge(call):
    uid = call.from_user.id
    user_states[uid] = {'state': 'waiting_wallet_amount'}
    markup = types.InlineKeyboardMarkup()
    markup.add(back_btn("🔙 بازگشت", "back_wallet"))
    bot.edit_message_text(
        "➕ <b>شارژ کیف پول</b>\n\n"
        "💬 مبلغی که می‌خواهی شارژ کنی را <b>به تومان</b> وارد کن:\n"
        "مثال: <code>100000</code>",
        call.message.chat.id, call.message.message_id,
        parse_mode="HTML", reply_markup=markup)

def handle_wallet_amount(message, uid):
    txt = message.text.strip().replace(",", "").replace("،", "")
    if not txt.isdigit() or int(txt) < 10000:
        bot.send_message(uid, "❌ مبلغ نامعتبر. حداقل <b>۱۰,۰۰۰ تومان</b> وارد کنید:", parse_mode="HTML")
        return

    amount = int(txt)
    user_states[uid]['amount'] = amount
    user_states[uid]['state'] = 'waiting_wallet_receipt'

    markup = types.InlineKeyboardMarkup()
    markup.add(back_btn("🔙 بازگشت", "back_wallet"))

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

    amount = st['amount']
    user_obj = message.from_user
    uname = f"@{user_obj.username}" if user_obj.username else "ندارد"

    caption = (
        "💳 <b>درخواست شارژ کیف پول</b>\n\n"
        f"👤 نام: <b>{user_obj.first_name}</b>\n"
        f"🆔 یوزرنیم: {uname}\n"
        f"🔢 آیدی: <code>{uid}</code>\n"
        f"💰 مبلغ درخواستی: <b>{price_fmt(amount)}</b>\n\n"
        f"✅ برای تایید، دقیقاً همین عدد را ریپلای کنید: <code>{amount}</code>"
    )

    try:
        sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        req_id = db.save_wallet_request(uid, amount)
        db.set_wallet_request_msg(req_id, sent.message_id)
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
    user = db.get_user(uid)
    purchases = db.get_purchases_by_user(uid)
    ref_link = f"https://t.me/{bot.get_me().username}?start={user['referral_code']}"

    markup = types.InlineKeyboardMarkup(row_width=1)
    for p in purchases:
        btn = types.InlineKeyboardButton(
            f"📦 {p['config_name']} — {p['plan_name']}",
            callback_data=f"reconfig_{p['id']}"
        )
        btn.color = "green"
        markup.add(btn)
    markup.add(back_btn("🔙 بازگشت", "back_main"))

    bot.send_message(chat_id,
        "👤 <b>حساب کاربری</b>\n\n"
        f"👥 تعداد دعوت موفق: <b>{user['referral_count']}</b>\n"
        f"🛒 تعداد خرید: <b>{len(purchases)}</b>\n"
        f"👛 موجودی: <b>{price_fmt(user['wallet'])}</b>\n\n"
        f"🔗 لینک دعوت:\n<code>{ref_link}</code>\n\n"
        "📋 <b>کانفیگ‌های خریداری‌شده</b> (برای ارسال مجدد کلیک کنید):",
        parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("reconfig_"))
def cb_reconfig(call):
    purchase_id = int(call.data.split("_")[1])
    purchase = db.get_purchase_by_id(purchase_id)
    uid = call.from_user.id

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
    uid = call.from_user.id
    dest = call.data[5:]

    if dest == "main":
        user_states.pop(uid, None)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id,
            "🏠 به منوی اصلی برگشتید.", reply_markup=main_menu())

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
            markup.add(back_btn("🔙 بازگشت به پلن‌ها", "back_plans"))
            bot.edit_message_text(
                f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
                "📝 لطفاً یک <b>نام انگلیسی</b> برای کانفیگ خود وارد کنید:\n"
                "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>",
                call.message.chat.id, call.message.message_id,
                parse_mode="HTML", reply_markup=markup)
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_plans(call.message.chat.id, uid)

    bot.answer_callback_query(call.id)

# ══════════════════════════════════════════════
# ریپلای ادمین در گروه — FIX اصلی
# مشکل: group_msg_to_purchase فقط در RAM بود و با ری‌استارت پاک می‌شد
# راه‌حل: مستقیم از دیتابیس خوندن
# ══════════════════════════════════════════════
@bot.message_handler(
    func=lambda m: m.chat.id == GROUP_ID and m.reply_to_message is not None
)
def handle_group_reply(message):
    replied_id = message.reply_to_message.message_id

    # ── شارژ کیف پول ── (از دیتابیس می‌خونیم، نه RAM)
    req = db.get_wallet_request_by_group_msg(replied_id)
    if req:
        txt = message.text.strip() if message.text else ""
        clean = txt.replace(",", "").replace("،", "")
        if not clean.isdigit():
            bot.reply_to(message, "❌ لطفاً دقیقاً عدد مبلغ را ریپلای کنید.")
            return

        confirmed_amount = int(clean)
        db.add_wallet(req['uid'], confirmed_amount)
        db.confirm_wallet_request(req['id'])

        try:
            bot.send_message(req['uid'],
                f"✅ <b>کیف پول شما شارژ شد!</b>\n\n"
                f"💰 مبلغ اضافه‌شده: <b>{price_fmt(confirmed_amount)}</b>\n"
                f"👛 موجودی جدید: <b>{price_fmt(db.get_user(req['uid'])['wallet'])}</b>",
                parse_mode="HTML", reply_markup=main_menu())
            bot.reply_to(message,
                f"✅ کیف پول کاربر <code>{req['uid']}</code> به مبلغ {price_fmt(confirmed_amount)} شارژ شد.",
                parse_mode="HTML")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا: <code>{e}</code>", parse_mode="HTML")
        return

    # ── ارسال کانفیگ ── (از دیتابیس می‌خونیم، نه RAM)
    purchase = db.get_purchase_by_group_msg(replied_id)
    if purchase:
        user_id = purchase['uid']
        intro = "✅ <b>کانفیگ شما آماده است:</b>\n\n"

        try:
            ct = message.content_type
            if ct == 'text':
                config_text = message.text
                db.save_config_to_purchase(purchase['id'], config_text)
                bot.send_message(user_id, intro + message.text, parse_mode="HTML")

            elif ct == 'photo':
                extra = f"\n\n{message.caption}" if message.caption else ""
                if message.caption:
                    db.save_config_to_purchase(purchase['id'], message.caption)
                bot.send_photo(user_id, message.photo[-1].file_id, caption=intro + extra, parse_mode="HTML")

            elif ct == 'document':
                extra = f"\n\n{message.caption}" if message.caption else ""
                if message.caption:
                    db.save_config_to_purchase(purchase['id'], message.caption)
                bot.send_document(user_id, message.document.file_id, caption=intro + extra, parse_mode="HTML")

            else:
                bot.copy_message(user_id, GROUP_ID, message.message_id)

            bot.reply_to(message,
                f"✅ کانفیگ به کاربر <code>{user_id}</code> ارسال شد.",
                parse_mode="HTML")

            bot.send_message(user_id,
                "🎉 <b>ممنون از خرید شما!</b>\n\n"
                f"📦 پلن: {purchase['plan_name']}\n"
                f"🏷️ نام کانفیگ: {purchase['config_name']}\n\n"
                "در صورت هرگونه مشکل با پشتیبانی در تماس باشید. 🙏",
                parse_mode="HTML")

            check_referral_reward(user_id, purchase['plan_name'], purchase['config_name'])

        except Exception as e:
            bot.reply_to(message, f"❌ خطا: <code>{e}</code>", parse_mode="HTML")
        return

    # اگر پیام ریپلای شده نه خرید بود نه کیف پول
    # (مثلاً ادمین روی پیام دیگری ریپلای زده)

# ─── اجرا ───
if __name__ == "__main__":
    db.init_db()
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🤖 Bot started (polling)...")
    bot.infinity_polling()
