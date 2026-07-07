import yfinance as yf
import pandas as pd

def calculate_atr_stop(ticker, multiplier=2.0, period=14):
    symbol = ticker.strip() if "." in ticker else ticker + ".TW"
    df = yf.download(symbol, period="1y", auto_adjust=True)
    
    # 處理 multiindex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(col).capitalize() for col in df.columns]
    
    # 手動計算 ATR (數學公式)
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    df['ATR'] = ranges.max(axis=1).rolling(window=period).mean()
    
    # 計算停損線
    df['Trailing_Stop'] = df['Close'] - (multiplier * df['ATR'])
    return df

def get_trading_signal(df):
    # 手動計算均線與 KD
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_60'] = df['Close'].rolling(window=60).mean()
    # 簡易訊號
    if df['Close'].iloc[-1] > df['SMA_20'].iloc[-1]:
        return "主升段 (趨勢明確)"
    else:
        return "盤整區 (觀察中)"