
import os
import json
import urllib.request
from datetime import datetime, timezone

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

POOL = "EQAJ_seDWXCvKh7zObjzByO4quyDzAcaZjRgsmTnyMumXR1H"

def get_data():
    url = f"https://api.geckoterminal.com/api/v2/networks/ton/pools/{POOL}"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read())

    return result["data"]["attributes"]

def publish():
    data = get_data()

    price = float(data["base_token_price_usd"])
    changes = data.get("price_change_percentage", {})
    volume = data.get("volume_usd", {})

    change_5m = float(changes.get("m5") or 0)
    change_1h = float(changes.get("h1") or 0)
    change_24h = float(changes.get("h24") or 0)

    liquidity = float(data.get("reserve_in_usd") or 0)
    volume_24h = float(volume.get("h24") or 0)

    def trend(value):
        return ("🟢 +" if value >= 0 else "🔴 ") + f"{value:.2f}%"

    now = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    message = (
        f"💰 </b> ${price:.8f}\n\n"
        f"⏱ <b>5 минут:</b> {trend(change_5m)}\n"
        f"🕐 <b>1 час:</b> {trend(change_1h)}\n"
        f"📊 <b>24 часа:</b> {trend(change_24h)}\n\n"
        f"💧 <b>Ликвидность:</b> ${liquidity:,.2f}\n"
        f"📈 <b>Объём за 24ч:</b> ${volume_24h:,.2f}\n\n"
        "🔗 <a href='https://www.geckoterminal.com/ton/pools/"
        f"{POOL}'>Открыть график LOOT</a>\n\n"
        f"🕒 {now}\n"
    )

    telegram_url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    )

    payload = json.dumps({
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).encode("utf-8")

    request = urllib.request.Request(
        telegram_url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        result = json.loads(response.read())

    if not result.get("ok"):
        raise RuntimeError("Telegram publication failed")

    print("LOOT price published successfully")

if __name__ == "__main__":
    publish()
