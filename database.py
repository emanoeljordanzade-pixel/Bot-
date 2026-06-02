import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid             BIGINT PRIMARY KEY,
            first_name      TEXT,
            username        TEXT,
            wallet          INTEGER DEFAULT 0,
            referral_code   TEXT UNIQUE,
            referred_by     BIGINT DEFAULT NULL,
            referral_count  INTEGER DEFAULT 0,
            rewarded_sets   INTEGER DEFAULT 0,
            joined_at       TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id              SERIAL PRIMARY KEY,
            uid             BIGINT,
            plan_key        TEXT,
            plan_name       TEXT,
            plan_price      INTEGER,
            config_name     TEXT,
            paid_from_wallet BOOLEAN DEFAULT FALSE,
            discount_pct    INTEGER DEFAULT 0,
            group_msg_id    INTEGER,
            config_data     TEXT DEFAULT NULL,
            purchased_at    TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS wallet_requests (
            id              SERIAL PRIMARY KEY,
            uid             BIGINT,
            amount          INTEGER,
            group_msg_id    INTEGER DEFAULT NULL,
            status          TEXT DEFAULT 'pending',
            created_at      TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# ─── کاربر ───
def get_user(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE uid=%s", (uid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def create_user(uid, first_name, username, referral_code, referred_by=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (uid, first_name, username, referral_code, referred_by)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (uid) DO NOTHING
    """, (uid, first_name, username, referral_code, referred_by))
    conn.commit()
    cur.close(); conn.close()


def get_user_by_referral(code):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE referral_code=%s", (code,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def add_wallet(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET wallet=wallet+%s WHERE uid=%s", (amount, uid))
    conn.commit()
    cur.close(); conn.close()


def deduct_wallet(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET wallet=wallet-%s WHERE uid=%s", (amount, uid))
    conn.commit()
    cur.close(); conn.close()


def increment_referral_count(referrer_uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET referral_count=referral_count+1 WHERE uid=%s RETURNING referral_count, rewarded_sets", (referrer_uid,))
    row = cur.fetchone()
    conn.commit()
    cur.close(); conn.close()
    return row


def mark_rewarded_set(referrer_uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET rewarded_sets=rewarded_sets+1 WHERE uid=%s", (referrer_uid,))
    conn.commit()
    cur.close(); conn.close()


# ─── خرید ───
def save_purchase(uid, plan_key, plan_name, plan_price, config_name, paid_from_wallet, discount_pct, group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO purchases (uid, plan_key, plan_name, plan_price, config_name, paid_from_wallet, discount_pct, group_msg_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
    """, (uid, plan_key, plan_name, plan_price, config_name, paid_from_wallet, discount_pct, group_msg_id))
    row = cur.fetchone()
    conn.commit()
    cur.close(); conn.close()
    return row['id']


def get_purchase_by_group_msg(group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE group_msg_id=%s", (group_msg_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def save_config_to_purchase(purchase_id, config_data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE purchases SET config_data=%s WHERE id=%s", (config_data, purchase_id))
    conn.commit()
    cur.close(); conn.close()


def get_purchases_by_user(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE uid=%s ORDER BY purchased_at DESC", (uid,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def get_purchase_by_id(purchase_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM purchases WHERE id=%s", (purchase_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


# ─── کیف پول ───
def save_wallet_request(uid, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO wallet_requests (uid, amount) VALUES (%s,%s) RETURNING id", (uid, amount))
    row = cur.fetchone()
    conn.commit()
    cur.close(); conn.close()
    return row['id']


def set_wallet_request_msg(request_id, group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE wallet_requests SET group_msg_id=%s WHERE id=%s", (group_msg_id, request_id))
    conn.commit()
    cur.close(); conn.close()


def get_wallet_request_by_group_msg(group_msg_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM wallet_requests WHERE group_msg_id=%s AND status='pending'", (group_msg_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row


def confirm_wallet_request(request_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE wallet_requests SET status='confirmed' WHERE id=%s", (request_id,))
    conn.commit()
    cur.close(); conn.close()
