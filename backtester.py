import pandas as pd
import numpy as np
from indicators import calculate_atr_stop

def run_backtest(ticker, multiplier, reward_ratio):
    try:
        df = calculate_atr_stop(ticker, multiplier=multiplier)
        df = df.dropna(subset=['Close', 'Trailing_Stop'])
        if len(df) < 20: return {"PF": 0, "MDD": 100}
        
        df['Returns'] = df['Close'].pct_change().fillna(0)
        
        cumulative = (1 + df['Returns']).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        mdd = abs(drawdown.min()) * 100
        
        wins = df[df['Returns'] > 0]['Returns'].sum()
        losses = abs(df[df['Returns'] < 0]['Returns'].sum())
        pf = wins / losses if losses != 0 else 99.9
        
        return {"PF": round(float(pf), 2), "MDD": round(float(mdd), 2)}
    except:
        return {"PF": 0, "MDD": 100}

def optimize_params(ticker):
    # 設定預設值，確保永遠回傳正確結構
    best_params = {"Multiplier": 2.0, "RewardRatio": 2.0, "PF": 0, "MDD": 100}
    best_pf = -1
    
    for m in [1.5, 2.0, 2.5]:
        for r in [1.0, 1.5, 2.0, 2.5]:
            metrics = run_backtest(ticker, m, r)
            # 尋找 PF 較高且 MDD 在 20% 以內的參數
            if metrics['PF'] > best_pf and metrics['MDD'] < 20:
                best_pf = metrics['PF']
                best_params = {"Multiplier": m, "RewardRatio": r, **metrics}
            
    return best_params