# ══════════════════════════════════════════════
# توابعی که باید به database.py اضافه شوند
# ══════════════════════════════════════════════

# ۱. گرفتن همه کاربران برای پیام همگانی
def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT uid, first_name, username FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"uid": r[0], "first_name": r[1], "username": r[2]} for r in rows]


# ۲. ذخیره شناسه پیام گروه برای خرید (اگه قبلاً نداری)
def set_purchase_group_msg(purchase_id, group_msg_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE purchases SET group_msg_id = ? WHERE id = ?",
        (group_msg_id, purchase_id)
    )
    conn.commit()
    conn.close()


# ۳. گرفتن خرید با شناسه پیام گروه (اگه قبلاً نداری)
def get_purchase_by_group_msg(group_msg_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM purchases WHERE group_msg_id = ?", (group_msg_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))
    return None


# ۴. گرفتن خرید با آیدی
def get_purchase_by_id(purchase_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM purchases WHERE id = ?", (purchase_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))
    return None
