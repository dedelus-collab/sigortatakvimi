"""
BIST Tüm Hisse Senetlerinde TD Sequential + Heiken Ashi Haftalık Tarayıcı
BIST'teki tüm hisseleri otomatik olarak tarar
Geçmiş Buy Setup 9 sinyallerinin başarı oranını analiz eder
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
import time
warnings.filterwarnings('ignore')

def bist_tum_hisseler_cek():
    """
    BIST'te işlem gören tüm hisse senetlerini çeker
    Manuel olarak hazırlanmış güncel liste
    """
    # BIST 100 ve diğer önemli hisseler
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
    
    # Tekrarları temizle ve sırala
    hisseler = sorted(list(set(hisseler)))
    
    print(f"✓ Toplam {len(hisseler)} hisse yüklendi")
    return hisseler

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
    Trend gücü hesaplama
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

def buy_setup_basari_orani_analiz(df):
    """
    Geçmiş Buy Setup 9 sinyallerinin başarı oranını analiz eder
    Başarı oranı ve ortalama kazanç yüzdesini döndürür
    """
    buy_setup_9_sinyaller = []
    
    # Geçmiş verideki tüm Buy Setup 9 oluşumlarını bul
    for i in range(len(df)):
        if df['buy_setup'].iloc[i] == 9:
            buy_setup_9_sinyaller.append(i)
    
    if len(buy_setup_9_sinyaller) == 0:
        return None, None, 0
    
    basarili_sinyal = 0
    toplam_kazanc = 0
    kazanc_listesi = []
    
    # Her Buy Setup 9 sinyalini analiz et
    for sinyal_idx in buy_setup_9_sinyaller:
        # Sinyal sonrası en az 20 gün olmalı
        if sinyal_idx + 20 >= len(df):
            continue
        
        sinyal_fiyat = df['Close'].iloc[sinyal_idx]
        
        # Sonraki 20 gündeki fiyatları kontrol et
        sonraki_max_fiyat = df['Close'].iloc[sinyal_idx+1:sinyal_idx+21].max()
        
        # Kazanç yüzdesini hesapla
        kazanc_yuzde = ((sonraki_max_fiyat - sinyal_fiyat) / sinyal_fiyat) * 100
        kazanc_listesi.append(kazanc_yuzde)
        toplam_kazanc += kazanc_yuzde
        
        # %2'den fazla kazanç varsa başarılı say
        if kazanc_yuzde > 2:
            basarili_sinyal += 1
    
    if len(kazanc_listesi) == 0:
        return None, None, 0
    
    basari_orani = (basarili_sinyal / len(kazanc_listesi)) * 100
    ortalama_kazanc = toplam_kazanc / len(kazanc_listesi)
    
    return basari_orani, ortalama_kazanc, len(kazanc_listesi)

def hisse_tara(sembol, periyot="3mo"):
    """
    Tek bir hisse senedini tarar
    """
    try:
        hisse = yf.Ticker(sembol)
        df = hisse.history(period=periyot, interval="1d")
        
        if df.empty or len(df) < 10:
            return None
        
        df = td_sequential_heiken_ashi(df)
        trend_gucu = trend_gucu_hesapla(df)
        
        son_buy_setup = df['buy_setup'].iloc[-1]
        son_sell_setup = df['sell_setup'].iloc[-1]
        son_fiyat = df['Close'].iloc[-1]
        son_ha_close = df['HA_Close'].iloc[-1]
        son_ha_open = df['HA_Open'].iloc[-1]
        son_trend = df['ha_trend'].iloc[-1]
        
        ha_renk = "🟢 YEŞİL" if son_ha_close > son_ha_open else "🔴 KIRMIZI"
        
        sonuc = {
            'sembol': sembol.replace('.IS', ''),
            'son_fiyat': round(son_fiyat, 2),
            'ha_close': round(son_ha_close, 2),
            'ha_open': round(son_ha_open, 2),
            'ha_renk': ha_renk,
            'ha_trend': son_trend,
            'trend_gucu': trend_gucu,
            'buy_setup_9': son_buy_setup == 9,
            'sell_setup_9': son_sell_setup == 9,
            'buy_setup': int(son_buy_setup),
            'sell_setup': int(son_sell_setup),
            'tarih': df.index[-1].strftime('%Y-%m-%d'),
            'basari_orani': None,
            'ort_kazanc': None,
            'sinyal_sayisi': 0
        }
        
        return sonuc
        
    except Exception as e:
        return None

def buy_setup_gecmis_analiz(sembol):
    """
    Buy Setup 9 olan hisseler için daha uzun geçmiş veriyle detaylı analiz
    """
    try:
        hisse = yf.Ticker(sembol)
        # 2 yıllık veri al (daha iyi geçmiş analiz için)
        df = hisse.history(period="2y", interval="1d")
        
        if df.empty or len(df) < 50:
            return None
        
        df = td_sequential_heiken_ashi(df)
        
        # Geçmiş Buy Setup 9 başarı oranını analiz et
        basari_orani, ort_kazanc, sinyal_sayisi = buy_setup_basari_orani_analiz(df)
        
        # Güncel sinyal bilgilerini al
        son_buy_setup = df['buy_setup'].iloc[-1]
        son_fiyat = df['Close'].iloc[-1]
        son_ha_close = df['HA_Close'].iloc[-1]
        son_ha_open = df['HA_Open'].iloc[-1]
        trend_gucu = trend_gucu_hesapla(df)
        
        ha_renk = "🟢 YEŞİL" if son_ha_close > son_ha_open else "🔴 KIRMIZI"
        
        sonuc = {
            'sembol': sembol.replace('.IS', ''),
            'son_fiyat': round(son_fiyat, 2),
            'ha_close': round(son_ha_close, 2),
            'ha_open': round(son_ha_open, 2),
            'ha_renk': ha_renk,
            'trend_gucu': trend_gucu,
            'basari_orani': round(basari_orani, 1) if basari_orani else None,
            'ort_kazanc': round(ort_kazanc, 2) if ort_kazanc else None,
            'sinyal_sayisi': sinyal_sayisi,
            'tarih': df.index[-1].strftime('%Y-%m-%d')
        }
        
        return sonuc
        
    except Exception as e:
        return None

def tum_hisseleri_tara():
    """
    BIST'teki tüm hisseleri tarar
    """
    print("=" * 90)
    print("BIST TÜM HİSSELER - TD SEQUENTIAL + HEİKEN ASHI HAFTALIK TARAMA")
    print("=" * 90)
    print(f"Tarama Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    
    # Hisse listesini çek
    bist_hisseler = bist_tum_hisseler_cek()
    print(f"Taranan Hisse Sayısı: {len(bist_hisseler)}")
    print("=" * 90)
    print("\nTarama başlatılıyor... (Bu işlem birkaç dakika sürebilir)\n")
    
    buy_setup_9_list = []
    sell_setup_9_list = []
    diger_sinyaller = []
    basarisiz = 0
    
    # İlerleme çubuğu için
    toplam = len(bist_hisseler)
    
    # Her hisseyi tara
    for i, sembol in enumerate(bist_hisseler, 1):
        # İlerleme göster
        yuzde = (i / toplam) * 100
        print(f"İlerleme: [{i}/{toplam}] %{yuzde:.1f} - {sembol:15s}", end='\r')
        
        sonuc = hisse_tara(sembol)
        
        if sonuc:
            if sonuc['buy_setup_9']:
                buy_setup_9_list.append(sonuc)
            elif sonuc['sell_setup_9']:
                sell_setup_9_list.append(sonuc)
            elif sonuc['buy_setup'] >= 7 or sonuc['sell_setup'] >= 7:
                diger_sinyaller.append(sonuc)
        else:
            basarisiz += 1
        
        # API rate limit için kısa bekleme
        if i % 10 == 0:
            time.sleep(0.5)
    
    print("\n" + "=" * 90)
    print(f"✓ Tarama tamamlandı!")
    print(f"  • Başarılı: {toplam - basarisiz}")
    print(f"  • Başarısız: {basarisiz}")
    print("=" * 90)
    
    # Sonuçları göster - BUY SETUP 9
    print("\n🟢 BUY SETUP 9 (ALIŞ SİNYALİ) - Heiken Ashi Haftalık:")
    print("-" * 90)
    if buy_setup_9_list:
        # Trend gücüne göre sırala
        buy_setup_9_list_sorted = sorted(buy_setup_9_list, 
                                        key=lambda x: (x['ha_renk'] == "🟢 YEŞİL", 
                                                      "KARARSIZ" in x['trend_gucu'],
                                                      "ORTA" in x['trend_gucu']), 
                                        reverse=True)
        for h in buy_setup_9_list_sorted:
            print(f"  {h['sembol']:10s} | Fiyat: {h['son_fiyat']:8.2f} TL | HA: {h['ha_renk']} | "
                  f"Trend: {h['trend_gucu']:18s} | {h['tarih']}")
    else:
        print("  Sinyal bulunamadı")
    
    # GEÇMİŞ BAŞARI ORANI ANALİZİ - BUY SETUP 9
    if buy_setup_9_list:
        print("\n" + "=" * 90)
        print("📊 GEÇMİŞ BUY SETUP 9 BAŞARI ORANI ANALİZİ")
        print("=" * 90)
        print("Geçmiş Buy Setup 9 sinyalleri analiz ediliyor (2 yıllık veri)...")
        print("Başarı = Sinyal sonrası 20 gün içinde fiyat %2'den fazla yükseldi\n")
        
        gecmis_sonuclar = []
        
        for i, h in enumerate(buy_setup_9_list_sorted, 1):
            print(f"{h['sembol']} analiz ediliyor... [{i}/{len(buy_setup_9_list_sorted)}]", end='\r')
            
            gecmis_veri = buy_setup_gecmis_analiz(h['sembol'] + '.IS')
            if gecmis_veri:
                gecmis_sonuclar.append(gecmis_veri)
            
            # Kısa bekleme
            if i % 5 == 0:
                time.sleep(0.3)
        
        print("\n" + "-" * 90)
        
        if gecmis_sonuclar:
            # Başarı oranına göre sırala
            gecmis_sonuclar_sirali = sorted(
                gecmis_sonuclar, 
                key=lambda x: (x['basari_orani'] if x['basari_orani'] else 0), 
                reverse=True
            )
            
            print(f"\n{'Sembol':<10} {'Fiyat':<12} {'HA Renk':<15} {'Trend':<18} "
                  f"{'Başarı Oranı':<18} {'Ort Kazanç':<15} {'Sinyal':<10}")
            print("-" * 90)
            
            toplam_basari = 0
            toplam_sinyal = 0
            gecerli_hisse = 0
            
            for h in gecmis_sonuclar_sirali:
                if h['basari_orani'] is not None:
                    basari_gostergesi = "✅" if h['basari_orani'] >= 60 else "⚠️" if h['basari_orani'] >= 40 else "❌"
                    kazanc_gostergesi = "📈" if h['ort_kazanc'] and h['ort_kazanc'] > 5 else "📊" if h['ort_kazanc'] and h['ort_kazanc'] > 2 else "📉"
                    
                    print(f"{h['sembol']:<10} {h['son_fiyat']:<12.2f} {h['ha_renk']:<15} {h['trend_gucu']:<18} "
                          f"{basari_gostergesi} %{h['basari_orani']:>5.1f}{'':<10} {kazanc_gostergesi} %{h['ort_kazanc']:>6.2f}{'':<6} {h['sinyal_sayisi']:>3} kez")
                    
                    toplam_basari += h['basari_orani']
                    toplam_sinyal += h['sinyal_sayisi']
                    gecerli_hisse += 1
                else:
                    print(f"{h['sembol']:<10} {h['son_fiyat']:<12.2f} {h['ha_renk']:<15} {h['trend_gucu']:<18} "
                          f"{'Yeterli veri yok':<18} {'N/A':<15} {'N/A':<10}")
            
            # Genel istatistikler
            if gecerli_hisse > 0:
                ort_basari_orani = toplam_basari / gecerli_hisse
                print("\n" + "=" * 90)
                print("📈 GENEL İSTATİSTİKLER:")
                print(f"  • Ortalama Başarı Oranı: %{ort_basari_orani:.1f}")
                print(f"  • Analiz Edilen Toplam Geçmiş Sinyal: {toplam_sinyal}")
                print(f"  • Geçerli Veri Olan Hisse: {gecerli_hisse}/{len(buy_setup_9_list)}")
                print("=" * 90)
                
                # Yorumlama
                print("\n💡 YORUMLAMA:")
                print(f"  ✅ Başarı Oranı ≥%60: Yüksek olasılıklı hisseler")
                print(f"  ⚠️  Başarı Oranı %40-60: Orta olasılıklı hisseler")
                print(f"  ❌ Başarı Oranı <%40: Düşük olasılıklı hisseler")
                print(f"  📈 Ort Kazanç >%5: Güçlü potansiyel")
                print(f"  📊 Ort Kazanç %2-5: Orta potansiyel")
                print(f"  📉 Ort Kazanç <%2: Zayıf potansiyel")
        else:
            print("  Yeterli geçmiş veri bulunamadı")
        
        print("=" * 90)
    
    # SELL SETUP 9
    print("\n🔴 SELL SETUP 9 (SATIŞ SİNYALİ) - Heiken Ashi Haftalık:")
    print("-" * 90)
    if sell_setup_9_list:
        sell_setup_9_list_sorted = sorted(sell_setup_9_list, 
                                         key=lambda x: (x['ha_renk'] == "🔴 KIRMIZI", 
                                                       "KARARSIZ" in x['trend_gucu'],
                                                       "ORTA" in x['trend_gucu']), 
                                         reverse=True)
        for h in sell_setup_9_list_sorted:
            print(f"  {h['sembol']:10s} | Fiyat: {h['son_fiyat']:8.2f} TL | HA: {h['ha_renk']} | "
                  f"Trend: {h['trend_gucu']:18s} | {h['tarih']}")
    else:
        print("  Sinyal bulunamadı")
    
    # DİĞER SİNYALLER (7-8)
    print("\n⚠️  DİĞER ÖNEMLİ SİNYALLER (7-8):")
    print("-" * 90)
    if diger_sinyaller:
        # İlk 20'yi göster
        for h in diger_sinyaller[:20]:
            if h['buy_setup'] >= 7:
                print(f"  {h['sembol']:10s} | Fiyat: {h['son_fiyat']:8.2f} TL | HA: {h['ha_renk']} | "
                      f"Buy: {h['buy_setup']} | Trend: {h['trend_gucu']:18s} | {h['tarih']}")
            if h['sell_setup'] >= 7:
                print(f"  {h['sembol']:10s} | Fiyat: {h['son_fiyat']:8.2f} TL | HA: {h['ha_renk']} | "
                      f"Sell: {h['sell_setup']} | Trend: {h['trend_gucu']:18s} | {h['tarih']}")
        
        if len(diger_sinyaller) > 20:
            print(f"\n  ... ve {len(diger_sinyaller) - 20} sinyal daha")
    else:
        print("  Sinyal bulunamadı")
    
    # ÖNE ÇIKANLAR - Buy Setup 9
    if buy_setup_9_list:
        print("\n" + "=" * 90)
        print("⭐ ÖNE ÇIKAN BUY SETUP 9 SİNYALLERİ:")
        print("=" * 90)
        
        # Yeşil HA + Kararsız/Orta trend olanları filtrele
        one_cikanlar = [h for h in buy_setup_9_list 
                       if h['ha_renk'] == "🟢 YEŞİL" 
                       and ("KARARSIZ" in h['trend_gucu'] or "ORTA" in h['trend_gucu'])]
        
        if one_cikanlar:
            for h in one_cikanlar[:10]:
                print(f"\n🔹 {h['sembol']} - {h['son_fiyat']} TL")
                print(f"   • HA Kapanış: {h['ha_close']:.2f} TL | HA Açılış: {h['ha_open']:.2f} TL")
                print(f"   • Son Mum: {h['ha_renk']}")
                print(f"   • Trend Durumu: {h['trend_gucu']}")
                print(f"   ✅ POZİTİF: İdeal alış fırsatı - HA yeşil + Trend zayıfladı")
        else:
            print("  İdeal sinyal bulunamadı. Yukarıdaki listeden değerlendirin.")
    
    # ÖNE ÇIKANLAR - Sell Setup 9
    if sell_setup_9_list:
        print("\n" + "=" * 90)
        print("⭐ ÖNE ÇIKAN SELL SETUP 9 SİNYALLERİ:")
        print("=" * 90)
        
        one_cikanlar = [h for h in sell_setup_9_list 
                       if h['ha_renk'] == "🔴 KIRMIZI" 
                       and ("KARARSIZ" in h['trend_gucu'] or "ORTA" in h['trend_gucu'])]
        
        if one_cikanlar:
            for h in one_cikanlar[:10]:
                print(f"\n🔹 {h['sembol']} - {h['son_fiyat']} TL")
                print(f"   • HA Kapanış: {h['ha_close']:.2f} TL | HA Açılış: {h['ha_open']:.2f} TL")
                print(f"   • Son Mum: {h['ha_renk']}")
                print(f"   • Trend Durumu: {h['trend_gucu']}")
                print(f"   ✅ DİKKAT: İdeal satış fırsatı - HA kırmızı + Trend zayıfladı")
        else:
            print("  İdeal sinyal bulunamadı. Yukarıdaki listeden değerlendirin.")
    
    # ÖZET
    print("\n" + "=" * 90)
    print("📊 GENEL ÖZET:")
    print(f"  • Taranan Toplam Hisse: {toplam}")
    print(f"  • Buy Setup 9 Sinyali: {len(buy_setup_9_list)} hisse")
    print(f"  • Sell Setup 9 Sinyali: {len(sell_setup_9_list)} hisse")
    print(f"  • Yaklaşan Sinyaller (7-8): {len(diger_sinyaller)} hisse")
    print("=" * 90)
    
    print("\n💡 KULLANIM NOTLARI:")
    print("  📌 Sinyaller trend gücüne ve HA mum rengine göre sıralanmıştır")
    print("  📌 GEÇMİŞ ANALİZ bölümü her hissenin başarı geçmişini gösterir")
    print("  📌 ÖNE ÇIKANLAR bölümü en güvenilir sinyalleri gösterir")
    print("  📌 Mutlaka diğer teknik göstergelerle (RSI, MACD, hacim) doğrulayın")
    print("  📌 Temel analiz ve risk yönetimi unutmayın!")
    print("=" * 90)
    
    # Sonuçları dosyaya kaydet
    tarih_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    dosya_adi = f"bist_tarama_{tarih_str}.txt"
    
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(f"BIST TÜM HİSSELER TARAMA SONUÇLARI\n")
        f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Taranan Hisse: {toplam}\n\n")
        
        f.write("BUY SETUP 9:\n")
        for h in buy_setup_9_list:
            f.write(f"{h['sembol']},{h['son_fiyat']},{h['ha_renk']},{h['trend_gucu']}\n")
        
        f.write("\nSELL SETUP 9:\n")
        for h in sell_setup_9_list:
            f.write(f"{h['sembol']},{h['son_fiyat']},{h['ha_renk']},{h['trend_gucu']}\n")
        
        # Geçmiş analiz sonuçları
        if gecmis_sonuclar:
            f.write("\n\nGEÇMİŞ BAŞARI ORANI ANALİZİ:\n")
            f.write("Sembol,Fiyat,Başarı Oranı,Ortalama Kazanç,Sinyal Sayısı\n")
            for h in gecmis_sonuclar_sirali:
                if h['basari_orani']:
                    f.write(f"{h['sembol']},{h['son_fiyat']},{h['basari_orani']},{h['ort_kazanc']},{h['sinyal_sayisi']}\n")
    
    print(f"\n✓ Sonuçlar '{dosya_adi}' dosyasına kaydedildi")
    print("=" * 90)

if __name__ == "__main__":
    try:
        import yfinance
        import pandas
    except ImportError:
        print("Gerekli kütüphaneler yükleniyor...")
        print("Lütfen şu komutları çalıştırın:")
        print("  pip install yfinance pandas")
        exit(1)
    
    tum_hisseleri_tara()
