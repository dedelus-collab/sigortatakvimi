"""
Binance Kripto TD Sequential + Heiken Ashi Otomatik Tarayıcı
Her saat başı çalışır ve mail gönderir
"""

import pandas as pd
from datetime import datetime, timedelta
import warnings
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule

warnings.filterwarnings('ignore')

# ============================================================================
# MAİL AYARLARI - KENDİ BİLGİLERİNİZİ GİRİN
# ============================================================================
MAIL_AYARLARI = {
    'gonderici_mail': 'cccanguler@gmail.com',
    'gonderici_sifre': 'Duru1982',
    'alici_mail': 'cccanguler@gmail.com',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}
# ============================================================================

# Taranacak coinler
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


def binance_veri_cek(symbol, interval='4h', limit=500):
    """Binance API'den veri çeker"""
    try:
        url = "https://api.binance.com/api/v3/klines"
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        if not data:
            return None
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df.set_index('timestamp', inplace=True)
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        return df
    except:
        return None


def heiken_ashi(df):
    """Heiken Ashi hesapla"""
    df = df.copy()
    df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    df['HA_Open'] = 0.0
    df.loc[df.index[0], 'HA_Open'] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
    
    for i in range(1, len(df)):
        df.loc[df.index[i], 'HA_Open'] = (df['HA_Open'].iloc[i-1] + df['HA_Close'].iloc[i-1]) / 2
    
    df['HA_High'] = df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    df['HA_Low'] = df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)
    
    return df


def td_sequential(df):
    """TD Sequential + Heiken Ashi"""
    df = heiken_ashi(df)
    
    # Buy Setup
    df['buy_setup'] = 0
    buy_count = 0
    for i in range(4, len(df)):
        if df['HA_Close'].iloc[i] < df['HA_Close'].iloc[i-4]:
            buy_count += 1
            df.loc[df.index[i], 'buy_setup'] = min(buy_count, 9)
        else:
            buy_count = 0
    
    # Sell Setup
    df['sell_setup'] = 0
    sell_count = 0
    for i in range(4, len(df)):
        if df['HA_Close'].iloc[i] > df['HA_Close'].iloc[i-4]:
            sell_count += 1
            df.loc[df.index[i], 'sell_setup'] = min(sell_count, 9)
        else:
            sell_count = 0
    
    # Trend
    df['ha_trend'] = 'NÖTR'
    for i in range(len(df)):
        if df['HA_Close'].iloc[i] > df['HA_Open'].iloc[i]:
            df.loc[df.index[i], 'ha_trend'] = 'YÜKSELİŞ'
        elif df['HA_Close'].iloc[i] < df['HA_Open'].iloc[i]:
            df.loc[df.index[i], 'ha_trend'] = 'DÜŞÜŞ'
    
    return df


def trend_gucu(df):
    """Trend gücü hesapla"""
    if len(df) < 5:
        return "BELİRSİZ"
    son_5 = df.tail(5)
    yukselis = (son_5['ha_trend'] == 'YÜKSELİŞ').sum()
    dusus = (son_5['ha_trend'] == 'DÜŞÜŞ').sum()
    
    if yukselis >= 4:
        return "GÜÇLÜ YÜKSELİŞ"
    elif dusus >= 4:
        return "GÜÇLÜ DÜŞÜŞ"
    elif yukselis >= 3:
        return "ORTA YÜKSELİŞ"
    elif dusus >= 3:
        return "ORTA DÜŞÜŞ"
    else:
        return "KARARSIZ"


def volatilite(df):
    """Volatilite hesapla"""
    if len(df) < 20:
        return "BELİRSİZ"
    son_20 = df.tail(20)
    vol = son_20['Close'].pct_change().std() * 100
    if vol > 5:
        return "YÜKSEK"
    elif vol > 2:
        return "ORTA"
    else:
        return "DÜŞÜK"


def coin_analiz(coin):
    """Tek bir coin'i analiz et"""
    try:
        # Stablecoin'leri atla
        if coin in ['USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FDUSD', 'USDE', 
                    'USDP', 'USD1', 'XUSD', 'BFUSD', 'RLUSD', 'EUR', 'EURI', 'AEUR']:
            return None
        
        symbol = f"{coin}USDT"
        df = binance_veri_cek(symbol, interval='4h', limit=500)
        
        if df is None or len(df) < 10:
            return None
        
        df = td_sequential(df)
        
        son_fiyat = df['Close'].iloc[-1]
        son_ha_close = df['HA_Close'].iloc[-1]
        son_ha_open = df['HA_Open'].iloc[-1]
        buy_setup = int(df['buy_setup'].iloc[-1])
        sell_setup = int(df['sell_setup'].iloc[-1])
        
        # 24h değişim
        degisim_24h = 0
        if len(df) >= 7:
            degisim_24h = ((son_fiyat - df['Close'].iloc[-7]) / df['Close'].iloc[-7]) * 100
        
        ha_renk = "🟢 YEŞİL" if son_ha_close > son_ha_open else "🔴 KIRMIZI"
        
        return {
            'coin': coin,
            'fiyat': round(son_fiyat, 8),
            'degisim_24h': round(degisim_24h, 2),
            'ha_renk': ha_renk,
            'trend': trend_gucu(df),
            'volatilite': volatilite(df),
            'buy_setup': buy_setup,
            'sell_setup': sell_setup,
            'buy_9': buy_setup == 9,
            'sell_9': sell_setup == 9
        }
    except:
        return None


def html_rapor_olustur(buy_list, sell_list, diger_list, toplam, basarisiz):
    """HTML mail raporu oluştur"""
    tarih = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ background-color: white; padding: 20px; border-radius: 10px; max-width: 1000px; margin: auto; }}
            h1 {{ color: #1a73e8; border-bottom: 3px solid #1a73e8; padding-bottom: 10px; }}
            h2 {{ color: #34a853; margin-top: 30px; }}
            h3 {{ color: #ea4335; margin-top: 30px; }}
            .stats {{ background-color: #e8f0fe; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th {{ background-color: #1a73e8; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .green {{ color: #34a853; font-weight: bold; }}
            .red {{ color: #ea4335; font-weight: bold; }}
            .warning {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Binance Kripto Tarama Raporu</h1>
            <p><strong>Tarih:</strong> {tarih}</p>
            
            <div class="stats">
                <h3>📊 Özet</h3>
                <ul>
                    <li>Taranan: {toplam} coin</li>
                    <li>Başarılı: {toplam - basarisiz}</li>
                    <li><span class="green">Buy Setup 9: {len(buy_list)}</span></li>
                    <li><span class="red">Sell Setup 9: {len(sell_list)}</span></li>
                    <li>Yaklaşan: {len(diger_list)}</li>
                </ul>
            </div>
    """
    
    # Buy Setup 9
    if buy_list:
        html += '<h2>🟢 BUY SETUP 9 - LONG POZİSYON</h2><table><tr><th>Coin</th><th>Fiyat</th><th>24h %</th><th>HA</th><th>Trend</th><th>Vol</th></tr>'
        for h in sorted(buy_list, key=lambda x: (x['ha_renk'] == "🟢 YEŞİL", "KARARSIZ" in x['trend']), reverse=True)[:15]:
            ha_class = "green" if "YEŞİL" in h['ha_renk'] else "red"
            deg_class = "green" if h['degisim_24h'] > 0 else "red"
            html += f"<tr><td><strong>{h['coin']}</strong></td><td>${h['fiyat']:.8f}</td><td class='{deg_class}'>{h['degisim_24h']:+.2f}%</td><td class='{ha_class}'>{h['ha_renk']}</td><td>{h['trend']}</td><td>{h['volatilite']}</td></tr>"
        html += '</table>'
    else:
        html += '<h2>🟢 BUY SETUP 9</h2><p>Sinyal yok</p>'
    
    # Sell Setup 9
    if sell_list:
        html += '<h3>🔴 SELL SETUP 9 - SHORT / ÇIKIŞ</h3><table><tr><th>Coin</th><th>Fiyat</th><th>24h %</th><th>HA</th><th>Trend</th><th>Vol</th></tr>'
        for h in sorted(sell_list, key=lambda x: (x['ha_renk'] == "🔴 KIRMIZI", "KARARSIZ" in x['trend']), reverse=True)[:15]:
            ha_class = "green" if "YEŞİL" in h['ha_renk'] else "red"
            deg_class = "green" if h['degisim_24h'] > 0 else "red"
            html += f"<tr><td><strong>{h['coin']}</strong></td><td>${h['fiyat']:.8f}</td><td class='{deg_class}'>{h['degisim_24h']:+.2f}%</td><td class='{ha_class}'>{h['ha_renk']}</td><td>{h['trend']}</td><td>{h['volatilite']}</td></tr>"
        html += '</table>'
    else:
        html += '<h3>🔴 SELL SETUP 9</h3><p>Sinyal yok</p>'
    
    # Yaklaşan
    if diger_list:
        html += '<h3>⚠️ YAKLAŞAN SİNYALLER (7-8)</h3><table><tr><th>Coin</th><th>Fiyat</th><th>Setup</th><th>Trend</th></tr>'
        for h in diger_list[:10]:
            setup = f"Buy: {h['buy_setup']}" if h['buy_setup'] >= 7 else f"Sell: {h['sell_setup']}"
            html += f"<tr><td><strong>{h['coin']}</strong></td><td>${h['fiyat']:.8f}</td><td>{setup}</td><td>{h['trend']}</td></tr>"
        html += '</table>'
    
    html += '<div class="warning"><strong>⚠️ UYARI:</strong> Yatırım tavsiyesi değildir!</div></div></body></html>'
    return html


def mail_gonder(konu, html):
    """Mail gönder"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = konu
        msg['From'] = MAIL_AYARLARI['gonderici_mail']
        msg['To'] = MAIL_AYARLARI['alici_mail']
        msg.attach(MIMEText(html, 'html'))
        
        server = smtplib.SMTP(MAIL_AYARLARI['smtp_server'], MAIL_AYARLARI['smtp_port'])
        server.starttls()
        server.login(MAIL_AYARLARI['gonderici_mail'], MAIL_AYARLARI['gonderici_sifre'])
        server.send_message(msg)
        server.quit()
        
        print(f"✓ Mail gönderildi: {MAIL_AYARLARI['alici_mail']}")
        return True
    except Exception as e:
        print(f"✗ Mail hatası: {str(e)}")
        return False


def tara():
    """Ana tarama fonksiyonu"""
    print("\n" + "=" * 100)
    print(f"🔍 TARAMA BAŞLADI: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    buy_list = []
    sell_list = []
    diger_list = []
    basarisiz = 0
    toplam = len(BINANCE_COINS)
    
    for i, coin in enumerate(BINANCE_COINS, 1):
        print(f"İlerleme: [{i}/{toplam}] {coin:10s}", end='\r')
        
        sonuc = coin_analiz(coin)
        
        if sonuc:
            if sonuc['buy_9']:
                buy_list.append(sonuc)
            elif sonuc['sell_9']:
                sell_list.append(sonuc)
            elif sonuc['buy_setup'] >= 7 or sonuc['sell_setup'] >= 7:
                diger_list.append(sonuc)
        else:
            basarisiz += 1
        
        if i % 10 == 0:
            time.sleep(0.5)
    
    print(f"\n✓ Tarama tamamlandı: {toplam - basarisiz} başarılı, {basarisiz} başarısız")
    
    # Konsola yazdır
    print("\n🟢 BUY SETUP 9:", len(buy_list))
    for h in buy_list[:5]:
        print(f"  {h['coin']:8s} | ${h['fiyat']:.8f} | {h['degisim_24h']:+6.2f}% | {h['ha_renk']}")
    
    print("\n🔴 SELL SETUP 9:", len(sell_list))
    for h in sell_list[:5]:
        print(f"  {h['coin']:8s} | ${h['fiyat']:.8f} | {h['degisim_24h']:+6.2f}% | {h['ha_renk']}")
    
    # Mail gönder
    if MAIL_AYARLARI['gonderici_mail'] != 'your_email@gmail.com':
        sinyal_sayisi = len(buy_list) + len(sell_list)
        konu = f"🚀 Binance: {sinyal_sayisi} Sinyal - {datetime.now().strftime('%d.%m %H:%M')}"
        html = html_rapor_olustur(buy_list, sell_list, diger_list, toplam, basarisiz)
        mail_gonder(konu, html)
    else:
        print("\n⚠️  Mail ayarları yapılmamış - mail gönderilmedi")
    
    print(f"\n✅ İşlem tamamlandı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏰ Sonraki tarama: {(datetime.now() + timedelta(hours=1)).strftime('%H:%M')}")
    print("=" * 100)


if __name__ == "__main__":
    try:
        import pandas
        import requests
        import schedule
    except ImportError:
        print("Eksik kütüphane! Yükleyin:")
        print("  pip install pandas requests schedule")
        exit(1)
    
    # Mail kontrolü
    if MAIL_AYARLARI['gonderici_mail'] == 'your_email@gmail.com':
        print("\n" + "=" * 100)
        print("⚠️  MAİL AYARLARI YAPILMAMIŞ!")
        print("=" * 100)
        print("\nScript başındaki MAIL_AYARLARI bölümünü doldurun:")
        print("  • gonderici_mail: Gmail adresiniz")
        print("  • gonderici_sifre: Gmail uygulama şifreniz")
        print("  • alici_mail: Mail alacak kişi")
        print("\nGmail uygulama şifresi: https://myaccount.google.com/security")
        print("=" * 100)
        
        devam = input("\nMail olmadan devam? (e/h): ")
        if devam.lower() != 'e':
            print("Çıkılıyor...")
            exit(0)
    
    print("\n" + "=" * 100)
    print("🤖 OTOMATIK TARAMA SİSTEMİ")
    print("=" * 100)
    print("⏰ Zamanlama: Her saat başı")
    print("📧 Mail: " + ("Aktif" if MAIL_AYARLARI['gonderici_mail'] != 'your_email@gmail.com' else "Devre Dışı"))
    print("💡 Durdurmak: CTRL+C")
    print("=" * 100)
    
    # İlk tarama
    tara()
    
    # Her saat başı
    schedule.every().hour.at(":00").do(tara)
    
    print("\n⏳ Zamanlayıcı aktif. Bekleniyor...\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⛔ DURDURULDU")
        print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("👋 Görüşmek üzere!\n")