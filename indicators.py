import yfinance as yf
import pandas as pd

def format_ticker(ticker):
    ticker = str(ticker).strip()
    return ticker if ticker.endswith(('.TW', '.TWO')) else f"{ticker}.TW"

def calculate_atr_stop(ticker, multiplier=2.0, period=14):
    symbol = format_ticker(ticker)
    df = yf.download(symbol, period="1y", auto_adjust=True)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(col).capitalize() for col in df.columns]
    
    # 計算 ATR (手動計算)
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['ATR'] = true_range.rolling(window=period).mean()
    
    df['Trailing_Stop'] = df['Close'] - (multiplier * df['ATR'])
    return df

def get_trading_signal(df):
    # 手動計算 SMA
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_60'] = df['Close'].rolling(window=60).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    # 手動計算 Stochastic (KD)
    low_min = df['Low'].rolling(window=14).min()
    high_max = df['High'].rolling(window=14).max()
    df['K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    df['D'] = df['K'].rolling(window=3).mean()

    curr = df.iloc[-1]
    
    if not (curr['SMA_20'] > curr['SMA_60'] > curr['SMA_200']):
        return "整理區 (趨勢未完全展開)"
    
    if curr['K'] > curr['D']:
        return "強烈買進訊號 (主升段 + 多頭排列 + KD金叉)"
    return "持股續抱 (主升段中)"
