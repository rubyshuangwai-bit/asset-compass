import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. 页面基础设置 ---
st.set_page_config(
    page_title="全球资产罗盘 Pro",
    page_icon="🧭",
    layout="wide"
)

# --- 2. 侧边栏（用户输入区） ---
st.sidebar.header("🧭 罗盘控制台")
st.sidebar.write("输入想要查询的资产代码")

# 默认值设为 NVDA，用户可以改
symbol_input = st.sidebar.text_input("资产代码 (Yahoo Finance格式)", value="NVDA")
market_type = st.sidebar.selectbox("市场类型", ["美股 (US)", "港股 (HK)", "A股 (CN)"])

# 一个简单的映射逻辑，帮用户自动补全后缀（针对 Yahoo 数据源）
# 如果你是自己的数据源，这段逻辑可以改
final_symbol = symbol_input.strip().upper()
if market_type == "港股 (HK)" and not final_symbol.endswith(".HK"):
    final_symbol += ".HK"
elif market_type == "A股 (CN)":
    if final_symbol.startswith("6"): final_symbol += ".SS"
    elif final_symbol.startswith("0") or final_symbol.startswith("3"): final_symbol += ".SZ"

search_btn = st.sidebar.button("开始分析 🚀")

# --- 3. 主界面逻辑 ---
st.title(f"全球资产罗盘: {final_symbol}")

# 定义一个获取数据的函数，并加上缓存装饰器（为了速度）
@st.cache_data(ttl=60) # 数据缓存60秒
def fetch_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # 获取历史数据
        hist = ticker.history(period="1mo") # 最近1个月
        # 获取基本信息
        info = ticker.info
        return hist, info
    except Exception as e:
        return None, None

# 只有点击按钮，或者刚进来时，才执行
if search_btn or final_symbol:
    with st.spinner('正在连接全球交易所数据...'):
        df, info = fetch_data(final_symbol)

    if df is not None and not df.empty:
        # --- A. 顶部核心指标卡片 ---
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change = current_price - prev_price
        pct_change = (change / prev_price) * 100
        
        # 获取名称，如果获取不到就用代码代替
        asset_name = info.get('longName', final_symbol)

        st.subheader(f"当前概览: {asset_name}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("最新价格", f"{current_price:.2f}", f"{pct_change:.2f}%")
        with col2:
            st.metric("最高价 (近1月)", f"{df['High'].max():.2f}")
        with col3:
            st.metric("最低价 (近1月)", f"{df['Low'].min():.2f}")

        st.divider() # 分割线

        # --- B. 交互式走势图 ---
        st.subheader("📈 价格走势 (30天)")
        st.line_chart(df['Close'])

        # --- C. 数据详情表 ---
        with st.expander("查看详细历史数据"):
            st.dataframe(df.sort_index(ascending=False)) # 倒序排列

    else:
        st.error(f"❌ 未找到代码为 {final_symbol} 的数据，请检查输入是否正确。")
        st.info("提示：美股直接输代码(如 AAPL)，港股需确保代码正确(如 0700.HK)。")
