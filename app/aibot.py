import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split

# =====================
# DATA
# =====================
symbol = "ETH-USD"
df = yf.download(symbol, period="3y", interval="4h")
df.dropna(inplace=True)

# =====================
# INDICATORS
# =====================
df["rsi"] = RSIIndicator(df["Close"], 14).rsi()
df["ema20"] = EMAIndicator(df["Close"], 20).ema_indicator()
df["ema50"] = EMAIndicator(df["Close"], 50).ema_indicator()

# =====================
# BASELINE BUY
# =====================
df["buy"] = (
    (df["rsi"] < 30) &
    (df["ema20"] > df["ema50"])
).astype(int)

# =====================
# AI TARGET (5 BAR SONRA YÜKSELİR Mİ)
# =====================
df["future"] = df["Close"].shift(-5)
df["target"] = (df["future"] > df["Close"]).astype(int)
df.dropna(inplace=True)

features = ["rsi", "ema20", "ema50"]
X = df[features]
y = df["target"]

# =====================
# TRAIN AI
# =====================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, shuffle=False, test_size=0.2
)

model = XGBClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss"
)

model.fit(X_train, y_train)

df["buy_prob"] = model.predict_proba(X)[:, 1]

# =====================
# AI FILTER
# =====================
df["ai_buy"] = (df["buy"] == 1) & (df["buy_prob"] > 0.65)

# =====================
# AI POSITION SIZING
# =====================
df["size"] = np.clip((df["buy_prob"] - 0.5) * 2, 0.1, 1.0)

# =====================
# BACKTEST
# =====================
capital = 1.0
equity = []
position = 0
entry_price = 0

for i in range(len(df)):
    price = df["Close"].iloc[i]

    # ENTRY
    if position == 0 and df["ai_buy"].iloc[i]:
        position = capital * df["size"].iloc[i]
        entry_price = price
        capital -= position

    # EXIT
    elif position > 0 and df["rsi"].iloc[i] > 55:
        capital += position * (price / entry_price)
        position = 0

    equity.append(capital + (position * price / entry_price if position else 0))

df["equity"] = equity

# =====================
# METRICS
# =====================
returns = df["equity"].pct_change().dropna()
net_profit = (df["equity"].iloc[-1] - 1) * 100
max_dd = ((df["equity"] / df["equity"].cummax()) - 1).min() * 100
trades = df["ai_buy"].sum()

print("\nAI FILTER + SIZING BACKTEST")
print(f"Trades: {trades}")
print(f"Net Getiri %: {net_profit:.2f}")
print(f"Max Drawdown %: {max_dd:.2f}")
