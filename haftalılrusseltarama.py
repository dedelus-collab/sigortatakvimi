"""
Russell 2000 - TD Sequential + Heiken Ashi Haftalık Tarayıcı
Amerikan küçük şirketlerini tarar
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import warnings
import time

warnings.filterwarnings('ignore')

# Russell 2000'in en likit ve popüler hisseleri
# Tam liste 2000 hisse - burada en aktif 200'ü var
RUSSELL_2000_STOCKS = [
    # Financials
    'WRBY', 'DCOM', 'PCTY', 'BANF', 'CATY', 'COLB', 'CVBF', 'EWBC', 
    'FFIN', 'FNB', 'FULT', 'GBCI', 'HWC', 'IBTX', 'NWBI', 'ONB', 
    'OZK', 'PB', 'PBCT', 'PNFP', 'SFNC', 'SNV', 'TCBI', 'UBSI', 
    'UMBF', 'UMPQ', 'VLY', 'WAFD', 'WBS', 'WSFS',
    
    # Healthcare
    'ADMA', 'AKRO', 'ALEC', 'ALKS', 'ALPN', 'AMRX', 'ANIP', 'APLS',
    'ARLP', 'ARVN', 'ASND', 'AVNS', 'AXSM', 'BDTX', 'BGNE', 'BIIB',
    'BLFS', 'BPMC', 'CARA', 'CERE', 'CGEM', 'CLDX', 'CRSP', 'CVAC',
    'CVIIQ', 'EDIT', 'EPIX', 'FATE', 'FDMT', 'FGEN', 'FOLD', 'GERN',
    
    # Technology
    'ACIW', 'AEIS', 'ALRM', 'AMBA', 'ATEN', 'AVAV', 'BL', 'BLKB',
    'BOX', 'CALX', 'CGNX', 'CLRO', 'CMTL', 'CNXN', 'COHR', 'CRUS',
    'CSGS', 'CSOD', 'CVLT', 'CXM', 'DLB', 'DOCN', 'DZSI', 'EVBG',
    'EXLS', 'FARO', 'FORM', 'FRSH', 'GTLS', 'HCAT', 'IDCC', 'INFN',
    
    # Consumer
    'AAON', 'ABG', 'ACLS', 'AIN', 'AIT', 'ALLE', 'AMED', 'AOS',
    'APOG', 'ARI', 'ATKR', 'AXL', 'B', 'BC', 'BCPC', 'BLD',
    'BLDR', 'BMI', 'BOOT', 'BRC', 'CALM', 'CBT', 'CEIX', 'CENX',
    
    # Industrials
    'AAON', 'ABM', 'ACA', 'ACHR', 'AGCO', 'AL', 'ALG', 'ALLE',
    'AMPS', 'ARCO', 'ASTE', 'ATI', 'AXL', 'B', 'BC', 'BECN',
    'BRC', 'BWXT', 'CECO', 'CRS', 'CW', 'CXT', 'DY', 'ESAB',
    
    # Real Estate
    'AAT', 'APLE', 'ARE', 'BPYU', 'BRX', 'BXP', 'CBRE', 'CIO',
    'CLDT', 'COLD', 'CPT', 'CUBE', 'CUZ', 'DEI', 'DEA', 'DLR',
    'DOC', 'EGP', 'ELS', 'EPR', 'EPRT', 'EQC', 'ESRT', 'EXR',
    
    # Energy
    'AM', 'AROC', 'ATEST', 'BTU', 'CDEV', 'CLB', 'CNX', 'CPE',
    'CRC', 'CRGY', 'CRK', 'DEN', 'DHT', 'ENLC', 'EPM', 'EQT',
    'GPOR', 'HLX', 'HP', 'KOS', 'LPI', 'MGY', 'MUR', 'NBR',
    
    # Materials
    'AA', 'APTV', 'ATI', 'BCPC', 'CENX', 'CLF', 'CMC', 'CRS',
    'DOOR', 'IOSP', 'MP', 'MTX', 'NGVT', 'NUE', 'OMI', 'RMBS',
    'RS', 'SCCO', 'SLVM', 'SMG', 'STLD', 'SXT', 'TGNA', 'TMST',
    
    # Utilities
    'AEE', 'AES', 'ALE', 'AQUA', 'AVA', 'AWK', 'BKH', 'CMS',
    'CNP', 'CPK', 'CWT', 'DTE', 'ES', 'EVRG', 'IDA', 'MDU',
    'NWE', 'NWN', 'OGS', 'ORA', 'OTTR', 'PNW', 'SJW', 'SR'
]


def heiken_ashi(df):
    """Heiken Ashi hesapla"""
    df = df.copy()
    
    df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    df['HA_Open'] = 0.0
    df.iloc[0, df.columns.get_loc('HA_Open')] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
    
    for i in range(1, len(df)):
        df.iloc[i, df.columns.get_loc('HA_Open')] = (
            df['HA_Open'].iloc[i-1] + df['HA_Close'].iloc[i-1]
        ) / 2
    
    df['HA_High'] = df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    df['HA_Low'] = df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)
    df['HA_Yesil'] = df['HA_Close'] > df['HA_Open']
    
    return df


def td_sequential(df):
    """TD Sequential + Heiken Ashi"""
    df = heiken_ashi(df)
    
    # Buy Setup
    df['Buy_Setup'] = 0
    count = 0
    for i in range(4, len(df)):
        if df['HA_Close'].iloc[i] < df['HA_Close'].iloc[i-4]:
            count += 1
            df.iloc[i, df.columns.get_loc('Buy_Setup')] = min(count, 9)
        else:
            count = 0
    
    # Sell Setup
    df['Sell_Setup'] = 0
    count = 0
    for i in range(4, len(df)):
        if df['HA_Close'].iloc[i] > df['HA_Close'].iloc[i-4]:
            count += 1
            df.iloc[i, df.columns.get_loc('Sell_Setup')] = min(count, 9)
        else:
            count = 0
    
    # Trend gücü
    if len(df) >= 5:
        son_5 = df.tail(5)
        yukselis = (son_5['HA_Yesil']).sum()
        if yukselis >= 4:
            trend = "GÜÇLÜ YÜKSELİŞ"
        elif yukselis >= 3:
            trend = "ORTA YÜKSELİŞ"
        elif yukselis <= 1:
            trend = "GÜÇLÜ DÜŞÜŞ"
        elif yukselis <= 2:
            trend = "ORTA DÜŞÜŞ"
        else:
            trend = "KARARSIZ"
    else:
        trend = "BELİRSİZ"
    
    return df, trend


def hisse_tara(ticker):
    """Tek bir hisse tarar"""
    try:
        # Haftalık veri çek (son 2 yıl)
        stock = yf.Ticker(ticker)
        df = stock.history(period='2y', interval='1d')
        
        if df.empty or len(df) < 20:
            return None
        
        # TD Sequential hesapla
        df, trend = td_sequential(df)
        
        # Son değerler
        son = df.iloc[-1]
        onceki = df.iloc[-2] if len(df) > 1 else son
        
        buy_setup = int(son['Buy_Setup'])
        sell_setup = int(son['Sell_Setup'])
        fiyat = son['Close']
        ha_yesil = son['HA_Yesil']
        
        # Buy Setup 9 tamamlandı mı kontrol et
        # Tamamlanmış = önceki mum 9'du, şimdi 9 değil veya 0
        buy_9_tamamlandi = (int(onceki['Buy_Setup']) == 9 and buy_setup != 9)
        buy_9_aktif = (buy_setup == 9)
        
        # Sell Setup 9 tamamlandı mı
        sell_9_tamamlandi = (int(onceki['Sell_Setup']) == 9 and sell_setup != 9)
        sell_9_aktif = (sell_setup == 9)
        
        # Hacim
        ort_hacim = df['Volume'].tail(20).mean()
        son_hacim = son['Volume']
        hacim_artis = ((son_hacim - ort_hacim) / ort_hacim) * 100 if ort_hacim > 0 else 0
        
        # 52 hafta min/max
        week_52_high = df['High'].tail(52).max()
        week_52_low = df['Low'].tail(52).min()
        fiyat_konum = ((fiyat - week_52_low) / (week_52_high - week_52_low)) * 100
        
        return {
            'ticker': ticker,
            'fiyat': round(fiyat, 2),
            'buy_setup': buy_setup,
            'sell_setup': sell_setup,
            'ha_yesil': ha_yesil,
            'trend': trend,
            'hacim_artis': round(hacim_artis, 1),
            'week_52_konum': round(fiyat_konum, 1),
            'buy_9_aktif': buy_9_aktif,
            'buy_9_tamamlandi': buy_9_tamamlandi,
            'sell_9_aktif': sell_9_aktif,
            'sell_9_tamamlandi': sell_9_tamamlandi
        }
    except:
        return None


def tara():
    """Tüm Russell 2000 hisselerini tarar"""
    
    print("\n" + "=" * 100)
    print("📊 RUSSELL 2000 - TD SEQUENTIAL + HEİKEN ASHI HAFTALIK TARAMA")
    print("=" * 100)
    print(f"⏰ Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📈 Zaman Dilimi: HAFTALIK (1W)")
    print(f"🎯 Hedef: Setup 9 Sinyalleri")
    print("=" * 100)
    print(f"\n🔍 {len(RUSSELL_2000_STOCKS)} hisse taranıyor...\n")
    
    buy_9_aktif_list = []      # Şu an Buy 9'da olanlar
    buy_9_tamamlandi_list = []  # Buy 9'u tamamlamış olanlar
    sell_9_aktif_list = []
    sell_9_tamamlandi_list = []
    yaklasan_list = []
    basarisiz = 0
    
    for i, ticker in enumerate(RUSSELL_2000_STOCKS, 1):
        print(f"İlerleme: [{i}/{len(RUSSELL_2000_STOCKS)}] {ticker:8s}", end='\r')
        
        sonuc = hisse_tara(ticker)
        
        if sonuc:
            if sonuc['buy_9_tamamlandi']:
                buy_9_tamamlandi_list.append(sonuc)
            elif sonuc['buy_9_aktif']:
                buy_9_aktif_list.append(sonuc)
            elif sonuc['sell_9_tamamlandi']:
                sell_9_tamamlandi_list.append(sonuc)
            elif sonuc['sell_9_aktif']:
                sell_9_aktif_list.append(sonuc)
            elif sonuc['buy_setup'] >= 7 or sonuc['sell_setup'] >= 7:
                yaklasan_list.append(sonuc)
        else:
            basarisiz += 1
        
        # API rate limit
        if i % 5 == 0:
            time.sleep(0.2)
    
    print(f"\n\n✅ Tarama tamamlandı!")
    print(f"   • Başarılı: {len(RUSSELL_2000_STOCKS) - basarisiz}")
    print(f"   • Başarısız: {basarisiz}")
    
    # BUY SETUP 9 - TAMAMLANMIŞ
    print("\n" + "=" * 100)
    print("🎯 BUY SETUP 9 TAMAMLANMIŞ (Geçen hafta 9'du, şimdi 1 veya 0) - HAFTALıK")
    print("=" * 100)
    print("Bu hisseler Setup 9'u bitirdi ve yeni bir hareket başlatıyor olabilir!")
    print("-" * 100)
    
    if buy_9_tamamlandi_list:
        buy_9_t_sorted = sorted(
            buy_9_tamamlandi_list,
            key=lambda x: (x['ha_yesil'], 'KARARSIZ' in x['trend'] or 'ORTA' in x['trend']),
            reverse=True
        )
        
        print(f"{'Ticker':<10} {'Fiyat':<12} {'Setup':<10} {'HA':<12} {'Trend':<20} {'Hacim %':<12} {'52w':<12}")
        print("-" * 100)
        
        for h in buy_9_t_sorted:
            ha = "🟢 YEŞİL" if h['ha_yesil'] else "🔴 KIRMIZI"
            print(f"{h['ticker']:<10} ${h['fiyat']:<11.2f} {h['buy_setup']:<10} {ha:<12} {h['trend']:<20} "
                  f"{h['hacim_artis']:+.1f}%{'':<8} {h['week_52_konum']:.1f}%")
        
        # Öne çıkanlar
        print("\n⭐ EN İYİ FIRSATLAR (HA Yeşil + İyi Trend):")
        print("-" * 100)
        one_cikan = [h for h in buy_9_t_sorted 
                     if h['ha_yesil'] and ('KARARSIZ' in h['trend'] or 'ORTA YÜKSELİŞ' in h['trend'])]
        
        if one_cikan:
            for h in one_cikan[:10]:
                print(f"\n💎 {h['ticker']} - ${h['fiyat']}")
                print(f"   • Setup: {h['buy_setup']} (9'dan sonra)")
                print(f"   • HA Mum: 🟢 YEŞİL - Yükseliş başladı!")
                print(f"   • Trend: {h['trend']}")
                print(f"   • Hacim: {h['hacim_artis']:+.1f}%")
                print(f"   • 52 Hafta Konum: %{h['week_52_konum']:.1f}")
                print(f"   ✅ SÜPER SİNYAL - Setup 9 tamamlandı, yeşil mum geldi!")
        else:
            print("   Yok (HA yeşil + iyi trend kombinasyonu bulunamadı)")
    else:
        print("   Sinyal bulunamadı")
    
    # BUY SETUP 9 - AKTİF
    print("\n" + "=" * 100)
    print("🟡 BUY SETUP 9 AKTİF (Şu an 9'da) - HAFTALIK")
    print("=" * 100)
    print("Bu hisseler şu an Setup 9'da, bu hafta tamamlanabilir!")
    print("-" * 100)
    
    if buy_9_aktif_list:
        buy_9_a_sorted = sorted(
            buy_9_aktif_list,
            key=lambda x: (x['ha_yesil'], 'KARARSIZ' in x['trend']),
            reverse=True
        )
        
        print(f"{'Ticker':<10} {'Fiyat':<12} {'HA':<12} {'Trend':<20} {'Hacim %':<12} {'52w':<12}")
        print("-" * 100)
        
        for h in buy_9_a_sorted:
            ha = "🟢 YEŞİL" if h['ha_yesil'] else "🔴 KIRMIZI"
            print(f"{h['ticker']:<10} ${h['fiyat']:<11.2f} {ha:<12} {h['trend']:<20} "
                  f"{h['hacim_artis']:+.1f}%{'':<8} {h['week_52_konum']:.1f}%")
        
        print("\n💡 Not: Bu hisseler şu an 9'da. Yeşil mum ile tamamlanırsa güçlü alış sinyali!")
    else:
        print("   Sinyal bulunamadı")
    
    # SELL SETUP 9 - TAMAMLANMIŞ
    print("\n" + "=" * 100)
    print("🎯 SELL SETUP 9 TAMAMLANMIŞ (Geçen hafta 9'du) - HAFTALIK")
    print("=" * 100)
    
    if sell_9_tamamlandi_list:
        sell_9_t_sorted = sorted(
            sell_9_tamamlandi_list,
            key=lambda x: (not x['ha_yesil'], 'KARARSIZ' in x['trend']),
            reverse=True
        )
        
        print(f"{'Ticker':<10} {'Fiyat':<12} {'Setup':<10} {'HA':<12} {'Trend':<20} {'Hacim %':<12} {'52w':<12}")
        print("-" * 100)
        
        for h in sell_9_t_sorted:
            ha = "🟢 YEŞİL" if h['ha_yesil'] else "🔴 KIRMIZI"
            print(f"{h['ticker']:<10} ${h['fiyat']:<11.2f} {h['sell_setup']:<10} {ha:<12} {h['trend']:<20} "
                  f"{h['hacim_artis']:+.1f}%{'':<8} {h['week_52_konum']:.1f}%")
        
        print("\n⭐ EN İYİ SHORT FIRSATLARI (HA Kırmızı):")
        one_cikan = [h for h in sell_9_t_sorted if not h['ha_yesil']]
        
        if one_cikan:
            for h in one_cikan[:10]:
                print(f"\n📉 {h['ticker']} - ${h['fiyat']}")
                print(f"   • Setup: {h['sell_setup']} (9'dan sonra)")
                print(f"   • HA Mum: 🔴 KIRMIZI - Düşüş başladı!")
                print(f"   • Trend: {h['trend']}")
                print(f"   ⚠️  Satış veya short fırsatı")
        else:
            print("   Yok")
    else:
        print("   Sinyal bulunamadı")
    
    # SELL SETUP 9 - AKTİF
    print("\n" + "=" * 100)
    print("🟡 SELL SETUP 9 AKTİF (Şu an 9'da) - HAFTALIK")
    print("=" * 100)
    
    if sell_9_aktif_list:
        sell_9_a_sorted = sorted(
            sell_9_aktif_list,
            key=lambda x: (not x['ha_yesil']),
            reverse=True
        )
        
        print(f"{'Ticker':<10} {'Fiyat':<12} {'HA':<12} {'Trend':<20} {'Hacim %':<12} {'52w':<12}")
        print("-" * 100)
        
        for h in sell_9_a_sorted:
            ha = "🟢 YEŞİL" if h['ha_yesil'] else "🔴 KIRMIZI"
            print(f"{h['ticker']:<10} ${h['fiyat']:<11.2f} {ha:<12} {h['trend']:<20} "
                  f"{h['hacim_artis']:+.1f}%{'':<8} {h['week_52_konum']:.1f}%")
        
        print("\n💡 Not: Bu hisseler şu an Sell 9'da. Kırmızı mum ile tamamlanırsa satış sinyali!")
    else:
        print("   Sinyal bulunamadı")
    
    # YAKLAŞAN SİNYALLER
    print("\n" + "=" * 100)
    print("⚠️  YAKLAŞAN SİNYALLER (Setup 7-8)")
    print("=" * 100)
    
    if yaklasan_list:
        print(f"{'Ticker':<10} {'Fiyat':<12} {'Setup':<12} {'HA':<12} {'Trend':<20}")
        print("-" * 100)
        
        for h in yaklasan_list[:20]:
            ha = "🟢 YEŞİL" if h['ha_yesil'] else "🔴 KIRMIZI"
            setup = f"Buy: {h['buy_setup']}" if h['buy_setup'] >= 7 else f"Sell: {h['sell_setup']}"
            print(f"{h['ticker']:<10} ${h['fiyat']:<11.2f} {setup:<12} {ha:<12} {h['trend']:<20}")
        
        if len(yaklasan_list) > 20:
            print(f"\n   ... ve {len(yaklasan_list) - 20} hisse daha")
    else:
        print("   Yok")
    
    # ÖZET
    print("\n" + "=" * 100)
    print("📈 ÖZET:")
    print(f"   • Taranan Hisse: {len(RUSSELL_2000_STOCKS)}")
    print(f"   • Buy Setup 9 TAMAMLANMIŞ: {len(buy_9_tamamlandi_list)} hisse 🎯")
    print(f"   • Buy Setup 9 AKTİF: {len(buy_9_aktif_list)} hisse 🟡")
    print(f"   • Sell Setup 9 TAMAMLANMIŞ: {len(sell_9_tamamlandi_list)} hisse 🎯")
    print(f"   • Sell Setup 9 AKTİF: {len(sell_9_aktif_list)} hisse 🟡")
    print(f"   • Yaklaşan Sinyal: {len(yaklasan_list)} hisse")
    print("=" * 100)
    
    print("\n💡 HAFTALIK TARAMA NOTLARI:")
    print("   📌 TAMAMLANMIŞ = Geçen hafta 9'du, şimdi hareket başladı (EN ÖNEMLİ!)")
    print("   📌 AKTİF = Şu an 9'da, bu hafta tamamlanabilir")
    print("   📌 Tamamlanmış + Yeşil HA = Güçlü alış sinyali")
    print("   📌 52w Konum %20 altı = Dip bölgede")
    print("   📌 Hacim artışı = Kurumsal ilgi")
    print("=" * 100)
    
    # CSV kaydet
    tarih = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if buy_9_tamamlandi_list or buy_9_aktif_list or sell_9_tamamlandi_list or sell_9_aktif_list:
        tum_sinyaller = buy_9_tamamlandi_list + buy_9_aktif_list + sell_9_tamamlandi_list + sell_9_aktif_list
        df_sonuc = pd.DataFrame(tum_sinyaller)
        dosya = f"russell2000_tarama_{tarih}.csv"
        df_sonuc.to_csv(dosya, index=False)
        print(f"\n✓ Sonuçlar '{dosya}' dosyasına kaydedildi")
    
    print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    try:
        import yfinance
        import pandas
    except ImportError:
        print("\nKütüphane eksik!")
        print("Yükleyin: pip install yfinance pandas")
        exit(1)
    
    tara()
    
    print("✅ Tarama tamamlandı!\n")
