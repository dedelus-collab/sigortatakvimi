"""
Binance API ile Kripto İşlem Çiftleri - TD Sequential + Heiken Ashi HAFTALIK Tarayıcı
Gerçek Binance verilerini kullanır
"""

import pandas as pd
from datetime import datetime, timedelta
import warnings
import time
import requests
warnings.filterwarnings('ignore')

# Majör coinler (En yüksek market cap ve hacim)
MAJOR_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE', 'DOT', 'MATIC',
    'LINK', 'UNI', 'LTC', 'ATOM', 'ETC', 'XLM', 'NEAR', 'ALGO', 'VET', 'ICP',
    'FIL', 'HBAR', 'APT', 'ARB', 'OP', 'GRT', 'AAVE', 'MKR', 'SNX', 'LDO',
    'CRV', 'SAND', 'MANA', 'AXS', 'RUNE', 'FTM', 'INJ', 'TIA', 'SEI', 'SUI',
    'STX', 'IMX', 'RNDR', 'THETA', 'FLR', 'KAVA', 'EGLD', 'XTZ', 'EOS', 'FLOW',
    'APE', 'CHZ', 'GMT', 'GAL', 'BLUR', 'CFX', 'JTO', 'WLD', 'ORDI', 'MEME',
    'TON', 'TRX', 'BCH', 'DYDX', 'GMX', 'COMP', 'SUSHI', 'YFI', 'ZRX', 'BAT'
]

# Diğer önemli ve alternatif coinler
OTHER_COINS = [
    'ACA', 'ACM', 'ADX', 'AEUR', 'ALCX', 'AMP', 'ARDR', 'ATM', 'AUDIO', 'BAR',
    'BIFI', 'BNSOL', 'BONK', 'BTTC', 'CITY', 'DATA', 'DCR', 'DGB',
    'DODO', 'FARM', 'FLOKI', 'FTT', 'GLMR', 'GNO', 'GNS',
    'IDEX', 'IQ', 'JUV', 'LAZIO', 'LUNA', 'LUNC', 'MBL', 'MDT', 'NEXO',
    'OSMO', 'PEPE', 'PIVX', 'POND', 'PORTO', 'PSG', 'PYR', 'QI', 'QKC', 'QUICK',
    'RAD', 'RAY', 'REQ', 'SC', 'SHIB', 'STRAX', 'SXP', 'TFUEL', 'TKO',
    'UTK', 'WAN', 'WIN', 'XEC', 'XNO', 
    '1INCH', 'ENJ', 'GALA', 'HOT', 'JASMY', 'MASK', 'OMG', 'ONE', 'QTUM',
    'RVN', 'SKL', 'STORJ', 'WAVES', 'WOO', 'ZIL', 'CELO', 'CTSI', 'ENS',
    'FET', 'MAGIC', 'PEOPLE', 'ROSE', 'SSV', 'T', 'USTC', 'ACH', 'ANKR',
    'ARPA', 'BAND', 'BEL', 'COTI', 'CVX', 'DUSK', 'HIGH', 'HOOK', 'ID',
    'LEVER', 'LQTY', 'LOKA', 'MAV', 'NMR', 'OG', 'PERP', 'POWR', 'RDNT',
    'STMX', 'SUN', 'TRU', 'UNFI', 'VOXEL', 'WRX', 'XVS', 'YGG'
]

# Tüm coinleri birleştir
ALL_COINS = MAJOR_COINS + OTHER_COINS

def binance_klines_cek(symbol, interval='1w', limit=200):
    """
    Binance API'den kline (mum) verisi çeker
    
    Args:
        symbol: İşlem çifti (örn: BTCUSDT)
        interval: Zaman dilimi (1w=haftalık, 1d=günlük, 4h vb.)
        limit: Kaç mum çekilecek (max 1000)
    
    Returns:
        DataFrame: OHLCV verisi
    """
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if not data:
            return None
        
        # DataFrame'e çevir
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # Sadece gerekli kolonları al
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        # Veri tiplerini düzelt
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # Index'i timestamp yap
        df.set_index('timestamp', inplace=True)
        
        # Kolon isimlerini büyük harfe çevir (standart format)
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        return df
        
    except Exception as e:
        return None

def heiken_ashi(df):
    """
    Heiken Ashi mumlarını hesaplar
    """
    df = df.copy()
    
    df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    df['HA_Open'] = 0.0
    df.loc[df.index[0], 'HA_Open'] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
    
    for i in range(1, len(df)):
        df.loc[df.index[i], 'HA_Open'] = (df['HA_Open'].iloc[i-1] + df['HA_Close'].iloc[i-1]) / 2
    
    df['HA_High'] = df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    df['HA_Low'] = df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)
    
    return df

def td_sequential_heiken_ashi(df):
    """
    Heiken Ashi mumları üzerinde TD Sequential hesaplama
    """
    df = df.copy()
    df = heiken_ashi(df)
    
    # Buy Setup
    df['buy_setup'] = 0
    buy_count = 0
    
    for i in range(4, len(df)):
        if df['HA_Close'].iloc[i] < df['HA_Close'].iloc[i-4]:
            buy_count += 1
            df.loc[df.index[i], 'buy_setup'] = buy_count
            if buy_count >= 9:
                buy_count = 9
        else:
            buy_count = 0
    
    # Sell Setup
    df['sell_setup'] = 0
    sell_count = 0
    
    for i in range(4, len(df)):
        if df['HA_Close'].iloc[i] > df['HA_Close'].iloc[i-4]:
            sell_count += 1
            df.loc[df.index[i], 'sell_setup'] = sell_count
            if sell_count >= 9:
                sell_count = 9
        else:
            sell_count = 0
    
    # Trend analizi
    df['ha_trend'] = 'NÖTR'
    for i in range(len(df)):
        if df['HA_Close'].iloc[i] > df['HA_Open'].iloc[i]:
            df.loc[df.index[i], 'ha_trend'] = 'YÜKSELİŞ'
        elif df['HA_Close'].iloc[i] < df['HA_Open'].iloc[i]:
            df.loc[df.index[i], 'ha_trend'] = 'DÜŞÜŞ'
    
    return df

def trend_gucu_hesapla(df):
    """
    Trend gücü hesaplama - Son 5 hafta
    """
    if len(df) < 5:
        return "BELİRSİZ"
    
    son_5 = df.tail(5)
    yukselis_sayisi = (son_5['ha_trend'] == 'YÜKSELİŞ').sum()
    dusus_sayisi = (son_5['ha_trend'] == 'DÜŞÜŞ').sum()
    
    if yukselis_sayisi >= 4:
        return "GÜÇLÜ YÜKSELİŞ"
    elif dusus_sayisi >= 4:
        return "GÜÇLÜ DÜŞÜŞ"
    elif yukselis_sayisi >= 3:
        return "ORTA YÜKSELİŞ"
    elif dusus_sayisi >= 3:
        return "ORTA DÜŞÜŞ"
    else:
        return "KARARSIZ"

def volatilite_hesapla(df):
    """
    Son 12 haftanın volatilitesini hesaplar
    """
    if len(df) < 12:
        return "BELİRSİZ"
    
    son_12 = df.tail(12)
    volatilite = son_12['Close'].pct_change().std() * 100
    
    if volatilite > 15:
        return "YÜKSEK"
    elif volatilite > 8:
        return "ORTA"
    else:
        return "DÜŞÜK"

def coin_tara(coin, base='USDT'):
    """
    Tek bir kripto parayı tarar
    
    Args:
        coin: Kripto para sembolü (örn: "BTC")
        base: Baz para (varsayılan: "USDT")
    """
    try:
        # Stablecoin'ler ve forex için özel durum
        if coin in ['USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FDUSD', 'USDE', 'USDP', 
                    'USD1', 'XUSD', 'BFUSD', 'RLUSD', 'EUR', 'EURI', 'AEUR']:
            return None
        
        # Binance sembol formatı: BTCUSDT (tire yok, boşluk yok)
        symbol = f"{coin}{base}"
        
        # Haftalık veri çek (200 hafta = yaklaşık 3.8 yıl)
        df = binance_klines_cek(symbol, interval='1w', limit=200)
        
        if df is None or df.empty or len(df) < 10:
            return None
        
        df = td_sequential_heiken_ashi(df)
        trend_gucu = trend_gucu_hesapla(df)
        volatilite = volatilite_hesapla(df)
        
        son_buy_setup = df['buy_setup'].iloc[-1]
        son_sell_setup = df['sell_setup'].iloc[-1]
        son_fiyat = df['Close'].iloc[-1]
        son_ha_close = df['HA_Close'].iloc[-1]
        son_ha_open = df['HA_Open'].iloc[-1]
        son_trend = df['ha_trend'].iloc[-1]
        
        # 7 günlük (1 hafta) değişim hesapla
        if len(df) >= 2:
            degisim_1w = ((son_fiyat - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
        else:
            degisim_1w = 0
        
        # 4 haftalık (1 ay) değişim hesapla
        if len(df) >= 5:
            degisim_4w = ((son_fiyat - df['Close'].iloc[-5]) / df['Close'].iloc[-5]) * 100
        else:
            degisim_4w = 0
        
        ha_renk = "🟢 YEŞİL" if son_ha_close > son_ha_open else "🔴 KIRMIZI"
        
        # Coin kategorisini belirle
        kategori = "MAJÖR" if coin in MAJOR_COINS else "ALT"
        
        sonuc = {
            'sembol': coin,
            'kategori': kategori,
            'parite': f"{coin}/{base}",
            'son_fiyat': round(son_fiyat, 8),
            'degisim_1w': round(degisim_1w, 2),
            'degisim_4w': round(degisim_4w, 2),
            'ha_close': round(son_ha_close, 8),
            'ha_open': round(son_ha_open, 8),
            'ha_renk': ha_renk,
            'ha_trend': son_trend,
            'trend_gucu': trend_gucu,
            'volatilite': volatilite,
            'buy_setup_9': son_buy_setup == 9,
            'sell_setup_9': son_sell_setup == 9,
            'buy_setup': int(son_buy_setup),
            'sell_setup': int(son_sell_setup),
            'tarih': df.index[-1].strftime('%Y-%m-%d')
        }
        
        return sonuc
        
    except Exception as e:
        return None

def tum_coinleri_tara():
    """
    Tüm kripto paraları tarar
    """
    print("=" * 110)
    print("BİNANCE KRİPTO - TD SEQUENTIAL + HEİKEN ASHI HAFTALIK TARAMA")
    print("=" * 110)
    print(f"Tarama Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Zaman Dilimi: HAFTALIK (1W) - Uzun vadeli yatırım perspektifi")
    print(f"Baz Para: USDT")
    print(f"Veri Kaynağı: Binance API")
    print("=" * 110)
    print(f"Taranan Majör Coin: {len(MAJOR_COINS)}")
    print(f"Taranan Diğer Coin: {len(OTHER_COINS)}")
    print(f"TOPLAM: {len(ALL_COINS)} coin")
    print("=" * 110)
    print("\nTarama başlatılıyor...\n")
    
    buy_setup_9_list = []
    sell_setup_9_list = []
    diger_sinyaller = []
    basarisiz = 0
    
    toplam = len(ALL_COINS)
    
    # Her coin'i tara
    for i, coin in enumerate(ALL_COINS, 1):
        yuzde = (i / toplam) * 100
        kategori = "MAJÖR" if coin in MAJOR_COINS else "ALT  "
        print(f"İlerleme: [{i}/{toplam}] %{yuzde:.1f} - [{kategori}] {coin:10s}", end='\r')
        
        sonuc = coin_tara(coin)
        
        if sonuc:
            if sonuc['buy_setup_9']:
                buy_setup_9_list.append(sonuc)
            elif sonuc['sell_setup_9']:
                sell_setup_9_list.append(sonuc)
            elif sonuc['buy_setup'] >= 7 or sonuc['sell_setup'] >= 7:
                diger_sinyaller.append(sonuc)
        else:
            basarisiz += 1
        
        # Binance API rate limit: 1200 request/min = ~20 req/sec
        # Her 10 request'te kısa bekleme
        if i % 10 == 0:
            time.sleep(0.5)
    
    print("\n" + "=" * 110)
    print(f"✓ Tarama tamamlandı!")
    print(f"  • Başarılı: {toplam - basarisiz}")
    print(f"  • Başarısız/Listelenmeyen: {basarisiz}")
    print("=" * 110)
    
    # Sonuçları göster - BUY SETUP 9
    print("\n🟢 BUY SETUP 9 (LONG POZİSYON) - Heiken Ashi HAFTALIK:")
    print("-" * 110)
    if buy_setup_9_list:
        # Önce kategoriye göre ayır
        major_buys = [h for h in buy_setup_9_list if h['kategori'] == 'MAJÖR']
        alt_buys = [h for h in buy_setup_9_list if h['kategori'] == 'ALT']
        
        if major_buys:
            print("\n  📌 MAJÖR COİNLER:")
            major_buys_sorted = sorted(major_buys, 
                                      key=lambda x: (x['ha_renk'] == "🟢 YEŞİL",
                                                    "KARARSIZ" in x['trend_gucu'],
                                                    x['volatilite'] == "ORTA"), 
                                      reverse=True)
            for h in major_buys_sorted:
                print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 1W: {h['degisim_1w']:+6.2f}% | 4W: {h['degisim_4w']:+6.2f}% | "
                      f"HA: {h['ha_renk']} | Trend: {h['trend_gucu']:18s} | Vol: {h['volatilite']:6s}")
        
        if alt_buys:
            print("\n  📌 DİĞER COİNLER:")
            alt_buys_sorted = sorted(alt_buys, 
                                    key=lambda x: (x['ha_renk'] == "🟢 YEŞİL",
                                                  "KARARSIZ" in x['trend_gucu'],
                                                  x['volatilite'] == "ORTA"), 
                                    reverse=True)
            for h in alt_buys_sorted[:15]:  # İlk 15'i göster
                print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 1W: {h['degisim_1w']:+6.2f}% | 4W: {h['degisim_4w']:+6.2f}% | "
                      f"HA: {h['ha_renk']} | Trend: {h['trend_gucu']:18s} | Vol: {h['volatilite']:6s}")
            if len(alt_buys) > 15:
                print(f"\n  ... ve {len(alt_buys) - 15} coin daha")
    else:
        print("  Sinyal bulunamadı")
    
    # SELL SETUP 9
    print("\n🔴 SELL SETUP 9 (SHORT POZİSYON / ÇIKIŞ) - Heiken Ashi HAFTALIK:")
    print("-" * 110)
    if sell_setup_9_list:
        # Önce kategoriye göre ayır
        major_sells = [h for h in sell_setup_9_list if h['kategori'] == 'MAJÖR']
        alt_sells = [h for h in sell_setup_9_list if h['kategori'] == 'ALT']
        
        if major_sells:
            print("\n  📌 MAJÖR COİNLER:")
            major_sells_sorted = sorted(major_sells, 
                                       key=lambda x: (x['ha_renk'] == "🔴 KIRMIZI",
                                                     "KARARSIZ" in x['trend_gucu'],
                                                     x['volatilite'] == "ORTA"), 
                                       reverse=True)
            for h in major_sells_sorted:
                print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 1W: {h['degisim_1w']:+6.2f}% | 4W: {h['degisim_4w']:+6.2f}% | "
                      f"HA: {h['ha_renk']} | Trend: {h['trend_gucu']:18s} | Vol: {h['volatilite']:6s}")
        
        if alt_sells:
            print("\n  📌 DİĞER COİNLER:")
            alt_sells_sorted = sorted(alt_sells, 
                                     key=lambda x: (x['ha_renk'] == "🔴 KIRMIZI",
                                                   "KARARSIZ" in x['trend_gucu'],
                                                   x['volatilite'] == "ORTA"), 
                                     reverse=True)
            for h in alt_sells_sorted[:15]:
                print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 1W: {h['degisim_1w']:+6.2f}% | 4W: {h['degisim_4w']:+6.2f}% | "
                      f"HA: {h['ha_renk']} | Trend: {h['trend_gucu']:18s} | Vol: {h['volatilite']:6s}")
            if len(alt_sells) > 15:
                print(f"\n  ... ve {len(alt_sells) - 15} coin daha")
    else:
        print("  Sinyal bulunamadı")
    
    # DİĞER SİNYALLER (7-8)
    print("\n⚠️  DİĞER ÖNEMLİ SİNYALLER (7-8) - Yakında 9:")
    print("-" * 110)
    if diger_sinyaller:
        major_others = [h for h in diger_sinyaller if h['kategori'] == 'MAJÖR']
        
        if major_others:
            print("\n  📌 MAJÖR COİNLER:")
            for h in major_others[:10]:
                setup_str = f"Buy: {h['buy_setup']}" if h['buy_setup'] >= 7 else f"Sell: {h['sell_setup']}"
                print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 1W: {h['degisim_1w']:+6.2f}% | "
                      f"HA: {h['ha_renk']} | {setup_str} | Trend: {h['trend_gucu']:18s}")
        
        alt_others = [h for h in diger_sinyaller if h['kategori'] == 'ALT']
        if alt_others:
            print("\n  📌 DİĞER COİNLER (İlk 15):")
            for h in alt_others[:15]:
                setup_str = f"Buy: {h['buy_setup']}" if h['buy_setup'] >= 7 else f"Sell: {h['sell_setup']}"
                print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 1W: {h['degisim_1w']:+6.2f}% | "
                      f"HA: {h['ha_renk']} | {setup_str} | Trend: {h['trend_gucu']:18s}")
        
        if len(diger_sinyaller) > 25:
            print(f"\n  ... ve {len(diger_sinyaller) - 25} sinyal daha")
    else:
        print("  Sinyal bulunamadı")
    
    # ÖNE ÇIKAN LONG POZİSYONLAR
    if buy_setup_9_list:
        print("\n" + "=" * 110)
        print("⭐ ÖNE ÇIKAN LONG POZİSYON FIRSATLARI (HAFTALIK):")
        print("=" * 110)
        
        # Önce majör coinlere bak
        major_opportunities = [h for h in buy_setup_9_list 
                              if h['kategori'] == 'MAJÖR'
                              and h['ha_renk'] == "🟢 YEŞİL" 
                              and ("KARARSIZ" in h['trend_gucu'] or "ORTA" in h['trend_gucu'])
                              and h['volatilite'] in ["ORTA", "YÜKSEK"]]
        
        if major_opportunities:
            print("\n💎 MAJÖR COİN FIRSATLARI:")
            for h in major_opportunities:
                print(f"\n💰 {h['parite']}")
                print(f"   • Fiyat: ${h['son_fiyat']:.8f} | 1 Hafta: {h['degisim_1w']:+.2f}% | 4 Hafta: {h['degisim_4w']:+.2f}%")
                print(f"   • HA Kapanış: ${h['ha_close']:.8f} | HA Açılış: ${h['ha_open']:.8f}")
                print(f"   • Son Mum: {h['ha_renk']} | Trend: {h['trend_gucu']} | Volatilite: {h['volatilite']}")
                print(f"   • Tarih: {h['tarih']}")
                print(f"   ✅ SİNYAL: HAFTALIK LONG fırsatı - Uzun vadeli yatırım için ideal")
                
                if h['volatilite'] == "YÜKSEK":
                    print(f"   ⚠️  RİSK: Yüksek volatilite - Pozisyon büyüklüğüne dikkat")
                else:
                    print(f"   💡 RİSK: Orta seviye - Standart risk yönetimi")
        
        # Sonra alt coinlere bak
        alt_opportunities = [h for h in buy_setup_9_list 
                            if h['kategori'] == 'ALT'
                            and h['ha_renk'] == "🟢 YEŞİL" 
                            and ("KARARSIZ" in h['trend_gucu'] or "ORTA" in h['trend_gucu'])
                            and h['volatilite'] in ["ORTA", "YÜKSEK"]]
        
        if alt_opportunities:
            print("\n\n🔹 ALTCOİN FIRSATLARI (İlk 5):")
            for h in alt_opportunities[:5]:
                print(f"\n💰 {h['parite']}")
                print(f"   • Fiyat: ${h['son_fiyat']:.8f} | 1 Hafta: {h['degisim_1w']:+.2f}% | 4 Hafta: {h['degisim_4w']:+.2f}%")
                print(f"   • Son Mum: {h['ha_renk']} | Trend: {h['trend_gucu']} | Volatilite: {h['volatilite']}")
                print(f"   • Tarih: {h['tarih']}")
                print(f"   ✅ SİNYAL: Altcoin LONG fırsatı - Yüksek risk/getiri")
                print(f"   ⚠️  RİSK: Altcoin volatilitesi yüksek - Dikkatli pozisyon yönetimi")
        
        if not major_opportunities and not alt_opportunities:
            print("  İdeal long fırsatı bulunamadı. Yukarıdaki listeden dikkatli seçim yapın.")
    
    # ÖNE ÇIKAN SHORT/ÇIKIŞ POZİSYONLARI
    if sell_setup_9_list:
        print("\n" + "=" * 110)
        print("⭐ ÖNE ÇIKAN SHORT POZİSYON / ÇIKIŞ NOKTALARI (HAFTALIK):")
        print("=" * 110)
        
        major_exit = [h for h in sell_setup_9_list 
                     if h['kategori'] == 'MAJÖR'
                     and h['ha_renk'] == "🔴 KIRMIZI" 
                     and ("KARARSIZ" in h['trend_gucu'] or "ORTA" in h['trend_gucu'])]
        
        if major_exit:
            print("\n💎 MAJÖR COİNLER:")
            for h in major_exit:
                print(f"\n📉 {h['parite']}")
                print(f"   • Fiyat: ${h['son_fiyat']:.8f} | 1 Hafta: {h['degisim_1w']:+.2f}% | 4 Hafta: {h['degisim_4w']:+.2f}%")
                print(f"   • Son Mum: {h['ha_renk']} | Trend: {h['trend_gucu']} | Volatilite: {h['volatilite']}")
                print(f"   • Tarih: {h['tarih']}")
                print(f"   ✅ SİNYAL: HAFTALIK SHORT fırsatı veya LONG'dan ÇIKIŞ")
                
                if h['degisim_4w'] < -20:
                    print(f"   ⚠️  DİKKAT: Güçlü düşüş trendi - Çok geç olabilir")
        
        alt_exit = [h for h in sell_setup_9_list 
                   if h['kategori'] == 'ALT'
                   and h['ha_renk'] == "🔴 KIRMIZI"]
        
        if alt_exit:
            print("\n\n🔹 ALTCOİNLER (İlk 5):")
            for h in alt_exit[:5]:
                print(f"\n📉 {h['parite']}")
                print(f"   • Fiyat: ${h['son_fiyat']:.8f} | 1 Hafta: {h['degisim_1w']:+.2f}% | 4 Hafta: {h['degisim_4w']:+.2f}%")
                print(f"   • Son Mum: {h['ha_renk']} | Trend: {h['trend_gucu']}")
                print(f"   ✅ SİNYAL: Altcoin SHORT veya ÇIKIŞ noktası")
        
        if not major_exit and not alt_exit:
            print("  İdeal short fırsatı bulunamadı.")
    
    # ÖZET
    print("\n" + "=" * 110)
    print("📈 GENEL ÖZET:")
    print(f"  • Taranan Toplam Coin: {toplam} (Majör: {len(MAJOR_COINS)}, Alt: {len(OTHER_COINS)})")
    print(f"  • Buy Setup 9 (LONG): {len(buy_setup_9_list)} coin")
    print(f"     - Majör: {len([h for h in buy_setup_9_list if h['kategori'] == 'MAJÖR'])}")
    print(f"     - Alt: {len([h for h in buy_setup_9_list if h['kategori'] == 'ALT'])}")
    print(f"  • Sell Setup 9 (SHORT/ÇIKIŞ): {len(sell_setup_9_list)} coin")
    print(f"     - Majör: {len([h for h in sell_setup_9_list if h['kategori'] == 'MAJÖR'])}")
    print(f"     - Alt: {len([h for h in sell_setup_9_list if h['kategori'] == 'ALT'])}")
    print(f"  • Yaklaşan Sinyaller (7-8): {len(diger_sinyaller)} coin")
    print("=" * 110)
    
    print("\n💡 HAFTALIK TİCARET NOTLARI:")
    print("  📌 Haftalık zaman dilimi = Uzun vadeli yatırım stratejisi (aylar)")
    print("  📌 Binance API kullanılıyor = Gerçek zamanlı veriler")
    print("  📌 Majör coinler = Düşük risk, orta getiri")
    print("  📌 Altcoinler = Yüksek risk, yüksek getiri potansiyeli")
    print("  📌 Buy Setup 9 + Yeşil HA = Uzun vadeli LONG pozisyon")
    print("  📌 Sell Setup 9 + Kırmızı HA = Uzun vadeli pozisyondan ÇIKIŞ")
    print("  📌 Haftalık sinyaller daha güvenilir ama daha nadir!")
    print("=" * 110)
    
    print("\n⚠️  RİSK UYARISI:")
    print("  • Kripto piyasası son derece volatildir")
    print("  • Haftalık strateji = sabır ve disiplin gerektirir")
    print("  • Stop-loss kullanımı ZORUNLUDUR")
    print("  • Portföy çeşitlendirmesi önemlidir")
    print("  • Bu sinyaller yatırım tavsiyesi DEĞİLDİR!")
    print("=" * 110)
    
    # Sonuçları dosyaya kaydet
    tarih_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    dosya_adi = f"binance_tarama_haftalik_{tarih_str}.txt"
    
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(f"BINANCE KRİPTO TARAMA SONUÇLARI (HAFTALIK)\n")
        f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Taranan Coin: {toplam} (Majör: {len(MAJOR_COINS)}, Alt: {len(OTHER_COINS)})\n\n")
        
        f.write("BUY SETUP 9 (LONG):\n")
        f.write("Kategori,Parite,Fiyat,1W%,4W%,HA,Trend,Volatilite\n")
        for h in buy_setup_9_list:
            f.write(f"{h['kategori']},{h['parite']},{h['son_fiyat']:.8f},{h['degisim_1w']:.2f}%,"
                   f"{h['degisim_4w']:.2f}%,{h['ha_renk']},{h['trend_gucu']},{h['volatilite']}\n")
        
        f.write("\nSELL SETUP 9 (SHORT/ÇIKIŞ):\n")
        f.write("Kategori,Parite,Fiyat,1W%,4W%,HA,Trend,Volatilite\n")
        for h in sell_setup_9_list:
            f.write(f"{h['kategori']},{h['parite']},{h['son_fiyat']:.8f},{h['degisim_1w']:.2f}%,"
                   f"{h['degisim_4w']:.2f}%,{h['ha_renk']},{h['trend_gucu']},{h['volatilite']}\n")
        
        f.write("\nYAKLAŞAN SİNYALLER (7-8):\n")
        f.write("Kategori,Parite,Fiyat,Setup,Trend,Volatilite\n")
        for h in diger_sinyaller:
            setup = f"Buy:{h['buy_setup']}" if h['buy_setup'] >= 7 else f"Sell:{h['sell_setup']}"
            f.write(f"{h['kategori']},{h['parite']},{h['son_fiyat']:.8f},{setup},"
                   f"{h['trend_gucu']},{h['volatilite']}\n")
    
    print(f"\n✓ Sonuçlar '{dosya_adi}' dosyasına kaydedildi")
    print("=" * 110)

if __name__ == "__main__":
    try:
        import pandas
        import requests
    except ImportError:
        print("Gerekli kütüphaneler yükleniyor...")
        print("Lütfen şu komutları çalıştırın:")
        print("  pip install pandas requests")
        exit(1)
    
    tum_coinleri_tara()