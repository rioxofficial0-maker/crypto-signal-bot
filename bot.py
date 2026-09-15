import time
import requests
import pandas as pd
import ta

TELEGRAM_BOT_TOKEN = "8829400475:AAFsDHzzsU1KznjwD1qKklZjpmF8J0sn-hw"
TELEGRAM_CHAT_ID = "7154715391"
SYMBOL = "BTCUSDT"
TIMEFRAME = "5m"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def fetch_binance_klines(symbol, interval, limit=500):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    res = requests.get(url).json()
    df = pd.DataFrame(res, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df

def analyze_market():
    df = fetch_binance_klines(SYMBOL, TIMEFRAME, limit=500)

    if len(df) < 200:
        print("Waiting for more market data...")
        return

    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)

    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()

    df['vol_avg'] = ta.trend.sma_indicator(df['volume'], window=20)

    latest = df.iloc[-1]

    long_score = 0
    short_score = 0

    if latest['close'] > latest['ema200']:
        long_score += 20
    else:
        short_score += 20

    if latest['close'] <= latest['bb_lower'] and latest['rsi'] < 40:
        long_score += 25
    if latest['close'] >= latest['bb_upper'] and latest['rsi'] > 60:
        short_score += 25

    if latest['volume'] > latest['vol_avg']:
        long_score += 15
        short_score += 15

    if latest['close'] > latest['open']:
        long_score += 10
    else:
        short_score += 10

    current_price = latest['close']

    if long_score >= 60:
        msg = f"🚀 *RIO LONG SIGNAL*\n\nPair: `{SYMBOL}`\nPrice: `{current_price}`\nScore: `{long_score}/100`"
        send_telegram_message(msg)
        print("Long Signal Sent!")

    elif short_score >= 60:
        msg = f"📉 *RIO SHORT SIGNAL*\n\nPair: `{SYMBOL}`\nPrice: `{current_price}`\nScore: `{short_score}/100`"
        send_telegram_message(msg)
        print("Short Signal Sent!")
    else:
        print(f"Market Checked | Price: {current_price} | Long: {long_score} | Short: {short_score}")

# Startup notification
send_telegram_message("🤖 *RIO Crypto Signal Bot Started Successfully on Render!*")
print("Bot running on Render...")

while True:
    try:
        analyze_market()
        time.sleep(60)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
