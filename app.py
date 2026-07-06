import streamlit as st
import plotly.graph_objects as go
from indicators import calculate_atr_stop, get_trading_signal
from backtester import optimize_params

st.set_page_config(page_title="全自動股票監測系統", layout="wide")

# 初始化 Session State
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

st.title("📈 全自動股票趨勢監測系統")

st.sidebar.header("系統輸入")
ticker = st.sidebar.text_input("輸入股票代號:", value="2330")
entry_price = st.sidebar.number_input("進場成本:", min_value=0.0, value=100.0)

# 執行全自動分析按鈕
if st.sidebar.button("執行全自動分析與優化"):
    with st.spinner('正在分析中...'):
        try:
            # 1. 取得最佳參數
            best = optimize_params(ticker)
            m = float(best.get('Multiplier', 2.0))
            r = float(best.get('RewardRatio', 2.0))
            
            # 2. 計算指標
            df = calculate_atr_stop(ticker, multiplier=m)
            signal = get_trading_signal(df)
            
            # 3. 動態抓取 ATR 欄位名稱 (避免欄位找不到)
            atr_cols = [c for c in df.columns if 'ATR' in c.upper()]
            if not atr_cols:
                st.error("系統找不到 ATR 欄位，請檢查 indicators.py")
                st.stop()
            atr_col = atr_cols[0]
            
            # 4. 清除空值並取得最後一行
            clean_df = df.dropna(subset=['Close', 'Trailing_Stop', atr_col])
            
            if clean_df.empty:
                st.error("沒有足夠的資料可供分析。")
            else:
                last_row = clean_df.iloc[-1]
                stop_price = float(last_row['Trailing_Stop'])
                atr_val = float(last_row[atr_col])
                
                st.session_state.analysis_results = {
                    "df": df, 
                    "signal": signal,
                    "curr_price": float(last_row['Close']),
                    "stop_price": stop_price,
                    "take_profit": entry_price + ((entry_price - stop_price) * r),
                    "entry_low": stop_price,
                    "entry_high": stop_price + (atr_val * 0.5),
                    "params": best
                }
        except Exception as e:
            st.error(f"分析失敗: {e}")

# 顯示分析結果
if st.session_state.analysis_results:
    res = st.session_state.analysis_results
    p = res['params']
    
    # 側邊欄顯示優化數據
    st.sidebar.success(
        f"系統已自動套用：\n\n"
        f"ATR 乘數: {p.get('Multiplier', 2.0)}\n"
        f"損益比: {p.get('RewardRatio', 2.0)}\n"
        f"PF: {p.get('PF', 0)} / MDD: {p.get('MDD', 0)}%"
    )

    # 【版面優化】將指標顯示拆分為更寬的 5 欄
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("目前股價", f"{res['curr_price']:.2f}")
    c2.metric("ATR 停損價", f"{res['stop_price']:.2f}")
    c3.metric("進場下限", f"{res['entry_low']:.2f}")
    c4.metric("進場上限", f"{res['entry_high']:.2f}")
    c5.metric("目標停利價", f"{res['take_profit']:.2f}")

    # 獲利/虧損率移至下方，避免欄位擁擠
    pct_change = ((res['curr_price'] - entry_price) / entry_price * 100)
    st.markdown(f"### 目前獲利/虧損率: :orange[{pct_change:.2f}%]")

    st.subheader("分析結論")
    st.info(res['signal'])

    # 繪圖
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['Close'], name='股價'))
    fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['Trailing_Stop'], name='停損線', line=dict(color='red', dash='dash')))
    fig.add_hline(y=res['take_profit'], line_dash="dash", line_color="orange", annotation_text="停利")
    st.plotly_chart(fig, use_container_width=True)