"""
Binance API ile Kripto İşlem Çiftleri - TD Sequential + Heiken Ashi 4 Saatlik Tarayıcı
Gerçek Binance verilerini kullanır
"""

import pandas as pd
from datetime import datetime, timedelta
import warnings
import time
import requests
warnings.filterwarnings('ignore')

# Binance işlem çiftleri - Belirtilen coinler
BINANCE_COINS = [
    'ACA', 'ACM', 'ADX', 'AEUR', 'ALCX', 'AMP', 'ARDR', 'ATM', 'AUDIO', 'BAR',
    'BFUSD', 'BIFI', 'BNSOL', 'BONK', 'BTTC', 'CITY', 'DAI', 'DATA', 'DCR', 'DGB',
    'DODO', 'EUR', 'EURI', 'FARM', 'FDUSD', 'FLOKI', 'FTT', 'GLMR', 'GNO', 'GNS',
    'IDEX', 'IQ', 'JUV', 'KGST', 'LAZIO', 'LUNA', 'LUNC', 'MBL', 'MDT', 'NEXO',
    'OSMO', 'PEPE', 'PIVX', 'POND', 'PORTO', 'PSG', 'PYR', 'QI', 'QKC', 'QUICK',
    'RAD', 'RAY', 'REQ', 'RLUSD', 'SC', 'SHIB', 'STRAX', 'SXP', 'TFUEL', 'TKO',
    'TUSD', 'U', 'USD1', 'USDE', 'USDP', 'USDT', 'UTK', 'WAN', 'WBETH', 'WBTC',
    'WIN', 'XEC', 'XNO', 'XUSD'
]

def binance_klines_cek(symbol, interval='4h', limit=500):
    """
    Binance API'den kline (mum) verisi çeker
    
    Args:
        symbol: İşlem çifti (örn: BTCUSDT)
        interval: Zaman dilimi (4h, 1h, 1d vb.)
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
    Trend gücü hesaplama - Son 5 mum
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
    Son 20 mumun volatilitesini hesaplar
    """
    if len(df) < 20:
        return "BELİRSİZ"
    
    son_20 = df.tail(20)
    volatilite = son_20['Close'].pct_change().std() * 100
    
    if volatilite > 5:
        return "YÜKSEK"
    elif volatilite > 2:
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
                    'USD1', 'XUSD', 'BFUSD', 'RLUSD']:
            return None
        
        # Binance sembol formatı: BTCUSDT (tire yok, boşluk yok)
        symbol = f"{coin}{base}"
        
        # 4 saatlik veri çek (500 mum = yaklaşık 83 gün)
        df = binance_klines_cek(symbol, interval='4h', limit=500)
        
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
        
        # 24h değişim hesapla (24h = 6 x 4h mum)
        if len(df) >= 7:
            degisim_24h = ((son_fiyat - df['Close'].iloc[-7]) / df['Close'].iloc[-7]) * 100
        else:
            degisim_24h = 0
        
        ha_renk = "🟢 YEŞİL" if son_ha_close > son_ha_open else "🔴 KIRMIZI"
        
        sonuc = {
            'sembol': coin,
            'parite': f"{coin}/{base}",
            'son_fiyat': round(son_fiyat, 8),
            'degisim_24h': round(degisim_24h, 2),
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
            'tarih': df.index[-1].strftime('%Y-%m-%d %H:%M')
        }
        
        return sonuc
        
    except Exception as e:
        return None

def tum_coinleri_tara():
    """
    Tüm kripto paraları tarar
    """
    print("=" * 100)
    print("BİNANCE KRİPTO - TD SEQUENTIAL + HEİKEN ASHI 4 SAATLİK TARAMA")
    print("=" * 100)
    print(f"Tarama Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Zaman Dilimi: 4 Saatlik (4H)")
    print(f"Baz Para: USDT")
    print(f"Veri Kaynağı: Binance API")
    print("=" * 100)
    print(f"Taranan Coin Sayısı: {len(BINANCE_COINS)}")
    print("=" * 100)
    print("\nTarama başlatılıyor...\n")
    
    buy_setup_9_list = []
    sell_setup_9_list = []
    diger_sinyaller = []
    basarisiz = 0
    
    toplam = len(BINANCE_COINS)
    
    # Her coin'i tara
    for i, coin in enumerate(BINANCE_COINS, 1):
        yuzde = (i / toplam) * 100
        print(f"İlerleme: [{i}/{toplam}] %{yuzde:.1f} - {coin:10s}", end='\r')
        
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
    
    print("\n" + "=" * 100)
    print(f"✓ Tarama tamamlandı!")
    print(f"  • Başarılı: {toplam - basarisiz}")
    print(f"  • Başarısız/Listelenmeyen: {basarisiz}")
    print("=" * 100)
    
    # Sonuçları göster - BUY SETUP 9
    print("\n🟢 BUY SETUP 9 (LONG POZİSYON) - Heiken Ashi 4H:")
    print("-" * 100)
    if buy_setup_9_list:
        buy_setup_9_list_sorted = sorted(buy_setup_9_list, 
                                        key=lambda x: (x['ha_renk'] == "🟢 YEŞİL",
                                                      "KARARSIZ" in x['trend_gucu'],
                                                      x['volatilite'] == "ORTA"), 
                                        reverse=True)
        for h in buy_setup_9_list_sorted:
            print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 24h: {h['degisim_24h']:+6.2f}% | "
                  f"HA: {h['ha_renk']} | Trend: {h['trend_gucu']:18s} | Vol: {h['volatilite']:6s}")
    else:
        print("  Sinyal bulunamadı")
    
    # SELL SETUP 9
    print("\n🔴 SELL SETUP 9 (SHORT POZİSYON / ÇIKIŞ) - Heiken Ashi 4H:")
    print("-" * 100)
    if sell_setup_9_list:
        sell_setup_9_list_sorted = sorted(sell_setup_9_list, 
                                         key=lambda x: (x['ha_renk'] == "🔴 KIRMIZI",
                                                       "KARARSIZ" in x['trend_gucu'],
                                                       x['volatilite'] == "ORTA"), 
                                         reverse=True)
        for h in sell_setup_9_list_sorted:
            print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 24h: {h['degisim_24h']:+6.2f}% | "
                  f"HA: {h['ha_renk']} | Trend: {h['trend_gucu']:18s} | Vol: {h['volatilite']:6s}")
    else:
        print("  Sinyal bulunamadı")
    
    # DİĞER SİNYALLER (7-8)
    print("\n⚠️  DİĞER ÖNEMLİ SİNYALLER (7-8) - Yakında 9:")
    print("-" * 100)
    if diger_sinyaller:
        for h in diger_sinyaller[:20]:
            setup_str = f"Buy: {h['buy_setup']}" if h['buy_setup'] >= 7 else f"Sell: {h['sell_setup']}"
            print(f"  {h['sembol']:8s} | ${h['son_fiyat']:12.8f} | 24h: {h['degisim_24h']:+6.2f}% | "
                  f"HA: {h['ha_renk']} | {setup_str} | Trend: {h['trend_gucu']:18s}")
        
        if len(diger_sinyaller) > 20:
            print(f"\n  ... ve {len(diger_sinyaller) - 20} sinyal daha")
    else:
        print("  Sinyal bulunamadı")
    
    # ÖNE ÇIKAN LONG POZİSYONLAR
    if buy_setup_9_list:
        print("\n" + "=" * 100)
        print("⭐ ÖNE ÇIKAN LONG POZİSYON FIRSATLARI:")
        print("=" * 100)
        
        one_cikanlar = [h for h in buy_setup_9_list 
                       if h['ha_renk'] == "🟢 YEŞİL" 
                       and ("KARARSIZ" in h['trend_gucu'] or "ORTA" in h['trend_gucu'])
                       and h['volatilite'] in ["ORTA", "YÜKSEK"]]
        
        if one_cikanlar:
            for h in one_cikanlar[:10]:
                print(f"\n💰 {h['parite']}")
                print(f"   • Fiyat: ${h['son_fiyat']:.8f} | 24h Değişim: {h['degisim_24h']:+.2f}%")
                print(f"   • HA Kapanış: ${h['ha_close']:.8f} | HA Açılış: ${h['ha_open']:.8f}")
                print(f"   • Son Mum: {h['ha_renk']} | Trend: {h['trend_gucu']} | Volatilite: {h['volatilite']}")
                print(f"   • Tarih: {h['tarih']}")
                print(f"   ✅ SİNYAL: İdeal LONG fırsatı - HA yeşil + Trend dönüşü + TD9")
                
                if h['volatilite'] == "YÜKSEK":
                    print(f"   ⚠️  RİSK: Yüksek volatilite - Sıkı stop-loss kullanın")
                else:
                    print(f"   💡 RİSK: Orta seviye - Standart risk yönetimi")
        else:
            print("  İdeal long fırsatı bulunamadı. Yukarıdaki listeden dikkatli seçim yapın.")
    
    # ÖNE ÇIKAN SHORT/ÇIKIŞ POZİSYONLARI
    if sell_setup_9_list:
        print("\n" + "=" * 100)
        print("⭐ ÖNE ÇIKAN SHORT POZİSYON / ÇIKIŞ NOKTALARI:")
        print("=" * 100)
        
        one_cikanlar = [h for h in sell_setup_9_list 
                       if h['ha_renk'] == "🔴 KIRMIZI" 
                       and ("KARARSIZ" in h['trend_gucu'] or "ORTA" in h['trend_gucu'])]
        
        if one_cikanlar:
            for h in one_cikanlar[:10]:
                print(f"\n📉 {h['parite']}")
                print(f"   • Fiyat: ${h['son_fiyat']:.8f} | 24h Değişim: {h['degisim_24h']:+.2f}%")
                print(f"   • HA Kapanış: ${h['ha_close']:.8f} | HA Açılış: ${h['ha_open']:.8f}")
                print(f"   • Son Mum: {h['ha_renk']} | Trend: {h['trend_gucu']} | Volatilite: {h['volatilite']}")
                print(f"   • Tarih: {h['tarih']}")
                print(f"   ✅ SİNYAL: İdeal SHORT fırsatı veya LONG pozisyondan ÇIKIŞ - HA kırmızı + TD9")
                
                if h['degisim_24h'] < -10:
                    print(f"   ⚠️  DİKKAT: Güçlü düşüş başlamış - Çok geç olabilir")
        else:
            print("  İdeal short fırsatı bulunamadı. Yukarıdaki listeden dikkatli seçim yapın.")
    
    # ÖZET
    print("\n" + "=" * 100)
    print("📈 GENEL ÖZET:")
    print(f"  • Taranan Toplam Coin: {toplam}")
    print(f"  • Buy Setup 9 (LONG): {len(buy_setup_9_list)} coin")
    print(f"  • Sell Setup 9 (SHORT/ÇIKIŞ): {len(sell_setup_9_list)} coin")
    print(f"  • Yaklaşan Sinyaller (7-8): {len(diger_sinyaller)} coin")
    print("=" * 100)
    
    print("\n💡 KRİPTO TİCARET NOTLARI:")
    print("  📌 4 saatlik zaman dilimi = Swing trading stratejisi (1-7 gün)")
    print("  📌 Binance API kullanılıyor = Gerçek zamanlı veriler")
    print("  📌 Buy Setup 9 + Yeşil HA = LONG pozisyon aç")
    print("  📌 Sell Setup 9 + Kırmızı HA = LONG'dan çık veya SHORT aç")
    print("  📌 MUTLAKA RSI, MACD, hacim ile doğrulayın!")
    print("=" * 100)
    
    print("\n⚠️  RİSK UYARISI:")
    print("  • Kripto piyasası son derece volatildir")
    print("  • Stop-loss kullanımı KRİTİKTİR")
    print("  • Bu sinyaller yatırım tavsiyesi değildir!")
    print("=" * 100)
    
    # Sonuçları dosyaya kaydet
    tarih_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    dosya_adi = f"binance_tarama_4h_{tarih_str}.txt"
    
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(f"BINANCE KRİPTO TARAMA SONUÇLARI (4 SAATLİK)\n")
        f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Taranan Coin: {toplam}\n\n")
        
        f.write("BUY SETUP 9 (LONG):\n")
        for h in buy_setup_9_list:
            f.write(f"{h['parite']},{h['son_fiyat']:.8f},{h['degisim_24h']:.2f}%,"
                   f"{h['ha_renk']},{h['trend_gucu']},{h['volatilite']}\n")
        
        f.write("\nSELL SETUP 9 (SHORT/ÇIKIŞ):\n")
        for h in sell_setup_9_list:
            f.write(f"{h['parite']},{h['son_fiyat']:.8f},{h['degisim_24h']:.2f}%,"
                   f"{h['ha_renk']},{h['trend_gucu']},{h['volatilite']}\n")
        
        f.write("\nYAKLAŞAN SİNYALLER (7-8):\n")
        for h in diger_sinyaller:
            setup = f"Buy:{h['buy_setup']}" if h['buy_setup'] >= 7 else f"Sell:{h['sell_setup']}"
            f.write(f"{h['parite']},{h['son_fiyat']:.8f},{setup},"
                   f"{h['trend_gucu']},{h['volatilite']}\n")
    
    print(f"\n✓ Sonuçlar '{dosya_adi}' dosyasına kaydedildi")
    print("=" * 100)

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