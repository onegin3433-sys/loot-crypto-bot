
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

API = "https://api.ston.fi/v1"
POOL_ADDRESS = "EQCGScrZe1xbyWqWDvdI6mzP-GAcAWFv6ZXuaJOuSqemxku4"
USDT_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
TON_ADDRESS = "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c"

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
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; GRAMPriceBot/1.0)",
            "Referer": "https://app.ston.fi/",
            "Origin": "https://app.ston.fi",
        }
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        return json.loads(response.read())


def discover_pool():
    return POOL_ADDRESS, True


def get_market_data():
    result = api_get(f"/pools/{POOL_ADDRESS}")
    pool = result.get("pool", result)

    token0 = pool.get("token0_address")
    token1 = pool.get("token1_address")
    if token0 != USDT_ADDRESS or token1 != TON_ADDRESS:
        raise RuntimeError(
            f"Неверная пара в пуле STON.fi: token0={token0}, token1={token1}"
        )

    reserve_usdt = int(pool["reserve0"]) / (10 ** 6)
    reserve_gram = int(pool["reserve1"]) / (10 ** 9)
    if reserve_usdt <= 0 or reserve_gram <= 0:
        raise RuntimeError("STON.fi вернул пустые резервы пула")

    # Цена GRAM (TON) в USDT по соотношению резервов пула.
    price = reserve_usdt / reserve_gram

    history = load_price_history()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    history.append({"time": now_ts, "price": price})
    history = [
        point for point in history
        if now_ts - point["time"] <= 2 * 60 * 60
    ]
    save_price_history(history)

    return POOL_ADDRESS, True, price, 0.0, 0.0


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


def load_price_history():
    try:
        with open("gram_history.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_price_history(history):
    with open("gram_history.json", "w") as file:
        json.dump(history, file)


def make_chart(pool_address, is_base):
    history = load_price_history()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    history = [
        point for point in history
        if now_ts - point["time"] <= 60 * 60
    ]
    if len(history) < 2 or now_ts - history[0]["time"] < 50 * 60:
        raise RuntimeError("Нужно накопить около часа точек для часового графика")

    history.sort(key=lambda point: point["time"])
    times = [
        datetime.fromtimestamp(point["time"], tz=timezone.utc)
        for point in history
    ]
    closes = [float(point["price"]) for point in history]

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

    # Photo uploads can take longer than ordinary Telegram text requests.
    with urllib.request.urlopen(request, timeout=120) as response:
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
        file.write(f"{price:.12g}")

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

    previous_price = get_previous_price()

    # Compare the same precision that is displayed in Telegram.
    displayed_price = round(price, 2)
    previous_displayed_price = (
        round(previous_price, 2) if previous_price is not None else None
    )

    if previous_displayed_price is None or displayed_price == previous_displayed_price:
        dot = "💎"
    elif displayed_price > previous_displayed_price:
        dot = "📈"
    else:
        dot = "📉"

    message = f"${displayed_price:.2f} {dot}"

    if previous_displayed_price is not None and previous_displayed_price > 0:
        change_percent = (
            (displayed_price - previous_displayed_price)
            / previous_displayed_price
        ) * 100

        if abs(change_percent) >= 1:
            joke = choose_joke(change_percent)
            if joke:
                message += "\n" + joke

    save_previous_price(displayed_price)

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
    
