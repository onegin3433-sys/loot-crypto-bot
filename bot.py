
import os
import json
import random
import urllib.request
import urllib.parse
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

API = "https://api.geckoterminal.com/api/v2"
POOL_ADDRESS = "EQBPTSLamspzALssCkevAbqS2J3GtH7E5Z0tm6XI0DaPyWzE"
NETWORK = "ton"

JOKES = {
    "p1": [
        "Оно живое 😱",
        "Ползёт вверх",
        "Это днище пытается карапкаться",
        "Неужели кто-то откупил 50 gram?",
        "До битка осталось немного",
        "Ой, ну не смеши",
        "С таким ростом иди ка ты на х√й",
        "А нормально расти будем?",
        "Пердёжь в лужу",
        "Матонга!",
    ],
    "p3": [
        "Ну нихера себе",
        "Пошла движуха",
        "А закупаться поздно, нужно было раньше",
        "Пружина сжимается",
        "Иксы неизбежны",
        "Полёт нормальный",
    ],
    "p5": [
        "Я сейчас закончу вообще всё!",
        "Пора стаканить?",
        "Да я сам ох*ел!",
        "Давай, сыночек!!!🚀",
    ],
    "p10": [
        "Это сон что-ли?!",
        "Я всегда говорил, что GRAM лучший альткоин!",
        "Это конечно хорошо, но кто-то тебя по 8 покупал.",
        "Верим в GRAM всем селом 🙏🏻",
    ],
    "p20": [
        "ЭТОГО НЕ МОЖЕТ БЫТЬ, МЫ БОГАТЫ???",
        "*ушел стаканить",
        "НУ НИ*УЯ СЕБЕ🚀🚀🚀",
    ],
    "m1": [
        "Стабильно вниз",
        "Ничего нового",
        "Давай уже нормально шлёпнись",
        "Катемся вниз",
        "Ну падаем и что? Ты удивлён?",
        "🗿🗿🗿",
        "💩💩💩",
        "Уже даже не смешно",
        "Это днище снова падает",
        "Дно неизбежно",
        "Матонга в действии",
    ],
    "m3": [
        "Да ты заеб@л",
        "Гооовноооо",
        "Кто-то застаканил 20 GRAM?",
        "Бесконечное падение",
        "Скидки скидки я слил",
        "Ураааа скидки",
    ],
    "m5": [
        "GRAM не причём, это просто медвежка",
        "Ну а ты на что рассчитывал когда покупал это говно?",
        "Я не хочу даже комментировать эту мразь",
        "Всегда говорил, что GRAM самый ху*вый шмекоин",
        "Го ещё ниже?",
    ],
    "m10": [
        "Ай больно на*уй",
        "Чмо е*аное",
        "Ты же по 8 это покупал?",
        "Дно днище днятина",
        "MTONGA",
    ],
    "m20": [
        "Всё, пи3да, я ливаю науй",
        "Скидки? Или ну его на*уй",
        "Приплыли",
        "Гавно",
    ],
}


def api_get(path, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read())


def discover_pool():
    return POOL_ADDRESS, True


def get_market_data():
    pool_address, is_base = discover_pool()

    result = api_get(
        f"/networks/{NETWORK}/pools/{pool_address}"
    )
    attrs = result["data"]["attributes"]

    price_key = "base_token_price_usd" if is_base else "quote_token_price_usd"
    price = float(attrs[price_key])

    changes = attrs.get("price_change_percentage", {})
    change_5m = float(changes.get("m5") or 0)
    change_24h = float(changes.get("h24") or 0)

    if not is_base:
        change_5m = -change_5m / (1 + change_5m / 100) if change_5m != -100 else 0
        change_24h = -change_24h / (1 + change_24h / 100) if change_24h != -100 else 0

    return pool_address, is_base, price, change_5m, change_24h


def choose_joke(change):
    if change >= 20:
        group = "p20"
    elif change >= 10:
        group = "p10"
    elif change >= 5:
        group = "p5"
    elif change >= 3:
        group = "p3"
    elif change >= 1:
        group = "p1"
    elif change <= -20:
        group = "m20"
    elif change <= -10:
        group = "m10"
    elif change <= -5:
        group = "m5"
    elif change <= -3:
        group = "m3"
    elif change <= -1:
        group = "m1"
    else:
        return None

    return random.choice(JOKES[group])


def make_chart(pool_address, is_base):
    token_side = "base" if is_base else "quote"

    result = api_get(
        f"/networks/{NETWORK}/pools/{pool_address}/ohlcv/minute",
        {
            "aggregate": 1,
            "limit": 60,
            "currency": "usd",
            "token": token_side,
        }
    )

    rows = result.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
    if len(rows) < 2:
        raise RuntimeError("Недостаточно данных для часового графика")

    rows = sorted(rows, key=lambda row: row[0])
    times = [
        datetime.fromtimestamp(row[0], tz=timezone.utc)
        for row in rows
    ]
    closes = [float(row[4]) for row in rows]

    plt.figure(figsize=(10, 5))
    plt.plot(times, closes, linewidth=2)
    plt.title("GRAM / USD — последний час")
    plt.ylabel("Цена, USD")
    plt.xlabel("Время UTC")
    plt.gca().xaxis.set_major_formatter(
        mdates.DateFormatter("%H:%M", tz=timezone.utc)
    )
    plt.grid(True, alpha=0.25)
    plt.tight_layout()

    filename = "gram_chart.png"
    plt.savefig(filename, dpi=150)
    plt.close()

    return filename


def telegram_request(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.loads(response.read())

    if not result.get("ok"):
        raise RuntimeError(f"Telegram error: {result}")

    return result


def send_photo(filename, caption):
    boundary = "----GramBotBoundary"
    body = []

    def add_field(name, value):
        body.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )

    add_field("chat_id", CHAT_ID)
    add_field("caption", caption)

    with open(filename, "rb") as image:
        image_data = image.read()

    body.append(
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="photo"; filename="gram_chart.png"\r\n'
        "Content-Type: image/png\r\n\r\n".encode("utf-8")
        + image_data + b"\r\n"
    )
    body.append(f"--{boundary}--\r\n".encode("utf-8"))

    request = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data=b"".join(body),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
    )

    with urllib.request.urlopen(request, timeout=40) as response:
        result = json.loads(response.read())

    if not result.get("ok"):
        raise RuntimeError(f"Telegram photo error: {result}")

def get_previous_price():
    try:
        with open("previous_price.txt", "r") as file:
            return float(file.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def save_previous_price(price):
    with open("previous_price.txt", "w") as file:
        file.write(f"{price:.2f}")

def get_last_chart_hour():
    try:
        with open("last_chart_hour.txt", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


def save_last_chart_hour(hour):
    with open("last_chart_hour.txt", "w") as file:
        file.write(hour)

def publish():
    pool, is_base, price, change_5m, change_24h = get_market_data()

    dot = "🟢" if change_5m >= 0 else "🔴"
    message = f"${price:.2f} {dot}"

    previous_price = get_previous_price()

    if previous_price is not None and round(price, 2) != previous_price:
        joke = choose_joke(change_24h)
        if joke:
            message += "\n" + joke

    save_previous_price(price)

        now = datetime.now(timezone.utc)
    current_hour = now.strftime("%Y-%m-%d %H")

    if get_last_chart_hour() != current_hour:
        try:
            chart = make_chart(pool, is_base)
            send_photo(chart, message)
            save_last_chart_hour(current_hour)
            print("GRAM hourly chart published")
            return
        except Exception as error:
            print(f"Chart error, sending text instead: {error}")

    telegram_request("sendMessage", {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    })

    print("GRAM price published successfully")


if __name__ == "__main__":
    publish()
    
