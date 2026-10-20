
import yfinance as yf
import pandas as pd
from datetime import time
from zoneinfo import ZoneInfo

# NSE stocks - initial watchlist
STOCKS = [
    "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS",
    "ITC.NS", "TATAMOTORS.NS", "M&M.NS",
    "BAJFINANCE.NS", "LT.NS", "SUNPHARMA.NS",
    "MARUTI.NS", "BHARTIARTL.NS", "TATASTEEL.NS",
    "ADANIPORTS.NS"
]

TZ = ZoneInfo("Asia/Kolkata")


def check_stock(symbol):
    try:
        df = yf.download(
            symbol,
            period="1d",
            interval="5m",
            progress=False,
            auto_adjust=False
        )

        if df.empty:
            return None

        # Handle Yahoo Finance column format
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna(subset=["Open", "High", "Low", "Close"])

        if df.empty:
            return None

        # Convert timestamps to Indian time
        if df.index.tz is None:
            df.index = df.index.tz_localize(TZ)
        else:
            df.index = df.index.tz_convert(TZ)

        today = df[df.index.date == pd.Timestamp.now(TZ).date()]

        if today.empty:
            return None

        # High-making window: 9:30 AM to 10:30 AM
        setup = today[
            (today.index.time >= time(9, 30)) &
            (today.index.time < time(10, 30))
        ]

        if setup.empty:
            return None

        # Find the highest candle in the setup window
        high_position = setup["High"].values.argmax()
        high_time = setup.index[high_position]
        morning_high = float(setup["High"].iloc[high_position])

        # Red retracement candle must occur AFTER the high
        after_high = setup[setup.index > high_time]
        red_candles = after_high[
            after_high["Close"] < after_high["Open"]
        ]

        if red_candles.empty:
            return None

        # Use the first red candle after the high
        red_time = red_candles.index[0]
        red_high = float(red_candles.iloc[0]["High"])

        # Look for a later 5-minute candle closing above red candle high
        later = today[today.index > red_time]
        breakout = later[later["Close"] > red_high]

        if breakout.empty:
            return None

        signal = breakout.iloc[0]
        signal_time = breakout.index[0]

        return {
            "Stock": symbol,
            "Morning High": round(morning_high, 2),
            "Red Candle High": round(red_high, 2),
            "BUY Close": round(float(signal["Close"]), 2),
            "Signal Time": signal_time.strftime("%H:%M")
        }

    except Exception as e:
        print(f"Error in {symbol}: {e}")
        return None


def main():
    print("\nIntraday Scanner - 9:30 AM to 10:30 AM")
    print("Scanning 5-minute candles...\n")

    results = []

    for symbol in STOCKS:
        result = check_stock(symbol)

        if result:
            results.append(result)
            print("BUY SETUP:", result)

    if results:
        pd.DataFrame(results).to_csv("buy_signals.csv", index=False)
        print("\nSignals saved to buy_signals.csv")
    else:
        print("Abhi koi matching setup nahi mila.")


if __name__ == "__main__":
    main()
