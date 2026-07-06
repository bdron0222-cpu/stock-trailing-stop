import yfinance as yf
import pandas as pd
import pandas_ta as ta

def format_ticker(ticker):
    ticker = str(ticker).strip()
    return ticker if ticker.endswith(('.TW', '.TWO')) else f"{ticker}.TW"

def calculate_atr_stop(ticker, multiplier=2.0, period=14):
    symbol = format_ticker(ticker)
    df = yf.download(symbol, period="1y", auto_adjust=True)
    
    # 資料清理
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(col).capitalize() for col in df.columns]
    
    # 計算 ATR
    df.ta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=period, append=True)
    
    # 【關鍵強制修正】把任何類似 ATR 的欄位名稱強制改為 'ATR'
    for col in df.columns:
        if 'ATR' in col.upper():
            df = df.rename(columns={col: 'ATR'})
            
    # 計算停損線
    if 'ATR' in df.columns:
        df['Trailing_Stop'] = df['Close'] - (multiplier * df['ATR'])
    else:
        raise ValueError(f"ATR 計算失敗，欄位名稱為: {df.columns.tolist()}")
        
    return df

def get_trading_signal(df):
    df.ta.adx(length=14, append=True)
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=60, append=True)
    df.ta.sma(length=200, append=True)
    df.ta.stoch(append=True)
    return "分析完成"