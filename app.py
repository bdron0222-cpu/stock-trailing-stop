import streamlit as st
import plotly.graph_objects as go
from indicators import calculate_atr_stop, get_trading_signal

# 1. 頁面設定
st.set_page_config(page_title="全自動股票監測系統", layout="wide")

# 2. 嚴格初始化 (確保程式穩定)
if "analysis_results" not in st.session_state: st.session_state.analysis_results = None
if "m" not in st.session_state: st.session_state.m = 2.0
if "r" not in st.session_state: st.session_state.r = 2.0

st.title("📈 全自動股票趨勢監測系統")

# 3. 側邊欄控制
st.sidebar.header("系統參數控制")
ticker_input = st.sidebar.text_input("輸入股票代號:", value="2330")
entry_price = st.sidebar.number_input("進場成本:", min_value=0.0, value=100.0)

st.sidebar.subheader("參數微調")
st.session_state.m = st.sidebar.slider("ATR 乘數 (風險係數)", 1.0, 5.0, st.session_state.m, 0.1)
st.session_state.r = st.sidebar.slider("損益比 (Reward Ratio)", 1.0, 5.0, st.session_state.r, 0.1)

# 參考指引區塊
with st.expander("📊 損益比與 ATR 指標參考指引"):
    st.markdown("""
    | 指標 | 盤整區範圍 (Consolidation) | 主升段範圍 (Main Trend) |
    | :--- | :--- | :--- |
    | **ATR 乘數** | 1.0 - 2.0 | 3.0 - 5.0 |
    | **損益比** | > 2.0 | 1.5 - 2.0 |
    """)

# 4. 執行分析
if st.sidebar.button("執行分析"):
    with st.spinner('計算中...'):
        try:
            df = calculate_atr_stop(ticker_input, multiplier=st.session_state.m)
            signal = get_trading_signal(df)
            
            # 取最新數據
            last_row = df.dropna().iloc[-1]
            stop_price = float(last_row['Trailing_Stop'])
            
            # --- 邏輯修正與防呆 ---
            if entry_price <= stop_price:
                st.error(f"⚠️ 參數錯誤：你的進場成本 ({entry_price:.2f}) 低於系統建議的停損線 ({stop_price:.2f})。這會導致停利價計算為負數，請調高進場成本或調整 ATR 乘數。")
            else:
                risk = entry_price - stop_price
                take_profit = entry_price + (risk * st.session_state.r)
                
                st.session_state.analysis_results = {
                    "df": df, "signal": signal,
                    "curr_price": float(last_row['Close']),
                    "stop_price": stop_price,
                    "take_profit": take_profit,
                    "r_ratio": st.session_state.r,
                    "atr": float(last_row['ATR'])
                }
        except Exception as e:
            st.error(f"分析過程發生錯誤: {e}")

# 5. 顯示分析結果
if st.session_state.analysis_results:
    res = st.session_state.analysis_results
    
    # 指標顯示區
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("目前股價", f"{res['curr_price']:.2f}")
    c2.metric("停損價 (ATR)", f"{res['stop_price']:.2f}")
    c3.metric("目標停利", f"{res['take_profit']:.2f}")
    c4.metric("當前 ATR", f"{res['atr']:.2f}")
    
    st.info(f"當前市場狀態: {res['signal']}")

    # 繪圖區
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['Close'], name='股價'))
    fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['Trailing_Stop'], name='停損線', line=dict(color='red', dash='dash')))
    fig.add_hline(y=res['take_profit'], line_dash="dash", line_color="orange", annotation_text="停利")
    st.plotly_chart(fig, use_container_width=True)