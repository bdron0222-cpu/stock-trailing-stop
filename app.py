import streamlit as st
import plotly.graph_objects as go
from indicators import calculate_atr_stop, get_trading_signal

st.set_page_config(page_title="全自動股票監測系統", layout="wide")

# 【核心修復】確保初始化在所有判斷之前
if "analysis_results" not in st.session_state: st.session_state.analysis_results = None
if "m" not in st.session_state: st.session_state.m = 2.0
if "r" not in st.session_state: st.session_state.r = 2.0

st.title("📈 股票監測系統")

# --- 參考指引 ---
with st.expander("📊 指標數值參考指引 (必讀)"):
    st.markdown("""
    | 指標 | 盤整區範圍 (Consolidation) | 主升段範圍 (Main Trend) |
    | :--- | :--- | :--- |
    | **ATR** | 低位/水平 (建議數值: 1.0 - 2.0) | 趨勢性擴大 (建議數值: 3.0 - 5.0) |
    | **損益比** | 高要求 (建議數值: > 2.0) | 穩健要求 (建議數值: 1.5 - 2.0) |
    """)

# --- 側邊欄控制 ---
ticker_input = st.sidebar.text_input("股票代號:", value="2330")
entry_price = st.sidebar.number_input("進場成本:", min_value=0.0, value=100.0)
st.session_state.m = st.sidebar.slider("ATR 乘數", 1.0, 5.0, st.session_state.m, 0.1)
st.session_state.r = st.sidebar.slider("損益比", 1.0, 5.0, st.session_state.r, 0.1)

if st.sidebar.button("執行分析"):
    try:
        df = calculate_atr_stop(ticker_input, multiplier=st.session_state.m)
        signal = get_trading_signal(df)
        last_row = df.dropna().iloc[-1]
        
        # 計算結果
        risk = entry_price - float(last_row['Trailing_Stop'])
        take_profit = entry_price + (risk * st.session_state.r)
        
        st.session_state.analysis_results = {
            "df": df, "signal": signal,
            "curr_price": float(last_row['Close']),
            "stop_price": float(last_row['Trailing_Stop']),
            "take_profit": take_profit,
            "atr": float(last_row['ATR'])
        }
    except Exception as e:
        st.error(f"分析失敗: {e}")

# --- 顯示結果 ---
if st.session_state.analysis_results:
    res = st.session_state.analysis_results
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("目前股價", f"{res['curr_price']:.2f}")
    c2.metric("ATR 停損", f"{res['stop_price']:.2f}")
    c3.metric("ATR 數值", f"{res['atr']:.2f}")
    c4.metric("目標停利", f"{res['take_profit']:.2f}")
    
    st.info(f"當前狀態: {res['signal']}")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['Close'], name='股價'))
    fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['Trailing_Stop'], name='停損線'))
    st.plotly_chart(fig, use_container_width=True)