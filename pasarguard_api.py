"""
PasarGuard Panel API Client
API مشابه Marzban - FastAPI based panel
"""
import requests
import uuid
import re
import time

PANEL_URL = "https://panel.foodchains.com.tr"
PANEL_USER = "moein"
PANEL_PASS = "P6blW82Wv161!"

# نگاشت پلن به گیگابایت
PLAN_GB = {
    "plan_10gb": 10,
    "plan_20gb": 20,
    "plan_30gb": 30,
    "plan_40gb": 40,
}

_token_cache = {"token": None, "expires": 0}

def get_token() -> str:
    """گرفتن توکن JWT از پنل (کش می‌شه)"""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]

    resp = requests.post(
        f"{PANEL_URL}/api/admin/token",
        data={"username": PANEL_USER, "password": PANEL_PASS},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data["access_token"]
    _token_cache["token"] = token
    _token_cache["expires"] = now + 3600 * 23  # 23 ساعت
    return token

def _headers() -> dict:
    return {"Authorization": f"Bearer {get_token()}"}

def get_inbounds() -> list:
    """گرفتن لیست inbound ها از پنل"""
    resp = requests.get(f"{PANEL_URL}/api/inbounds", headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()

def create_user(config_name: str, plan_key: str, user_uid: int) -> dict:
    """
    ساخت کاربر جدید در پاسارگاد
    برمی‌گردونه: {"username": ..., "subscription_url": ..., "links": [...]}
    """
    gb = PLAN_GB.get(plan_key, 10)
    data_limit_bytes = gb * 1024 * 1024 * 1024  # تبدیل GB به Byte

    # ساخت username یونیک
    clean = re.sub(r'[^a-zA-Z0-9]', '', config_name)[:12] or "user"
    username = f"{clean}_{user_uid}"[:32]

    # گرفتن inboundهای موجود
    try:
        inbounds_data = get_inbounds()
        # ساخت دیکشنری proxies از inbound های فعال
        proxies = {}
        inbounds_tags = {}
        for inb in inbounds_data:
            protocol = inb.get("protocol", "").lower()
            tag = inb.get("tag", "")
            if protocol == "vless":
                proxies["vless"] = {"id": str(uuid.uuid4()), "flow": ""}
                inbounds_tags.setdefault("vless", []).append(tag)
            elif protocol == "vmess":
                proxies["vmess"] = {"id": str(uuid.uuid4())}
                inbounds_tags.setdefault("vmess", []).append(tag)
            elif protocol == "trojan":
                proxies["trojan"] = {"password": str(uuid.uuid4())[:12]}
                inbounds_tags.setdefault("trojan", []).append(tag)
            elif protocol == "shadowsocks":
                proxies["shadowsocks"] = {
                    "password": str(uuid.uuid4())[:16],
                    "method": "chacha20-ietf-poly1305"
                }
                inbounds_tags.setdefault("shadowsocks", []).append(tag)
    except Exception:
        # fallback: vless پیش‌فرض
        proxies = {"vless": {"id": str(uuid.uuid4()), "flow": ""}}
        inbounds_tags = {}

    payload = {
        "username": username,
        "proxies": proxies,
        "inbounds": inbounds_tags,
        "data_limit": data_limit_bytes,
        "data_limit_reset_strategy": "no_reset",
        "status": "active",
        "note": f"TelegramUID:{user_uid}|Plan:{plan_key}|Name:{config_name}",
    }

    resp = requests.post(
        f"{PANEL_URL}/api/users",
        json=payload,
        headers=_headers(),
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()

def get_subscription_url(username: str) -> str:
    """لینک ساب کاربر"""
    resp = requests.get(
        f"{PANEL_URL}/api/users/{username}",
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("subscription_url", "")

def get_user_links(username: str) -> list:
    """لینک‌های کانفیگ مستقیم"""
    resp = requests.get(
        f"{PANEL_URL}/api/users/{username}",
        headers=_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("links", [])
