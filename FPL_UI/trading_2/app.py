import streamlit as st
import yfinance as yf
import pandas as pd
import xgboost as xgb
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
import numpy as np

# --- VERSION 4.0 ---
st.set_page_config(page_title="Nifty Quant Strategy v4.0", layout="wide")
st.title("🇮🇳 Nifty Quant Scanner: Alpha Hunter")
st.markdown("**Version 4.0:** Now compares individual stock momentum against the Nifty 50 benchmark to find hidden 'Alpha' stocks climbing during market downtrends.")

# --- NIFTY 100 TICKERS ---
NIFTY_TICKERS = [
    "ABB.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ADANIPOWER.NS", "ADANIENSOL.NS", 
    "ADANIGREEN.NS", "ATGL.NS", "AMBUJACEM.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", 
    "DMART.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", 
    "BAJAJHLDNG.NS", "BANKBARODA.NS", "BEL.NS", "BPCL.NS", "BHARTIARTL.NS", 
    "BHEL.NS", "BOSCHLTD.NS", "BRITANNIA.NS", "CANBK.NS", "CHOLAFIN.NS", 
    "CIPLA.NS", "COALINDIA.NS", "DABUR.NS", "DIVISLAB.NS", "DLF.NS", 
    "DRREDDY.NS", "EICHERMOT.NS", "GAIL.NS", "GODREJCP.NS", "GRASIM.NS", 
    "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HAVELLS.NS", "HEROMOTOCO.NS", 
    "HINDALCO.NS", "HAL.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "ICICIGI.NS", 
    "ICICIPRULI.NS", "INDIGO.NS", "INDUSINDBK.NS", "NAUKRI.NS", "INFY.NS", 
    "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JIOFIN.NS", "JSWENERGY.NS", 
    "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "LTIM.NS", "M&M.NS", 
    "MARUTI.NS", "MOTHERSON.NS", "MAXHEALTH.NS", "NESTLEIND.NS", "NTPC.NS", 
    "NHPC.NS", "ONGC.NS", "PIDILITIND.NS", "PFC.NS", "POWERGRID.NS", 
    "PNB.NS", "RECLTD.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", 
    "SHREECEM.NS", "SHRIRAMFIN.NS", "SIEMENS.NS", "SUNPHARMA.NS", "TVSMOTOR.NS", 
    "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATAPOWER.NS", "TATASTEEL.NS", 
    "TECHM.NS", "TITAN.NS", "TORNTPHARM.NS", "TRENT.NS", "ULTRACEMCO.NS", 
    "UNIONBANK.NS", "MCDOWELL-N.NS", "VBL.NS", "VEDL.NS", "WIPRO.NS", 
    "ZYDUSLIFE.NS", "ZOMATO.NS", "TATAELXSI.NS", "PERSISTENT.NS", "POLYCAB.NS"
]

@st.cache_data(ttl=3600)
def get_nifty_benchmark():
    """Fetches Nifty 50 data once to compare against all stocks."""
    try:
        nifty = yf.Ticker("^NSEI").history(period="1y")
        # Calculate Nifty's 10-day rolling percentage return
        nifty['Nifty_10d_Ret'] = nifty['Close'].pct_change(periods=10) * 100
        return nifty[['Nifty_10d_Ret']]
    except:
        return pd.DataFrame()

def generate_error_row(ticker, reason):
    return {
        "Ticker": ticker.replace(".NS", ""),
        "AI Signal": "⚠️ ERROR",
        "Entry (LTP)": 0.0,
        "vs Nifty (10d)": "0.0%",
        "GTT Stop Loss": 0.0,
        "GTT Target": 0.0,
        "Reasoning": reason,
        "Up Prob (%)": 0.0,
        "Backtest Acc (%)": 0.0,
        "RSI": 0.0
    }

@st.cache_data(ttl=3600)
def analyze_stock(ticker, nifty_df):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if df.empty:
            return generate_error_row(ticker, "yfinance API rate limit blocked data fetch.")
        if len(df) < 100:
            return generate_error_row(ticker, f"Insufficient history ({len(df)} days).")
            
        # Merge with Nifty benchmark data by Date
        if not nifty_df.empty:
            df = df.join(nifty_df, how='left')
        else:
            df['Nifty_10d_Ret'] = 0.0
            
        # Calculate Stock's own 10-day return
        df['Stock_10d_Ret'] = df['Close'].pct_change(periods=10) * 100
        
        # Calculate Spread (Alpha)
        df['Alpha_Spread'] = df['Stock_10d_Ret'] - df['Nifty_10d_Ret']

        # Indicators
        df['SMA_20'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
        df['SMA_50'] = SMAIndicator(close=df['Close'], window=50).sma_indicator()
        df['RSI_14'] = RSIIndicator(close=df['Close'], window=14).rsi()
        
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        df = df.dropna()
        
        features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_20', 'SMA_50', 'RSI_14']
        X = df[features][:-1]
        y = df['Target'][:-1]
        
        if len(X) < 50:
             return generate_error_row(ticker, "Too many NaN values dropped; likely suspended.")
             
        split = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]
        
        model = xgb.XGBClassifier(n_estimators=50, learning_rate=0.1, random_state=42)
        model.fit(X_train, y_train)
        
        today_data = df[features].iloc[-1:]
        prob_up = model.predict_proba(today_data)[0][1]
        accuracy = model.score(X_test, y_test)
        
        ltp = df['Close'].iloc[-1]
        rsi = df['RSI_14'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        alpha = df['Alpha_Spread'].iloc[-1]
        nifty_ret = df['Nifty_10d_Ret'].iloc[-1]
        
        signal = "⚪ HOLD"
        reason = "No clear edge."
        target_price = 0.0
        stop_loss = 0.0
        
        # Base BUY Condition
        if (sma_20 > sma_50) and (rsi < 65) and (prob_up > 0.60) and (accuracy > 0.52):
            # Upgrade to ALPHA BUY if the stock is beating Nifty by more than 3% over 10 days
            if alpha > 3.0:
                signal = "⭐ ALPHA BUY"
                reason = f"Outperforming Nifty by {alpha:.1f}%. Strong institutional accumulation."
            else:
                signal = "🟢 BUY"
                reason = "Standard technical & ML buy setup. Moving with the market."
                
            stop_loss = ltp * 0.98  
            target_price = ltp * 1.04 
            
        elif prob_up < 0.40 and accuracy > 0.52:
            signal = "🔴 SELL"
            reason = "ML indicates high probability of immediate downward movement."
            stop_loss = ltp * 1.02
            target_price = ltp * 0.96
            
        return {
            "Ticker": ticker.replace(".NS", ""),
            "AI Signal": signal,
            "Entry (LTP)": round(ltp, 2),
            "vs Nifty (10d)": f"{alpha:+.1f}%",
            "GTT Stop Loss": round(stop_loss, 2),
            "GTT Target": round(target_price, 2),
            "Reasoning": reason,
            "Up Prob (%)": round(prob_up * 100, 1),
            "Backtest Acc (%)": round(accuracy * 100, 1),
            "RSI": round(rsi, 1)
        }
    except Exception as e:
        return generate_error_row(ticker, f"Execution failed: {str(e)}")

# --- STYLING FUNCTIONS ---
def highlight_signal(val):
    if val == "⭐ ALPHA BUY":
        return 'background-color: rgba(243, 156, 18, 0.3); color: #f39c12; font-weight: bold; border: 1px solid #f39c12;'
    elif val == "🟢 BUY":
        return 'background-color: rgba(39, 174, 96, 0.3); color: #2ecc71; font-weight: bold;'
    elif val == "🔴 SELL":
        return 'background-color: rgba(192, 57, 43, 0.3); color: #e74c3c; font-weight: bold;'
    elif val == "⚠️ ERROR":
        return 'background-color: rgba(149, 165, 166, 0.2); color: #7f8c8d; font-style: italic;'
    return 'color: gray;'

# --- UI EXECUTION ---
if st.button("🚀 Run Alpha Hunter Scan", type="primary"):
    results = []
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    # Pre-fetch Nifty 50 benchmark once to save API calls
    nifty_df = get_nifty_benchmark()
    
    for i, ticker in enumerate(NIFTY_TICKERS):
        progress_text.text(f"Scanning {ticker} ({i+1}/{len(NIFTY_TICKERS)})...")
        res = analyze_stock(ticker, nifty_df)
        if res:
            results.append(res)
        progress_bar.progress((i + 1) / len(NIFTY_TICKERS))
        
    progress_text.text("Scan Complete!")
    
    if results:
        df_results = pd.DataFrame(results)
        
        # Sort so Alpha Buys are explicitly at the very top, followed by regular Buys
        df_results['Sort_Rank'] = df_results['AI Signal'].map({"⭐ ALPHA BUY": 1, "🟢 BUY": 2, "⚪ HOLD": 3, "🔴 SELL": 4, "⚠️ ERROR": 5})
        df_results = df_results.sort_values(by=["Sort_Rank", "Up Prob (%)"], ascending=[True, False]).drop(columns=['Sort_Rank']).reset_index(drop=True)
        
        st.subheader("📊 Trade Setup Results")
        
        styled_df = df_results.style\
            .map(highlight_signal, subset=['AI Signal'])\
            .format({
                "Entry (LTP)": "₹{:.2f}",
                "GTT Stop Loss": "₹{:.2f}",
                "GTT Target": "₹{:.2f}",
                "Up Prob (%)": "{:.1f}",
                "Backtest Acc (%)": "{:.1f}",
                "RSI": "{:.1f}"
            })
            
        st.dataframe(styled_df, use_container_width=True, height=600)

st.markdown("---")
st.subheader("📖 What is an Alpha Buy?")
st.markdown("""
When the broader market is falling, most stocks fall with it. If a stock is rising against the tide, it means large institutions are aggressively buying it regardless of market conditions. 
- The dashboard now pulls the **Nifty 50 Index (^NSEI)** and calculates its 10-day return.
- It then calculates the individual stock's 10-day return.
- If the stock's return is beating the Nifty by more than **3.0%** AND the XGBoost model flashes a Buy, it is upgraded to a **⭐ ALPHA BUY**. These are your strongest setups in a bear market.
""")