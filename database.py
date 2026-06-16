import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "bot.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # ── کاربران ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid         INTEGER PRIMARY KEY,
            first_name  TEXT,
            username    TEXT,
            wallet      INTEGER DEFAULT 0,
            referral_code   TEXT UNIQUE,
            referred_by     INTEGER,
            referral_count  INTEGER DEFAULT 0,
            rewarded_sets   INTEGER DEFAULT 0,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── خریدها ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            uid             INTEGER,
            plan_key        TEXT,
            plan_name       TEXT,
            price           INTEGER,
            config_name     TEXT,
            wallet_paid     INTEGER DEFAULT 0,
            discount        INTEGER DEFAULT 0,
            group_msg_id    INTEGER,
            config_data     TEXT,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── درخواست‌های شارژ کیف پول ──
    c.execute("""
        CREATE TABLE IF NOT EXISTS wallet_requests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            uid             INTEGER,
            amount          INTEGER,
            group_msg_id    INTEGER,
            confirmed       INTEGER DEFAULT 0,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Initialized successfully.")


# ══════════════════════════════════════════════
# توابع کاربران
# ══════════════════════════════════════════════

def get_user(uid):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE uid=?", (uid,)).fetchone()
    conn.close()
    return dict(user) if user else None


def create_user(uid, first_name, username, referral_code, referred_by=None):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO users (uid, first_name, username, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?)
        """, (uid, first_name, username, referral_code, referred_by))
        conn.commit()
    except Exception as e:
        print(f"[DB create_user error] {e}")
    finally:
        conn.close()


def get_user_by_referral(referral_code):
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE referral_code=?", (referral_code,)).fetchone()
    conn.close()
    return dict(user) if user else None


def add_wallet(uid, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET wallet = wallet + ? WHERE uid=?", (amount, uid))
    conn.commit()
    conn.close()


def deduct_wallet(uid, amount):
    conn = get_conn()
    conn.execute("UPDATE users SET wallet = wallet - ? WHERE uid=?", (amount, uid))
    conn.commit()
    conn.close()


def increment_referral_count(uid):
    conn = get_conn()
    conn.execute("UPDATE users SET referral_count = referral_count + 1 WHERE uid=?", (uid,))
    conn.commit()
    user = conn.execute("SELECT referral_count, rewarded_sets FROM users WHERE uid=?", (uid,)).fetchone()
    conn.close()
    return dict(user) if user else None


def mark_rewarded_set(uid):
    conn = get_conn()
    conn.execute("UPDATE users SET rewarded_sets = rewarded_sets + 1 WHERE uid=?", (uid,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════
# توابع خریدها
# ══════════════════════════════════════════════

def save_purchase(uid, plan_key, plan_name, price, config_name, wallet_paid, discount, group_msg_id):
    conn = get_conn()
    c = conn.execute("""
        INSERT INTO purchases (uid, plan_key, plan_name, price, config_name, wallet_paid, discount, group_msg_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, plan_key, plan_name, price, config_name, int(wallet_paid), discount, group_msg_id))
    purchase_id = c.lastrowid
    conn.commit()
    conn.close()
    return purchase_id


def save_config_to_purchase(purchase_id, config_data):
    conn = get_conn()
    conn.execute("UPDATE purchases SET config_data=? WHERE id=?", (config_data, purchase_id))
    conn.commit()
    conn.close()


def get_purchase_by_id(purchase_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_purchase_by_group_msg(group_msg_id):
    """گرفتن خرید بر اساس آیدی پیام گروه — برای ری‌استارت‌پروف بودن"""
    conn = get_conn()
    row = conn.execute("SELECT * FROM purchases WHERE group_msg_id=?", (group_msg_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_purchases_by_user(uid):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM purchases WHERE uid=? ORDER BY created_at DESC", (uid,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════
# توابع کیف پول
# ══════════════════════════════════════════════

def save_wallet_request(uid, amount):
    conn = get_conn()
    c = conn.execute(
        "INSERT INTO wallet_requests (uid, amount) VALUES (?, ?)", (uid, amount)
    )
    req_id = c.lastrowid
    conn.commit()
    conn.close()
    return req_id


def set_wallet_request_msg(req_id, group_msg_id):
    conn = get_conn()
    conn.execute("UPDATE wallet_requests SET group_msg_id=? WHERE id=?", (group_msg_id, req_id))
    conn.commit()
    conn.close()


def get_wallet_request_by_group_msg(group_msg_id):
    """گرفتن درخواست شارژ بر اساس آیدی پیام گروه — ری‌استارت‌پروف"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM wallet_requests WHERE group_msg_id=? AND confirmed=0", (group_msg_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def confirm_wallet_request(req_id):
    conn = get_conn()
    conn.execute("UPDATE wallet_requests SET confirmed=1 WHERE id=?", (req_id,))
    conn.commit()
    conn.close()
    cur.execute("""
        INSERT INTO purchases (uid, plan_key, plan_name, plan_price, config_name, paid_from_wallet, discount_pct, group_msg_id)
        VALUES (?,?,?,?,?,?,?,?)
    """, (uid, plan_key, plan_name, plan_price, config_name, int(paid_from_wallet), discount_pct, group_msg_id))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def get_purchase_by_group_msg(group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE group_msg_id=?", (group_msg_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def save_config_to_purchase(purchase_id, config_data):
    conn = get_conn()
    conn.execute("UPDATE purchases SET config_data=? WHERE id=?", (config_data, purchase_id))
    conn.commit()
    conn.close()

def get_purchases_by_user(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE uid=? ORDER BY purchased_at DESC", (uid,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_purchase_by_id(purchase_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE id=?", (purchase_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def save_wallet_request(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO wallet_requests (uid, amount) VALUES (?,?)", (uid, amount))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def set_wallet_request_msg(request_id, group_msg_id):
    conn = get_conn()
    conn.execute("UPDATE wallet_requests SET group_msg_id=? WHERE id=?", (group_msg_id, request_id))
    conn.commit()
    conn.close()

def get_wallet_request_by_group_msg(group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM wallet_requests WHERE group_msg_id=? AND status='pending'", (group_msg_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def confirm_wallet_request(request_id):
    conn = get_conn()
    conn.execute("UPDATE wallet_requests SET status='confirmed' WHERE id=?", (request_id,))
    conn.commit()
    conn.close()

# ══════════════════════════════════════════════
# توابع جدید برای آمار و پیام همگانی
# ══════════════════════════════════════════════

def get_all_user_ids():
    """برگرداندن آیدی تمام کاربران برای ارسال پیام همگانی"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT uid FROM users")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_stats():
    """آمار کلی ربات"""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM purchases")
    total_purchases = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM purchases WHERE config_data IS NOT NULL")
    confirmed_purchases = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM wallet_requests WHERE status='confirmed'")
    confirmed_wallets = cur.fetchone()[0]

    cur.execute("SELECT SUM(plan_price) FROM purchases WHERE config_data IS NOT NULL")
    total_revenue = cur.fetchone()[0] or 0

    conn.close()
    return {
        "total_users": total_users,
        "total_purchases": total_purchases,
        "confirmed_purchases": confirmed_purchases,
        "confirmed_wallets": confirmed_wallets,
        "total_revenue": total_revenue,
    }
