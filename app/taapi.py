import requests

# 1) Spot market
spot_url = "https://api.binance.com/api/v3/exchangeInfo"
spot_data = requests.get(spot_url).json()

spot_coins = set()
for s in spot_data.get("symbols", []):
    if s.get("status") == "TRADING":
        spot_coins.add(s.get("baseAsset"))

# 2) USDT-M Futures
futures_url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
futures_data = requests.get(futures_url).json()

futures_coins = set()
for s in futures_data.get("symbols", []):
    if s.get("status") == "TRADING":
        futures_coins.add(s.get("baseAsset"))

# 3) COIN-M Futures
coinm_url = "https://dapi.binance.com/dapi/v1/exchangeInfo"
coinm_data = requests.get(coinm_url).json()

for s in coinm_data.get("symbols", []):
    if s.get("status") == "TRADING":
        futures_coins.add(s.get("baseAsset"))

# 4) Spot var ama Futures yok
spot_only = sorted(c for c in spot_coins - futures_coins if c)

print(f"SADECE SPOT (FUTURES YOK) COIN SAYISI: {len(spot_only)}\n")
print(spot_only)
