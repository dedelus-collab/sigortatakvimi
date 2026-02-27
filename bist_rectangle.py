"""
BIST Bullish Rectangle Pattern Scanner
Robert D. Edwards - Technical Analysis of Stock Trends

AMAÇ: Sadece YUKARI KIRILIM potansiyeli yüksek rectangle'ları bul
- Fiyat dirence yakın
- Yükseliş momentumu var
- Hacim artışı mevcut
- Bullish chart pattern sinyalleri
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class BullishRectangleScanner:
    def __init__(self, min_periods=15, max_periods=60, tolerance=0.025):
        """
        Parameters:
        -----------
        min_periods : int
            Minimum dikdörtgen süresi (gün)
        max_periods : int
            Maximum dikdörtgen süresi (gün)
        tolerance : float
            Fiyat seviyelerindeki tolerans yüzdesi (0.025 = %2.5)
        """
        self.min_periods = min_periods
        self.max_periods = max_periods
        self.tolerance = tolerance
        
    def get_bist_stocks(self):
        """BIST 100 ve diğer önemli hisseler"""
        hisseler = [
            # BIST 30
            "AKBNK.IS", "ALARK.IS", "ARCLK.IS", "ASELS.IS", "BIMAS.IS",
            "EKGYO.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "GUBRF.IS",
            "HEKTS.IS", "ISCTR.IS", "KCHOL.IS", "KONTR.IS", "KOZAL.IS",
            "KOZAA.IS", "KRDMD.IS", "ODAS.IS", "PETKM.IS", "PGSUS.IS",
            "SAHOL.IS", "SASA.IS", "SISE.IS", "TAVHL.IS", "TCELL.IS",
            "THYAO.IS", "TOASO.IS", "TUPRS.IS", "VESTL.IS", "YKBNK.IS",
            
            # BIST 50 ek
            "AEFES.IS", "AKSA.IS", "AKSEN.IS", "AYGAZ.IS", "DOHOL.IS",
            "ENKAI.IS", "ENJSA.IS", "EUPWR.IS", "GOZDE.IS", "HALKB.IS",
            "ITTFH.IS", "ISGYO.IS", "MGROS.IS", "OYAKC.IS", "SOKM.IS",
            "TTKOM.IS", "TTRAK.IS", "ULKER.IS", "VACBT.IS", "YATAS.IS",
            
            # BIST 100 ek hisseler
            "AGHOL.IS", "AGROT.IS", "AHGAZ.IS", "AKCNS.IS", "AKENR.IS",
            "ALGYO.IS", "ALKIM.IS", "ALMAD.IS", "ANSGR.IS", "ARDYZ.IS",
            "ASTOR.IS", "ASUZU.IS", "ATEKS.IS", "AVGYO.IS", "AYDEM.IS",
            "BAGFS.IS", "BASGZ.IS", "BERA.IS", "BIENY.IS", "BINHO.IS",
            "BIZIM.IS", "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BNTAS.IS",
            "BOBET.IS", "BRISA.IS", "BRKSN.IS", "BRKVY.IS", "BRMEN.IS",
            "BRSAN.IS", "BRYAT.IS", "BSOKE.IS", "BTCIM.IS", "BUCIM.IS",
            "BURCE.IS", "BURVA.IS", "CANTE.IS", "CCOLA.IS", "CELHA.IS",
            "CEMAS.IS", "CEMTS.IS", "CIMSA.IS", "CLEBI.IS", "CMENT.IS",
            "CONSE.IS", "COSMO.IS", "CRDFA.IS", "CRFSA.IS", "CVKMD.IS",
            "CWENE.IS", "DAGHL.IS", "DAPGM.IS", "DARDL.IS", "DENGE.IS",
            "DERHL.IS", "DERIM.IS", "DESA.IS", "DESPC.IS", "DEVA.IS",
            "DGATE.IS", "DGGYO.IS", "DITAS.IS", "DMSAS.IS", "DNISI.IS",
            "DOAS.IS", "DOBUR.IS", "DOCO.IS", "DOFER.IS", "DOGUB.IS",
            "DOHOL.IS", "DOKTA.IS", "DURDO.IS", "DYOBY.IS", "DZGYO.IS",
            "ECILC.IS", "ECZYT.IS", "EDIP.IS", "EGEEN.IS", "EGEPO.IS",
            "EGGUB.IS", "EGPRO.IS", "EGSER.IS", "EKIZ.IS", "ELITE.IS",
            "EMKEL.IS", "EMNIS.IS", "ENERY.IS", "ENJSA.IS", "ENSRI.IS",
            "EPLAS.IS", "ERBOS.IS", "ERSU.IS", "ESCAR.IS", "ESCOM.IS",
            "ESEN.IS", "ETILR.IS", "ETYAT.IS", "EUKYO.IS", "EUREN.IS",
            "EYGYO.IS", "FADE.IS", "FENER.IS", "FLAP.IS", "FMIZP.IS",
            "FONET.IS", "FORMT.IS", "FORTE.IS", "FRIGO.IS", "GARAN.IS",
            "GARFA.IS", "GEDIK.IS", "GEDZA.IS", "GENIL.IS", "GENTS.IS",
            "GEREL.IS", "GESAN.IS", "GLBMD.IS", "GLCVY.IS", "GLYHO.IS",
            "GMTAS.IS", "GOKNR.IS", "GOLTS.IS", "GOODY.IS", "GSDDE.IS",
            "GSDHO.IS", "GSRAY.IS", "GUBRF.IS", "GUNDG.IS", "GWIND.IS",
            "GZNMI.IS", "HALKB.IS", "HATEK.IS", "HATSN.IS", "HDFGS.IS",
            "HEDEF.IS", "HEKTS.IS", "HOROZ.IS", "HRKET.IS", "HTTBT.IS",
            "HUBVC.IS", "HUNER.IS", "HURGZ.IS", "ICBCT.IS", "ICUGS.IS",
            "IDEAS.IS", "IDGYO.IS", "IEYHO.IS", "IHEVA.IS", "IHGZT.IS",
            "IHLAS.IS", "IHLGM.IS", "IHYAY.IS", "INDES.IS", "INFO.IS",
            "INGRM.IS", "INTEM.IS", "INVEO.IS", "INVES.IS", "IPEKE.IS",
            "ISBIR.IS", "ISBTR.IS", "ISCTR.IS", "ISDMR.IS", "ISGSY.IS",
            "ISGYO.IS", "ISKPL.IS", "ISKUR.IS", "ISMEN.IS", "ITTFH.IS",
            "IZMDC.IS", "IZFAS.IS", "IZINV.IS", "JANTS.IS", "KAPLM.IS",
            "KAREL.IS", "KARSN.IS", "KARTN.IS", "KARYE.IS", "KATMR.IS",
            "KAYSE.IS", "KBORU.IS", "KCAER.IS", "KCHOL.IS", "KENT.IS",
            "KERVN.IS", "KERVT.IS", "KFEIN.IS", "KGYO.IS", "KIMMR.IS",
            "KLGYO.IS", "KLKIM.IS", "KLMSN.IS", "KLRHO.IS", "KLSER.IS",
            "KLSYN.IS", "KMPUR.IS", "KNFRT.IS", "KONKA.IS", "KONTR.IS",
            "KONYA.IS", "KOPOL.IS", "KORDS.IS", "KORNE.IS", "KOTON.IS",
            "KOZAA.IS", "KOZAL.IS", "KRDMA.IS", "KRDMB.IS", "KRDMD.IS",
            "KRGYO.IS", "KRONT.IS", "KRPLS.IS", "KRSTL.IS", "KRTEK.IS",
            "KRVGD.IS", "KSTUR.IS", "KTLEV.IS", "KTSKR.IS", "KUTPO.IS",
            "KUVVA.IS", "KUYAS.IS", "KZBGY.IS", "KZGYO.IS", "LIDER.IS",
            "LINK.IS", "LKMNH.IS", "LOGO.IS", "LRSHO.IS", "LUKSK.IS",
            "MAALT.IS", "MACKO.IS", "MAGEN.IS", "MAKIM.IS", "MAKTK.IS",
            "MANAS.IS", "MARBL.IS", "MARKA.IS", "MARTI.IS", "MARUL.IS",
            "MAVI.IS", "MEDTR.IS", "MEGAP.IS", "MEGMT.IS", "MEKAG.IS",
            "MEPET.IS", "MERCN.IS", "MERKO.IS", "METRO.IS", "METUR.IS",
            "MGROS.IS", "MHRGY.IS", "MIATK.IS", "MJICA.IS", "MNDRS.IS",
            "MNDTR.IS", "MOBTL.IS", "MOGAN.IS", "MPARK.IS", "MRGYO.IS",
            "MRSHL.IS", "MSGYO.IS", "MTRKS.IS", "MTRYO.IS", "MZHLD.IS",
            "NATEN.IS", "NETAS.IS", "NIBAS.IS", "NTHOL.IS", "NTGAZ.IS",
            "NUHCM.IS", "NUGYO.IS", "OBASE.IS", "ODAS.IS", "ODJE.IS",
            "ODINE.IS", "OFSYM.IS", "ONCSM.IS", "ORCAY.IS", "ORGE.IS",
            "ORMA.IS", "OSMEN.IS", "OSTIM.IS", "OTKAR.IS", "OTTO.IS",
            "OYAKC.IS", "OYAYO.IS", "OYLUM.IS", "OYYAT.IS", "OZBAL.IS",
            "OZEN.IS", "OZGYO.IS", "OZKGY.IS", "OZRDN.IS", "OZSUB.IS",
            "PAMEL.IS", "PAPIL.IS", "PARSN.IS", "PASEU.IS", "PATEK.IS",
            "PAVIP.IS", "PEHOL.IS", "PEKGY.IS", "PENGD.IS", "PENTA.IS",
            "PETKM.IS", "PETUN.IS", "PGSUS.IS", "PHOLS.IS", "PINSU.IS",
            "PKART.IS", "PKENT.IS", "PLTUR.IS", "PNLSN.IS", "PNSUT.IS",
            "POLHO.IS", "POLTK.IS", "PRDGS.IS", "PRKAB.IS", "PRKME.IS",
            "PRZMA.IS", "PSDTC.IS", "PSGYO.IS", "QNBFB.IS", "QNBFL.IS",
            "QUAGR.IS", "RALYH.IS", "RAYSG.IS", "REASN.IS", "REYSN.IS",
            "RGYAS.IS", "RNPOL.IS", "RODRG.IS", "ROYAL.IS", "RTALB.IS",
            "RUBNS.IS", "RYGYO.IS", "RYSAS.IS", "SAFKR.IS", "SAHOL.IS",
            "SAMAT.IS", "SANEL.IS", "SANFM.IS", "SANKO.IS", "SARKY.IS",
            "SASA.IS", "SAYAS.IS", "SDTTR.IS", "SEGYO.IS", "SEKFK.IS",
            "SEKUR.IS", "SELEC.IS", "SELGD.IS", "SELVA.IS", "SEYKM.IS",
            "SILVR.IS", "SISE.IS", "SKBNK.IS", "SKTAS.IS", "SMART.IS",
            "SMRTG.IS", "SNGYO.IS", "SNICA.IS", "SNKRN.IS", "SNPAM.IS",
            "SODSN.IS", "SOKM.IS", "SONME.IS", "SRVGY.IS", "SUMAS.IS",
            "SUNTK.IS", "SUWEN.IS", "TATGD.IS", "TBORG.IS", "TCELL.IS",
            "TCZYT.IS", "TDGYO.IS", "TEKTU.IS", "TERA.IS", "TGSAS.IS",
            "THYAO.IS", "TKFEN.IS", "TKNSA.IS", "TLMAN.IS", "TMPOL.IS",
            "TMSN.IS", "TOASO.IS", "TRCAS.IS", "TRGYO.IS", "TRILC.IS",
            "TSGYO.IS", "TSKB.IS", "TSPOR.IS", "TTKOM.IS", "TTRAK.IS",
            "TUCLK.IS", "TUKAS.IS", "TUPRS.IS", "TUREX.IS", "TURGG.IS",
            "TURSG.IS", "UFUK.IS", "ULAS.IS", "ULKER.IS", "ULUFA.IS",
            "ULUSE.IS", "ULUUN.IS", "UMPAS.IS", "UNLU.IS", "USAK.IS",
            "UZERB.IS", "VAKBN.IS", "VAKFN.IS", "VAKKO.IS", "VANGD.IS",
            "VBTYZ.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "VKFYO.IS",
            "VKING.IS", "VKGYO.IS", "YAPRK.IS", "YATAS.IS", "YATVK.IS",
            "YAZIC.IS", "YEOTK.IS", "YESIL.IS", "YGGYO.IS", "YGYO.IS",
            "YKBNK.IS", "YKSLN.IS", "YUNSA.IS", "YYLGD.IS", "ZEDUR.IS",
            "ZELOT.IS", "ZOREN.IS", "ZRGYO.IS"
        ]
        return hisseler
    
    def download_data(self, symbol, period='6mo'):
        """Hisse verilerini indir"""
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            if df.empty:
                return None
            return df
        except Exception as e:
            return None
    
    def find_swing_points(self, df, window=5):
        """Swing high ve swing low noktalarını bul"""
        highs = df['High'].values
        lows = df['Low'].values
        
        swing_highs = []
        swing_lows = []
        
        for i in range(window, len(df) - window):
            if all(highs[i] >= highs[i-window:i]) and all(highs[i] >= highs[i+1:i+window+1]):
                swing_highs.append((i, highs[i], df.index[i]))
            
            if all(lows[i] <= lows[i-window:i]) and all(lows[i] <= lows[i+1:i+window+1]):
                swing_lows.append((i, lows[i], df.index[i]))
        
        return swing_highs, swing_lows
    
    def check_recent_activity(self, swing_points, days_threshold=10):
        """Son X gün içinde test olmuş mu kontrol et"""
        if not swing_points:
            return False
        
        latest_swing_date = swing_points[-1][2]
        
        if latest_swing_date.tz is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
            if hasattr(latest_swing_date, 'to_pydatetime'):
                latest_swing_date = latest_swing_date.to_pydatetime().replace(tzinfo=None)
        
        days_ago = (now - latest_swing_date).days
        return days_ago <= days_threshold
    
    def calculate_bullish_score(self, df, pattern_data):
        """Bullish kırılım olasılığını skorla (0-100)"""
        score = 0
        reasons = []
        
        # 1. FİYAT POZİSYONU (Max 30 puan)
        price_pos = pattern_data['price_position_pct']
        if price_pos >= 70:  # Rectangle'ın üst %30'unda
            score += 30
            reasons.append("Fiyat dirence çok yakın (%{:.0f})".format(price_pos))
        elif price_pos >= 50:
            score += 20
            reasons.append("Fiyat direncin üst yarısında")
        elif price_pos >= 40:
            score += 10
            reasons.append("Fiyat orta-üst bölgede")
        
        # 2. MOMENTUM (Max 25 puan)
        last_10 = df['Close'].tail(10)
        bullish_days = sum(last_10.pct_change() > 0)
        
        if bullish_days >= 7:  # Son 10 günün 7+ pozitif
            score += 25
            reasons.append("Güçlü yükseliş momentumu (10 günün {}/10'u pozitif)".format(bullish_days))
        elif bullish_days >= 6:
            score += 20
            reasons.append("İyi yükseliş momentumu")
        elif bullish_days >= 5:
            score += 12
            reasons.append("Pozitif momentum")
        
        # 3. HACİM TRENDİ (Max 20 puan)
        volume_inc = pattern_data['volume_increase_pct']
        if volume_inc > 30:  # %30+ hacim artışı
            score += 20
            reasons.append("Hacim güçlü artışta (%{:.0f})".format(volume_inc))
        elif volume_inc > 15:
            score += 15
            reasons.append("Hacim artışta")
        elif volume_inc > 5:
            score += 8
            reasons.append("Hafif hacim artışı")
        
        # 4. DİRENÇ TESTLERİ (Max 15 puan)
        if pattern_data['recent_high_test']:
            score += 15
            reasons.append("Son 10 gün içinde direnç testi var")
        elif pattern_data['swing_highs_count'] >= 3:
            score += 8
            reasons.append("Direnci {} kez test etti".format(pattern_data['swing_highs_count']))
        
        # 5. MUM PATTERN (Max 10 puan)
        last_3 = df.tail(3)
        bullish_candles = sum(last_3['Close'] > last_3['Open'])
        
        if bullish_candles == 3:  # 3 yeşil mum üst üste
            score += 10
            reasons.append("3 yeşil mum üst üste")
        elif bullish_candles == 2:
            score += 6
            reasons.append("Son 3 günde 2 yeşil mum")
        
        return score, reasons
    
    def detect_bullish_rectangle(self, df):
        """Bullish rectangle pattern tespit et"""
        if len(df) < self.min_periods:
            return None
        
        recent_df = df.tail(self.max_periods).copy()
        swing_highs, swing_lows = self.find_swing_points(recent_df)
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return None
        
        high_levels = [h[1] for h in swing_highs]
        low_levels = [l[1] for l in swing_lows]
        
        resistance = np.mean(high_levels)
        support = np.mean(low_levels)
        
        resistance_tolerance = resistance * self.tolerance
        support_tolerance = support * self.tolerance
        
        valid_highs = sum(1 for h in high_levels if abs(h - resistance) <= resistance_tolerance)
        valid_lows = sum(1 for l in low_levels if abs(l - support) <= support_tolerance)
        
        if valid_highs / len(high_levels) < 0.6 or valid_lows / len(low_levels) < 0.6:
            return None
        
        rect_height = resistance - support
        rect_height_pct = (rect_height / support) * 100
        
        if rect_height_pct < 3:
            return None
        
        first_swing = min(swing_highs[0][0], swing_lows[0][0])
        last_swing = max(swing_highs[-1][0], swing_lows[-1][0])
        duration = last_swing - first_swing
        
        if duration < self.min_periods:
            return None
        
        current_price = recent_df['Close'].iloc[-1]
        last_5_closes = recent_df['Close'].tail(5)
        
        upper_breakout = sum(last_5_closes > resistance * 1.02) >= 2
        lower_breakout = sum(last_5_closes < support * 0.98) >= 2
        
        if upper_breakout or lower_breakout:
            return None
        
        if current_price < support * 0.97 or current_price > resistance * 1.03:
            return None
        
        recent_high_test = self.check_recent_activity(swing_highs, days_threshold=10)
        recent_low_test = self.check_recent_activity(swing_lows, days_threshold=10)
        
        if not (recent_high_test or recent_low_test):
            return None
        
        # *** BULLISH FİLTRE: Fiyat en az orta seviyede olmalı ***
        price_position = ((current_price - support) / (resistance - support)) * 100
        
        if price_position < 35:  # Rectangle'ın alt %35'inde ise bullish değil
            return None
        
        distance_to_resistance = ((resistance - current_price) / current_price) * 100
        distance_to_support = ((current_price - support) / current_price) * 100
        
        avg_volume = recent_df['Volume'].iloc[:-5].mean()
        recent_volume = recent_df['Volume'].tail(5).mean()
        volume_increase = ((recent_volume - avg_volume) / avg_volume) * 100
        
        pattern_data = {
            'resistance': resistance,
            'support': support,
            'height_pct': rect_height_pct,
            'duration': duration,
            'current_price': current_price,
            'price_position_pct': price_position,
            'distance_to_resistance': distance_to_resistance,
            'distance_to_support': distance_to_support,
            'swing_highs_count': len(swing_highs),
            'swing_lows_count': len(swing_lows),
            'recent_high_test': recent_high_test,
            'recent_low_test': recent_low_test,
            'volume_increase_pct': volume_increase,
            'target_up': resistance + rect_height,
            'data': recent_df
        }
        
        # Bullish skoru hesapla
        bullish_score, reasons = self.calculate_bullish_score(recent_df, pattern_data)
        
        # *** BULLISH FİLTRE: Minimum 40 puan gerekli ***
        if bullish_score < 40:
            return None
        
        pattern_data['bullish_score'] = bullish_score
        pattern_data['bullish_reasons'] = reasons
        
        return pattern_data
    
    def scan_all_stocks(self):
        """Tüm hisseleri tara"""
        stocks = self.get_bist_stocks()
        results = []
        
        print(f"{'='*90}")
        print(f"🚀 BIST BULLISH RECTANGLE PATTERN TARAMASI 🚀")
        print(f"Sadece YUKARI KIRILIM Potansiyeli Yüksek Hisseler")
        print(f"{'='*90}\n")
        print(f"Taranacak hisse sayısı: {len(stocks)} (BIST 100 + Diğer Önemli Hisseler)\n")
        
        for i, symbol in enumerate(stocks, 1):
            print(f"[{i}/{len(stocks)}] {symbol:12} taranıyor...", end=' ')
            
            df = self.download_data(symbol)
            if df is None or len(df) < self.min_periods:
                print("❌")
                continue
            
            pattern = self.detect_bullish_rectangle(df)
            if pattern:
                results.append({
                    'symbol': symbol,
                    'name': symbol.replace('.IS', ''),
                    **pattern
                })
                print(f"✅ BULLISH! (Skor: {pattern['bullish_score']}/100)")
            else:
                print("⚪")
        
        return results
    
    def generate_report(self, results):
        """Detaylı rapor oluştur"""
        if not results:
            print("\n❌ Bullish rectangle pattern bulunamadı!")
            print("   (Kriterleri karşılayan hisse yok veya piyasa düşüş trendinde)\n")
            return None
        
        print(f"\n{'='*90}")
        print(f"🎯 BULLISH RECTANGLE SONUÇLARI - {len(results)} HİSSE BULUNDU")
        print(f"{'='*90}\n")
        
        df_report = pd.DataFrame(results)
        df_report = df_report.sort_values('bullish_score', ascending=False)
        
        for idx, row in df_report.iterrows():
            print(f"\n{'='*90}")
            print(f"🚀 {row['name']:8} - BULLISH SKOR: {row['bullish_score']}/100")
            print(f"{'='*90}")
            print(f"   💰 MEVCUT FİYAT: {row['current_price']:.2f} TL")
            print(f"   📈 DİRENÇ:       {row['resistance']:.2f} TL  (↑{row['distance_to_resistance']:.1f}%)")
            print(f"   📉 DESTEK:       {row['support']:.2f} TL  (↓{row['distance_to_support']:.1f}%)")
            print(f"   📏 YÜKSEKLIK:    %{row['height_pct']:.1f}")
            print(f"   📍 POZİSYON:     Rectangle içinde %{row['price_position_pct']:.0f} seviyesinde")
            print(f"")
            print(f"   🎯 YUKARI KIRILIM HEDEFİ: {row['target_up']:.2f} TL (+%{row['height_pct']:.1f})")
            print(f"   ⏱️  SÜRE: {row['duration']} gün")
            print(f"")
            print(f"   ✅ BULLISH SİNYALLER:")
            for reason in row['bullish_reasons']:
                print(f"      • {reason}")
            print(f"")
            print(f"   📊 DETAYLAR:")
            print(f"      Direnç testleri: {row['swing_highs_count']} kez")
            print(f"      Destek testleri: {row['swing_lows_count']} kez")
        
        print(f"\n{'='*90}\n")
        
        # Özet tablo
        print("\n📋 BULLISH RECTANGLE ÖZET TABLOSU (Skora Göre Sıralı):")
        print("-" * 90)
        summary = df_report[['name', 'bullish_score', 'current_price', 'resistance', 
                            'distance_to_resistance', 'target_up', 'height_pct']].copy()
        summary.columns = ['Hisse', 'Skor', 'Fiyat', 'Direnç', 'Dirence(%)', 'Hedef', 'Potansiyel(%)']
        summary = summary.round(2)
        
        print(summary.to_string(index=False))
        print("-" * 90)
        
        return df_report
    
    def plot_pattern(self, symbol, pattern_data, save_path=None):
        """Bullish pattern görselleştirmesi"""
        df = pattern_data['data']
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 2, height_ratios=[3, 1, 1], hspace=0.3, wspace=0.3)
        
        ax1 = fig.add_subplot(gs[0, :])
        
        # Mum grafik
        for i in range(len(df)):
            color = 'green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red'
            ax1.plot([df.index[i], df.index[i]], 
                    [df['Low'].iloc[i], df['High'].iloc[i]], 
                    color=color, linewidth=0.8, alpha=0.7)
            ax1.plot([df.index[i], df.index[i]], 
                    [df['Open'].iloc[i], df['Close'].iloc[i]], 
                    color=color, linewidth=3, alpha=0.9)
        
        # Seviyeler
        ax1.axhline(y=pattern_data['resistance'], color='red', 
                   linestyle='--', linewidth=2.5, label=f"🔴 Direnç: {pattern_data['resistance']:.2f} TL", alpha=0.8)
        ax1.axhline(y=pattern_data['support'], color='green', 
                   linestyle='--', linewidth=2.5, label=f"🟢 Destek: {pattern_data['support']:.2f} TL", alpha=0.8)
        ax1.axhline(y=pattern_data['target_up'], color='darkgreen', 
                   linestyle=':', linewidth=2, label=f"🎯 Hedef: {pattern_data['target_up']:.2f} TL", alpha=0.7)
        ax1.axhline(y=pattern_data['current_price'], color='blue', 
                   linestyle='-', linewidth=2, label=f"💰 Mevcut: {pattern_data['current_price']:.2f} TL", alpha=0.7)
        
        ax1.fill_between(df.index, pattern_data['support'], pattern_data['resistance'], 
                        alpha=0.15, color='purple', label='Rectangle Zone')
        
        ax1.set_title(f'🚀 {symbol} - BULLISH RECTANGLE | Skor: {pattern_data["bullish_score"]}/100', 
                     fontsize=16, fontweight='bold', pad=20)
        ax1.set_ylabel('Fiyat (TL)', fontsize=13, fontweight='bold')
        ax1.legend(loc='upper left', fontsize=10, framealpha=0.9)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # Hacim
        ax2 = fig.add_subplot(gs[1, :])
        colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red' 
                 for i in range(len(df))]
        ax2.bar(df.index, df['Volume'], color=colors, alpha=0.6)
        ax2.axhline(y=df['Volume'].mean(), color='orange', 
                   linestyle='--', linewidth=2, alpha=0.8, label='Ortalama Hacim')
        ax2.set_ylabel('Hacim', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper left', fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # Bullish sinyaller paneli
        ax3 = fig.add_subplot(gs[2, 0])
        ax3.axis('off')
        
        signals_text = "🚀 BULLISH SİNYALLER\n" + "━"*35 + "\n"
        for reason in pattern_data['bullish_reasons']:
            signals_text += f"✓ {reason}\n"
        
        ax3.text(0.1, 0.5, signals_text, fontsize=9, verticalalignment='center',
                family='monospace', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
        
        # İstatistik paneli
        ax4 = fig.add_subplot(gs[2, 1])
        ax4.axis('off')
        stats_text = f"""
        📊 PATTERN BİLGİLERİ
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        Bullish Skor: {pattern_data['bullish_score']}/100
        Rectangle Yüksekliği: %{pattern_data['height_pct']:.1f}
        Süre: {pattern_data['duration']} gün
        
        🎯 HEDEF
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        Yukarı Kırılım: {pattern_data['target_up']:.2f} TL
        Potansiyel Kazanç: %{pattern_data['height_pct']:.1f}
        """
        ax4.text(0.1, 0.5, stats_text, fontsize=9, verticalalignment='center',
                family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        return fig

def main():
    """Ana program"""
    print("\n" + "="*90)
    print("🚀 BIST BULLISH RECTANGLE PATTERN SCANNER 🚀")
    print("Robert D. Edwards - Technical Analysis of Stock Trends")
    print("Sadece YUKARI KIRILIM Potansiyeli Yüksek Hisseler")
    print("="*90 + "\n")
    
    scanner = BullishRectangleScanner(
        min_periods=15,
        max_periods=60,
        tolerance=0.025
    )
    
    results = scanner.scan_all_stocks()
    df_report = scanner.generate_report(results)
    
    if results:
        df_report.to_csv('bullish_rectangle_patterns.csv', index=False, encoding='utf-8-sig')
        print(f"\n✅ Sonuçlar 'bullish_rectangle_patterns.csv' dosyasına kaydedildi.\n")
        
        print("📈 Grafikler oluşturuluyor...\n")
        for i, result in enumerate(results, 1):
            fig = scanner.plot_pattern(
                result['name'], 
                result,
                save_path=f"bullish_{result['name']}_skor{result['bullish_score']}.png"
            )
            print(f"   [{i}/{len(results)}] Grafik: bullish_{result['name']}_skor{result['bullish_score']}.png")
            plt.close(fig)
        
        print("\n✅ Tüm grafikler oluşturuldu!")
        print("="*90)
        print("💡 İPUCU: En yüksek skorlu hisseler en güçlü bullish sinyallere sahip.")
        print("="*90 + "\n")

if __name__ == "__main__":
    main()