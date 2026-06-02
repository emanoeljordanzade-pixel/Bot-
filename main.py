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

# =================== متون آموزش ===================

TEXT_V2RAY = (
    "📱 <b>آموزش اتصال با V2RayNG</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "ابتدا لینکی که برایتان فرستادیم را <b>کپی (Copy)</b> کنید.\n"
    "(دستتان را روی لینک نگه دارید و گزینه کپی را بزنید)\n\n"
    "سپس برنامه <b>V2RayNG</b> را باز کنید و مراحل زیر را قدم به قدم انجام دهید:\n\n"
    "1️⃣ روی علامت <b>+</b> (به‌علاوه) در بالای صفحه بزنید.\n\n"
    "2️⃣ گزینه <b>Import config from Clipboard</b>\n"
    "   (وارد کردن کانفیگ از کلیپ‌بورد) را انتخاب کنید.\n\n"
    "3️⃣ روی <b>سه نقطه</b> بالا سمت راست صفحه بزنید.\n\n"
    "4️⃣ گزینه <b>Real delay all configuration</b>\n"
    "   (تاخیر کانفیگ‌های گروه فعلی) را انتخاب کنید.\n"
    "   ⏳ کمی صبر کنید تا جلوی سرورها عددهای <b>سبزرنگ</b> ظاهر شود.\n\n"
    "5️⃣ دوباره روی همان <b>سه نقطه</b> بالا سمت راست بزنید.\n\n"
    "6️⃣ گزینه <b>Sorting by test results</b>\n"
    "   (انتخاب بر اساس نتایج آزمایش) را بزنید.\n"
    "   ✅ با این کار، قوی‌ترین سرورِ آن لحظه به ردیف اول می‌آید.\n\n"
    "7️⃣ روی <b>دایره بزرگ</b> پایین صفحه بزنید تا متصل شوید. 🟢\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "💡 <b>راهنمای حل مشکل کندی سرعت:</b>\n\n"
    "هر وقت سرعت افت کرد، نیازی به دریافت کانفیگ جدید نیست.\n"
    "فقط برنامه را باز کنید و مراحل <b>۳ تا ۶</b> را تکرار کنید.\n"
    "برنامه خودکار بهترین سرور جایگزین را فعال می‌کند.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "📊 همچنین می‌توانید از طریق <b>ساب‌لینک</b> ارسال‌شده،\n"
    "مقدار مصرف و حجم باقی‌مانده را مشاهده کنید."
)

TEXT_V2BOX = (
    "📱 <b>آموزش اتصال با V2Box (از طریق ساب‌لینک)</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "برنامه <b>V2Box</b> را باز کنید و مراحل زیر را دنبال کنید:\n\n"
    "1️⃣ در صفحه اصلی، روی آیکون <b>پروفایل</b> (گوشه پایین) بزنید.\n\n"
    "2️⃣ گزینه <b>Subscriptions</b> (اشتراک‌ها) را انتخاب کنید.\n\n"
    "3️⃣ روی دکمه <b>+</b> (افزودن) بزنید.\n\n"
    "4️⃣ یک نام دلخواه در کادر <b>Name</b> وارد کنید.\n"
    "   (مثال: My VPN)\n\n"
    "5️⃣ <b>ساب‌لینک</b> ارسال‌شده را در کادر <b>URL</b> وارد کنید.\n\n"
    "6️⃣ روی <b>Save</b> (ذخیره) بزنید.\n\n"
    "7️⃣ ⏳ چند ثانیه صبر کنید تا کانفیگ‌ها بارگذاری شوند.\n\n"
    "8️⃣ به صفحه اصلی برگردید.\n"
    "   لیست سرورها را مشاهده می‌کنید.\n\n"
    "9️⃣ روی <b>بهترین سرور</b> (کمترین پینگ) ضربدر بزنید تا انتخاب شود.\n\n"
    "🔟 روی دکمه <b>اتصال</b> در پایین صفحه بزنید. 🟢\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "💡 <b>نکته:</b> برای به‌روزرسانی سرورها، وارد بخش\n"
    "Subscriptions شوید و گزینه <b>Update</b> را بزنید.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "📊 همچنین می‌توانید از طریق <b>ساب‌لینک</b> ارسال‌شده،\n"
    "مقدار مصرف و حجم باقی‌مانده را مشاهده کنید."
)

TEXT_NPV = (
    "📱 <b>آموزش اتصال با NPV Tunnel</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "برنامه <b>NPV Tunnel</b> را باز کنید و مراحل زیر را دنبال کنید:\n\n"
    "1️⃣ در پایین صفحه روی گزینه <b>Subs</b> بزنید.\n\n"
    "2️⃣ روی دکمه <b>+</b> بزنید.\n\n"
    "3️⃣ کادر اول (نام) را <i>اختیاری</i> پر کنید.\n"
    "   (می‌توانید هر نامی مثل My VPN بنویسید)\n\n"
    "4️⃣ در کادر دوم، <b>ساب‌لینک</b> ارسال‌شده را وارد کنید.\n\n"
    "5️⃣ ⏳ چند ثانیه صبر کنید، سپس روی\n"
    "   آیکون <b>ابر ☁️</b> در پایین کادر کلیک کنید تا سرورها بارگذاری شوند.\n\n"
    "6️⃣ روی گزینه <b>Ping</b> بزنید و صبر کنید.\n\n"
    "7️⃣ از لیست، روی سروری که <b>پینگ کمتری</b> دارد کلیک کنید تا انتخاب شود.\n\n"
    "8️⃣ در پایین صفحه روی آیکون <b>خانه 🏠</b> بزنید.\n\n"
    "9️⃣ روی دکمه <b>اتصال</b> بزنید. 🟢\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "💡 <b>نکته:</b> هر بار که کانکشن ضعیف شد،\n"
    "مراحل Ping و انتخاب سرور را تکرار کنید.\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n"
    "📊 همچنین می‌توانید از طریق <b>ساب‌لینک</b> ارسال‌شده،\n"
    "مقدار مصرف و حجم باقی‌مانده را مشاهده کنید."
)

# =================== کیبوردها ===================

def kb_tutorial_menu():
    """منوی اصلی آموزش"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📶 آموزش V2RayNG",      callback_data="tut_v2ray"),
        types.InlineKeyboardButton("⚫ آموزش V2Box",         callback_data="tut_v2box"),
        types.InlineKeyboardButton("🔐 آموزش NPV Tunnel",   callback_data="tut_npv"),
        types.InlineKeyboardButton("📥 دانلود برنامه موردنظر", callback_data="tut_download"),
        types.InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="tut_back_main"),
    )
    return markup

def kb_back_to_tutorial():
    """دکمه بازگشت به منوی آموزش"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔙 بازگشت به آموزش‌ها", callback_data="tut_back"),
    )
    return markup

def kb_download_menu():
    """منوی دانلود برنامه‌ها"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "📶 دانلود V2RayNG",
            url="https://play.google.com/store/apps/details?id=com.v2ray.ang"
        ),
        types.InlineKeyboardButton(
            "⚫ دانلود V2Box",
            url="https://play.google.com/store/apps/details?id=dev.hexasoftware.v2box"
        ),
        types.InlineKeyboardButton(
            "🔐 دانلود NPV Tunnel",
            url="https://play.google.com/store/apps/details?id=com.napsternetlabs.napsternetv"
        ),
        types.InlineKeyboardButton("🔙 بازگشت به آموزش‌ها", callback_data="tut_back"),
    )
    return markup

@app.route('/')
def home():
    return "Bot is running!", 200

def run_web():
    app.run(host='0.0.0.0', port=7860)

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛒 خرید کانفیگ"),
        types.KeyboardButton("👨‍💻 پشتیبانی"),
        types.KeyboardButton("📚 آموزش وصل شدن به کانفیگ"),
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

# ─── Callback آموزش‌ها ───
@bot.callback_query_handler(func=lambda call: call.data.startswith("tut_"))
def cb_tutorial(call):
    bot.answer_callback_query(call.id)
    cid = call.message.chat.id
    mid = call.message.message_id
    data = call.data

    if data == "tut_back" or data == "tut_menu":
        # بازگشت به منوی اصلی آموزش
        bot.edit_message_text(
            chat_id=cid,
            message_id=mid,
            text="📚 <b>آموزش وصل شدن به کانفیگ</b>\n\n"
                 "یکی از گزینه‌های زیر را انتخاب کنید 👇",
            parse_mode="HTML",
            reply_markup=kb_tutorial_menu()
        )

    elif data == "tut_back_main":
        # بازگشت به منوی اصلی ربات
        bot.delete_message(cid, mid)
        bot.send_message(
            cid,
            "به منوی اصلی بازگشتید. 👇",
            reply_markup=main_menu()
        )

    elif data == "tut_v2ray":
        bot.edit_message_text(
            chat_id=cid,
            message_id=mid,
            text=TEXT_V2RAY,
            parse_mode="HTML",
            reply_markup=kb_back_to_tutorial()
        )

    elif data == "tut_v2box":
        bot.edit_message_text(
            chat_id=cid,
            message_id=mid,
            text=TEXT_V2BOX,
            parse_mode="HTML",
            reply_markup=kb_back_to_tutorial()
        )

    elif data == "tut_npv":
        bot.edit_message_text(
            chat_id=cid,
            message_id=mid,
            text=TEXT_NPV,
            parse_mode="HTML",
            reply_markup=kb_back_to_tutorial()
        )

    elif data == "tut_download":
        bot.edit_message_text(
            chat_id=cid,
            message_id=mid,
            text="📥 <b>دانلود برنامه موردنظر</b>\n\n"
                 "روی یکی از گزینه‌های زیر بزنید تا به صفحه دانلود هدایت شوید 👇",
            parse_mode="HTML",
            reply_markup=kb_download_menu()
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

        if txt == "📚 آموزش وصل شدن به کانفیگ":
            bot.send_message(
                message.chat.id,
                "📚 <b>آموزش وصل شدن به کانفیگ</b>\n\n"
                "یکی از گزینه‌های زیر را انتخاب کنید 👇",
                parse_mode="HTML",
                reply_markup=kb_tutorial_menu()
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
