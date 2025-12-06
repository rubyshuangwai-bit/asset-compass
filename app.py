import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. 页面配置 ---
st.set_page_config(page_title="全球资产罗盘 Pro", layout="wide", page_icon="🧭")
st.title("🧭 全球资产罗盘 Pro")
st.markdown("### 🌐 一站式统计美股、港股、A股资产")

# --- 2. 核心函数 ---
@st.cache_data(ttl=300) 
def get_exchange_rates():
    """获取汇率"""
    try:
        tickers = ["CNY=X", "HKD=X"]
        data = yf.download(tickers, period="1d")['Close'].iloc[-1]
        usd_to_cny = data['CNY=X']
        hkd_to_cny = (1 / data['HKD=X']) * usd_to_cny
        return usd_to_cny, hkd_to_cny
    except:
        return 7.25, 0.93 

@st.cache_data(ttl=60)
def fetch_prices(symbols):
    """获取股价"""
    if not symbols: return {}
    try:
        df = yf.download(symbols, period="1d")['Close']
        if isinstance(df, pd.Series): return {symbols[0]: df.iloc[-1]}
        return df.iloc[-1].to_dict()
    except:
        return {}

def get_market_type(symbol):
    if symbol.upper().endswith(".HK"): return "HK"
    if symbol.upper().endswith(".SS") or symbol.upper().endswith(".SZ"): return "CN"
    return "US"
# --- 3. 界面与逻辑 ---
st.subheader("1. 配置持仓")

default_data = [
    {"代码": "NVDA", "名称": "英伟达", "成本": 100.0, "持仓数": 10},
    {"代码": "0700.HK", "名称": "腾讯", "成本": 350.0, "持仓数": 100},
]

edited_df = st.data_editor(
    default_data, num_rows="dynamic",
    column_config={
        "代码": st.column_config.TextColumn(required=True),
        "成本": st.column_config.NumberColumn(format="%.2f"),
        "持仓数": st.column_config.NumberColumn(format="%d"),
    }, hide_index=True
)

if st.button("开始计算 💰", type="primary"):
    with st.spinner('计算中...'):
        portfolio = pd.DataFrame(edited_df)
        if not portfolio.empty:
            # 准备数据
            portfolio["代码"] = portfolio["代码"].astype(str).str.strip().str.upper()
            symbols = portfolio["代码"].tolist()
            usd_cny, hkd_cny = get_exchange_rates()
            current_prices = fetch_prices(symbols)
            
            results = []
            total_assets = 0
            total_profit = 0
            
            # 循环计算
            for i, row in portfolio.iterrows():
                symbol = row['代码']
                cost = row['成本']
                shares = row['持仓数']
                price = current_prices.get(symbol, 0)
                if pd.isna(price): price = 0
                
                # 汇率处理
                mkt = get_market_type(symbol)
                rate = usd_cny if mkt == "US" else (hkd_cny if mkt == "HK" else 1.0)
                
                # 算钱
                val_cny = price * shares * rate
                prof_cny = (price - cost) * shares * rate
                
                total_assets += val_cny
                total_profit += prof_cny
                
                results.append({
                    "代码": symbol,
                    "现价": f"{price:.2f}",
                    "市值(CNY)": f"¥{val_cny:.2f}",
                    "盈亏(CNY)": f"¥{prof_cny:.2f}"
                })
            
            # 展示结果
            st.divider()
            c1, c2 = st.columns(2)
            c1.metric("📦 总资产", f"¥{total_assets:,.2f}")
            c2.metric("💰 总盈亏", f"¥{total_profit:+,.2f}")
            st.dataframe(pd.DataFrame(results))
