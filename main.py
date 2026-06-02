from flask import Flask
from threading import Thread
import telebot
from telebot import types

# =================== تنظیمات ===================
BOT_TOKEN      = "8773215261:AAF67pQ9AHZrzvMOZlNbsnaG2-uoTo3HHyk"
ADMIN_ID       = 7374971382
ADMIN_USERNAME = "AIireza_1383"
GROUP_ID       = -1003649866579
CARD_NUMBER    = "5892101542283284"
CARD_OWNER     = "علیرضا وحدانی اصل"
# ================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_states       = {}
group_msg_to_user = {}

PLANS = {
    "plan_10gb": {"name": "۱۰ گیگابایت", "price": "۱۷۵,۰۰۰ تومان"},
    "plan_20gb": {"name": "۲۰ گیگابایت", "price": "۳۲۵,۰۰۰ تومان"},
    "plan_30gb": {"name": "۳۰ گیگابایت", "price": "۴۳۰,۰۰۰ تومان"},
    "plan_40gb": {"name": "۴۰ گیگابایت", "price": "۵۶۰,۰۰۰ تومان"},
}

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web():
    app.run(host='0.0.0.0', port=7860)

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 خرید کانفیگ"),
        types.KeyboardButton("👨‍💻 پشتیبانی")
    )
    return markup

# ─── /start ───
@bot.message_handler(commands=['start'])
def cmd_start(message):
    if message.chat.type != 'private':
        return
    user_states.pop(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        f"👋 سلام <b>{message.from_user.first_name}</b> عزیز!\n\n"
        "🎉 به ربات فروش کانفیگ VPN خوش آمدید.\n\n"
        "از منوی زیر یکی را انتخاب کنید 👇",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# ─── انتخاب پلن (Inline button) ───
@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_"))
def cb_plan(call):
    plan = PLANS.get(call.data)
    if not plan:
        bot.answer_callback_query(call.id, "❌ پلن یافت نشد!")
        return
    user_states[call.from_user.id] = {'state': 'waiting_config_name', 'plan_key': call.data}
    bot.answer_callback_query(call.id, f"✅ {plan['name']} انتخاب شد")
    bot.send_message(
        call.message.chat.id,
        f"✅ پلن <b>{plan['name']}</b> انتخاب شد.\n\n"
        "📝 لطفاً یک <b>نام انگلیسی</b> برای کانفیگ خود وارد کنید:\n"
        "⚠️ <i>فقط حروف انگلیسی — مثال: Alireza</i>",
        parse_mode="HTML"
    )

# ─── تمام پیام‌های پرایوت ───
@bot.message_handler(
    func=lambda m: m.chat.type == 'private',
    content_types=['text', 'photo', 'document', 'sticker', 'voice', 'video', 'audio']
)
def handle_private(message):
    uid   = message.from_user.id
    state = user_states.get(uid, {}).get('state', '')

    # ── متن ──
    if message.content_type == 'text':
        txt = message.text.strip()

        if txt == "🛒 خرید کانفیگ":
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(
                types.InlineKeyboardButton("🩵  ۱۰ گیگابایت  ─  ۱۷۵,۰۰۰ تومان", callback_data="plan_10gb"),
                types.InlineKeyboardButton("💙  ۲۰ گیگابایت  ─  ۳۲۵,۰۰۰ تومان", callback_data="plan_20gb"),
                types.InlineKeyboardButton("🩷  ۳۰ گیگابایت  ─  ۴۳۰,۰۰۰ تومان", callback_data="plan_30gb"),
                types.InlineKeyboardButton("❤️‍🔥  ۴۰ گیگابایت  ─  ۵۶۰,۰۰۰ تومان", callback_data="plan_40gb"),
            )
            bot.send_message(
                message.chat.id,
                "💎 <b>پلن‌های موجود (نامحدود):</b>\n\n"
                "✅ تعداد کاربر: <b>نامحدود</b>\n"
                "✅ مدت زمان: <b>نامحدود</b>\n\n"
                "🚀 <b>سازگار با:</b>\n"
                "📶 V2RAY  |  ⚫ V2BOX\n"
                "🔐 NPVtunnel  |  🔐 HIDDEFY\n\n"
                "👇 پلن مورد نظر خود را انتخاب کنید:",
                parse_mode="HTML",
                reply_markup=markup
            )
            return

        if txt == "👨‍💻 پشتیبانی":
            mk = types.InlineKeyboardMarkup()
            mk.add(types.InlineKeyboardButton("💬 ارتباط با پشتیبانی", url=f"https://t.me/{ADMIN_USERNAME}"))
            bot.send_message(
                message.chat.id,
                "👨‍💻 <b>پشتیبانی</b>\n\nبرای سوال یا پیگیری سفارش روی دکمه زیر بزنید:",
                parse_mode="HTML",
                reply_markup=mk
            )
            return

        if state == 'waiting_config_name':
            name = txt
            if not name.replace(" ", "").isascii() or not name.replace(" ", "").isalpha():
                bot.send_message(
                    uid,
                    "❌ نام باید فقط از <b>حروف انگلیسی</b> باشد.\n"
                    "مثال: <code>Alireza</code>\n\nدوباره وارد کنید:",
                    parse_mode="HTML"
                )
                return
            st = user_states[uid]
            st['config_name'] = name
            st['state']       = 'waiting_receipt'
            plan = PLANS[st['plan_key']]
            bot.send_message(
                uid,
                "╔══════════════════════╗\n"
                "       🛒  <b>خلاصه سفارش شما</b>\n"
                "╚══════════════════════╝\n\n"
                f"📦  پلن انتخابی:  <b>{plan['name']}</b>\n"
                f"💰  مبلغ قابل پرداخت:  <b>{plan['price']}</b>\n"
                f"🏷️  نام کانفیگ:  <code>{name}</code>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💳  <b>اطلاعات پرداخت:</b>\n\n"
                f"شماره کارت:\n<code>{CARD_NUMBER}</code>\n"
                f"👤  به نام:  <b>{CARD_OWNER}</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📸  پس از واریز <b>{plan['price']}</b>،\n"
                "عکس رسید پرداخت را در همین چت ارسال کنید.",
                parse_mode="HTML"
            )
            return

        if state == 'waiting_receipt':
            bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> پرداخت را ارسال کنید.", parse_mode="HTML")
            return

        bot.send_message(uid, "برای شروع /start بزنید یا از دکمه‌های منو استفاده کنید.", reply_markup=main_menu())
        return

    # ── عکس رسید ──
    if message.content_type == 'photo':
        if state != 'waiting_receipt':
            bot.send_message(uid, "❌ ابتدا یک پلن انتخاب کنید.", reply_markup=main_menu())
            return
        st          = user_states[uid]
        plan        = PLANS[st['plan_key']]
        config_name = st['config_name']
        user        = message.from_user
        uname       = f"@{user.username}" if user.username else "ندارد"
        caption = (
            "🚨 <b>سفارش جدید دریافت شد!</b>\n\n"
            f"📦 پلن: <b>{plan['name']} — {plan['price']}</b>\n"
            f"🏷️ نام کانفیگ: <a href='tg://user?id={uid}'>{config_name}</a>\n"
            f"👤 نام: <b>{user.first_name}</b>\n"
            f"🆔 یوزرنیم: {uname}\n"
            f"🔢 آیدی: <code>{uid}</code>\n\n"
            "✅ برای ارسال کانفیگ روی این پیام <b>ریپلای</b> کنید."
        )
        try:
            sent = bot.send_photo(GROUP_ID, message.photo[-1].file_id, caption=caption, parse_mode="HTML")
            group_msg_to_user[sent.message_id] = uid
            st['state'] = 'done'
            bot.send_message(
                uid,
                "✅ <b>رسید شما با موفقیت ثبت شد!</b>\n\n"
                "⏳ در حال بررسی توسط ادمین...\n"
                "پس از تایید، کانفیگ برای شما ارسال می‌شود.\n\n"
                "🙏 ممنون از خرید شما!",
                parse_mode="HTML",
                reply_markup=main_menu()
            )
        except Exception as e:
            print(f"[ERROR] {e}")
            bot.send_message(uid, "⚠️ خطا در ثبت سفارش. لطفاً دوباره رسید را ارسال کنید.")
        return

    if state == 'waiting_receipt':
        bot.send_message(uid, "❌ لطفاً فقط <b>عکس رسید</b> پرداخت را ارسال کنید.", parse_mode="HTML")

# ─── ریپلای ادمین در گروه ───
@bot.message_handler(
    func=lambda m: m.chat.id == GROUP_ID and m.reply_to_message is not None
)
def handle_group_reply(message):
    replied_id = message.reply_to_message.message_id
    user_id    = group_msg_to_user.get(replied_id)
    if not user_id:
        return
    intro = "✅ <b>کانفیگ شما آماده است:</b>\n\n"
    try:
        ct = message.content_type
        if ct == 'text':
            bot.send_message(user_id, intro + message.text, parse_mode="HTML")
        elif ct == 'photo':
            extra = f"\n\n{message.caption}" if message.caption else ""
            bot.send_photo(user_id, message.photo[-1].file_id, caption=intro+extra, parse_mode="HTML")
        elif ct == 'document':
            extra = f"\n\n{message.caption}" if message.caption else ""
            bot.send_document(user_id, message.document.file_id, caption=intro+extra, parse_mode="HTML")
        else:
            bot.copy_message(user_id, GROUP_ID, message.message_id)
        bot.reply_to(message, f"✅ کانفیگ به کاربر <code>{user_id}</code> ارسال شد.", parse_mode="HTML")
        group_msg_to_user.pop(replied_id, None)
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: <code>{e}</code>", parse_mode="HTML")

# ─── اجرا ───
if __name__ == "__main__":
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🤖 Bot started (polling)...")
    bot.infinity_polling()
