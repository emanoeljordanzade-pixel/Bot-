import sqlite3

DB_NAME = "bot.db"

def get_db_connection():
    """ایجاد اتصال به دیتابیس با قابلیت دسترسی تردها و خروجی دیکشنری"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # برای اینکه خروجی‌ها به صورت دیکشنری با نام ستون‌ها باشند
    return conn

def init_db():
    """ساخت جداول دیتابیس در صورت عدم وجود"""
    conn = get_db_connection()
    try:
        # جدول کاربران
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                referral_count INTEGER DEFAULT 0,
                rewarded_sets INTEGER DEFAULT 0,
                wallet INTEGER DEFAULT 0
            )
        ''')
        
        # جدول خریدها (سفارشات کانفیگ)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER,
                plan_key TEXT,
                plan_name TEXT,
                price INTEGER,
                config_name TEXT,
                wallet_paid INTEGER, -- 1 برای کیف پول، 0 برای کارت به کارت
                discount INTEGER,
                group_msg_id INTEGER,
                config_data TEXT DEFAULT NULL
            )
        ''')
        
        # جدول درخواست‌های شارژ کیف پول
        conn.execute('''
            CREATE TABLE IF NOT EXISTS wallet_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid INTEGER,
                amount INTEGER,
                group_msg_id INTEGER,
                status TEXT DEFAULT 'pending'
            )
        ''')
        conn.commit()
    finally:
        conn.close()

# ══════════════════════════════════════════════
# بخش مدیریت کاربران و زیرمجموعه‌گیری
# ══════════════════════════════════════════════

def get_user(uid):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM users WHERE uid = ?', (uid,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def create_user(uid, first_name, username, code, referred_by=None):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO users (uid, first_name, username, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (uid, first_name, username, code, referred_by))
        conn.commit()
    finally:
        conn.close()

def get_user_by_referral(ref_code):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM users WHERE referral_code = ?', (ref_code,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def increment_referral_count(referrer_uid):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET referral_count = referral_count + 1 WHERE uid = ?', (referrer_uid,))
        conn.commit()
        row = conn.execute('SELECT referral_count, rewarded_sets FROM users WHERE uid = ?', (referrer_uid,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def mark_rewarded_set(referrer_uid):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET rewarded_sets = rewarded_sets + 1 WHERE uid = ?', (referrer_uid,))
        conn.commit()
    finally:
        conn.close()

def get_all_users():
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT uid FROM users').fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

# ══════════════════════════════════════════════
# بخش مدیریت کیف پول
# ══════════════════════════════════════════════

def deduct_wallet(uid, final_price):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET wallet = wallet - ? WHERE uid = ?', (final_price, uid))
        conn.commit()
    finally:
        conn.close()

def add_wallet(uid, confirmed_amount):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET wallet = wallet + ? WHERE uid = ?', (confirmed_amount, uid))
        conn.commit()
    finally:
        conn.close()

def save_wallet_request(uid, amount):
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO wallet_requests (uid, amount)
            VALUES (?, ?)
        ''', (uid, amount))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def set_wallet_request_msg(req_id, msg_id):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE wallet_requests SET group_msg_id = ? WHERE id = ?', (msg_id, req_id))
        conn.commit()
    finally:
        conn.close()

def get_wallet_request_by_group_msg(replied_id):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM wallet_requests WHERE group_msg_id = ? AND status = "pending"', (replied_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def confirm_wallet_request(req_id):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE wallet_requests SET status = "confirmed" WHERE id = ?', (req_id,))
        conn.commit()
    finally:
        conn.close()

# ══════════════════════════════════════════════
# بخش مدیریت خریدها و کانفیگ‌ها
# ══════════════════════════════════════════════

def save_purchase(uid, plan_key, plan_name, final_price, config_name, wallet_paid, discount, group_msg_id):
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO purchases (uid, plan_key, plan_name, price, config_name, wallet_paid, discount, group_msg_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (uid, plan_key, plan_name, final_price, config_name, 1 if wallet_paid else 0, discount, group_msg_id))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def set_purchase_group_msg(purchase_id, msg_id):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE purchases SET group_msg_id = ? WHERE id = ?', (msg_id, purchase_id))
        conn.commit()
    finally:
        conn.close()

def save_config_to_purchase(purchase_id, config_link):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE purchases SET config_data = ? WHERE id = ?', (config_link, purchase_id))
        conn.commit()
    finally:
        conn.close()

def get_purchases_by_user(uid):
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT * FROM purchases WHERE uid = ?', (uid,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_purchase_by_id(purchase_id):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM purchases WHERE id = ?', (purchase_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_purchase_by_group_msg(replied_id):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM purchases WHERE group_msg_id = ?', (replied_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
    finally:
        conn.close()

# ══════════════════════════════════════════════
# بخش مدیریت کیف پول
# ══════════════════════════════════════════════

def deduct_wallet(uid, final_price):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET wallet = wallet - ? WHERE uid = ?', (final_price, uid))
        conn.commit()
    finally:
        conn.close()

def add_wallet(uid, confirmed_amount):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET wallet = wallet + ? WHERE uid = ?', (confirmed_amount, uid))
        conn.commit()
    finally:
        conn.close()

def save_wallet_request(uid, amount):
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO wallet_requests (uid, amount)
            VALUES (?, ?)
        ''', (uid, amount))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def set_wallet_request_msg(req_id, msg_id):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE wallet_requests SET group_msg_id = ? WHERE id = ?', (msg_id, req_id))
        conn.commit()
    finally:
        conn.close()

def get_wallet_request_by_group_msg(replied_id):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM wallet_requests WHERE group_msg_id = ? AND status = "pending"', (replied_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def confirm_wallet_request(req_id):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE wallet_requests SET status = "confirmed" WHERE id = ?', (req_id,))
        conn.commit()
    finally:
        conn.close()

# ══════════════════════════════════════════════
# بخش مدیریت خریدها و کانفیگ‌ها
# ══════════════════════════════════════════════

def save_purchase(uid, plan_key, plan_name, final_price, config_name, wallet_paid, discount, group_msg_id):
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO purchases (uid, plan_key, plan_name, price, config_name, wallet_paid, discount, group_msg_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (uid, plan_key, plan_name, final_price, config_name, 1 if wallet_paid else 0, discount, group_msg_id))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def set_purchase_group_msg(purchase_id, msg_id):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE purchases SET group_msg_id = ? WHERE id = ?', (msg_id, purchase_id))
        conn.commit()
    finally:
        conn.close()

def save_config_to_purchase(purchase_id, config_link):
    conn = get_db_connection()
    try:
        conn.execute('UPDATE purchases SET config_data = ? WHERE id = ?', (config_link, purchase_id))
        conn.commit()
    finally:
        conn.close()

def get_purchases_by_user(uid):
    conn = get_db_connection()
    try:
        rows = conn.execute('SELECT * FROM purchases WHERE uid = ?', (uid,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_purchase_by_id(purchase_id):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM purchases WHERE id = ?', (purchase_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_purchase_by_group_msg(replied_id):
    conn = get_db_connection()
    try:
        row = conn.execute('SELECT * FROM purchases WHERE group_msg_id = ?', (replied_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
