#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIST Tüm Hisse Senetleri TD Sequential + Heiken Ashi Haftalık Tarayıcı - GUI Versiyonu
Görsel arayüz ile kolay kullanım
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
import time
import threading
from collections import defaultdict

warnings.filterwarnings('ignore')

# Matplotlib import (opsiyonel)
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class BISTStockScanner:
    """BIST hisse senedi tarayıcısı ana sınıfı"""
    
    @staticmethod
    def bist_tum_hisseler_cek():
        """BIST'te işlem gören tüm hisse senetlerini çeker"""
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
            
            # BIST 100 ve tüm diğer hisseler
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
        
        return sorted(list(set(hisseler)))
    
    @staticmethod
    def heiken_ashi(df):
        """Heiken Ashi mumlarını hesaplar"""
        df = df.copy()
        
        df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
        df['HA_Open'] = 0.0
        df.loc[df.index[0], 'HA_Open'] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
        
        for i in range(1, len(df)):
            df.loc[df.index[i], 'HA_Open'] = (df['HA_Open'].iloc[i-1] + df['HA_Close'].iloc[i-1]) / 2
        
        df['HA_High'] = df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
        df['HA_Low'] = df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)
        
        return df
    
    @staticmethod
    def td_sequential_heiken_ashi(df):
        """Heiken Ashi mumları üzerinde TD Sequential hesaplama"""
        df = df.copy()
        df = BISTStockScanner.heiken_ashi(df)
        
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
    
    @staticmethod
    def trend_gucu_hesapla(df):
        """Trend gücü hesaplama"""
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
    
    @staticmethod
    def buy_setup_basari_orani_analiz(df):
        """Geçmiş Buy Setup 9 sinyallerinin başarı oranını analiz eder"""
        buy_setup_9_sinyaller = []
        
        for i in range(len(df)):
            if df['buy_setup'].iloc[i] == 9:
                buy_setup_9_sinyaller.append(i)
        
        if len(buy_setup_9_sinyaller) == 0:
            return None, None, 0
        
        basarili_sinyal = 0
        toplam_kazanc = 0
        kazanc_listesi = []
        
        for sinyal_idx in buy_setup_9_sinyaller:
            if sinyal_idx + 20 >= len(df):
                continue
            
            sinyal_fiyat = df['Close'].iloc[sinyal_idx]
            sonraki_max_fiyat = df['Close'].iloc[sinyal_idx+1:sinyal_idx+21].max()
            
            kazanc_yuzde = ((sonraki_max_fiyat - sinyal_fiyat) / sinyal_fiyat) * 100
            kazanc_listesi.append(kazanc_yuzde)
            toplam_kazanc += kazanc_yuzde
            
            if kazanc_yuzde > 2:
                basarili_sinyal += 1
        
        if len(kazanc_listesi) == 0:
            return None, None, 0
        
        basari_orani = (basarili_sinyal / len(kazanc_listesi)) * 100
        ortalama_kazanc = toplam_kazanc / len(kazanc_listesi)
        
        return basari_orani, ortalama_kazanc, len(kazanc_listesi)


class BISTScannerGUI:
    """BIST Tarayıcı GUI Uygulaması"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("BIST Hisse Senedi Tarayıcı - TD Sequential + Heiken Ashi")
        self.root.geometry("1600x900")
        
        # Tema renkleri
        self.colors = {
            'bg_dark': '#0a0e27',
            'bg_medium': '#1a1f3a',
            'bg_light': '#252b48',
            'accent': '#00d9ff',
            'success': '#00ff88',
            'warning': '#ffaa00',
            'danger': '#ff4444',
            'text': '#e8edf4',
            'text_dim': '#8892b0'
        }
        
        # Tarama durumu
        self.is_scanning = False
        self.scan_results = {
            'buy_setup_9': [],
            'sell_setup_9': [],
            'other_signals': []
        }
        
        # Stil yapılandırması
        self.configure_styles()
        
        # UI oluştur
        self.setup_ui()
    
    def configure_styles(self):
        """TTK stillerini yapılandır"""
        style = ttk.Style()
        style.theme_use('clam')
        
        self.root.configure(bg=self.colors['bg_dark'])
        
        # Frame stilleri
        style.configure('Dark.TFrame', background=self.colors['bg_dark'])
        style.configure('Card.TFrame', background=self.colors['bg_medium'],
                       relief='flat', borderwidth=1)
        
        # Label stilleri
        style.configure('Title.TLabel', background=self.colors['bg_dark'],
                       foreground=self.colors['accent'], font=('Segoe UI', 28, 'bold'))
        style.configure('Subtitle.TLabel', background=self.colors['bg_medium'],
                       foreground=self.colors['text_dim'], font=('Segoe UI', 10))
        style.configure('Header.TLabel', background=self.colors['bg_medium'],
                       foreground=self.colors['text'], font=('Segoe UI', 12, 'bold'))
        
        # Button stilleri
        style.configure('Accent.TButton', 
                       background=self.colors['accent'],
                       foreground=self.colors['bg_dark'],
                       font=('Segoe UI', 11, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        # Notebook stilleri
        style.configure('TNotebook', background=self.colors['bg_dark'], borderwidth=0)
        style.configure('TNotebook.Tab', background=self.colors['bg_medium'],
                       foreground=self.colors['text_dim'], padding=[20, 10],
                       font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', self.colors['bg_light'])],
                 foreground=[('selected', self.colors['accent'])])
    
    def setup_ui(self):
        """Ana UI bileşenlerini oluştur"""
        # Ana container
        main_container = ttk.Frame(self.root, style='Dark.TFrame')
        main_container.pack(fill='both', expand=True)
        
        # Başlık
        self.create_header(main_container)
        
        # İçerik alanı
        content_frame = ttk.Frame(main_container, style='Dark.TFrame')
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Sol panel - Kontroller
        left_panel = ttk.Frame(content_frame, style='Card.TFrame', width=350)
        left_panel.pack(side='left', fill='y', padx=(0, 10), pady=5)
        left_panel.pack_propagate(False)
        
        self.create_control_panel(left_panel)
        
        # Sağ panel - Notebook ile sekmeler
        right_panel = ttk.Frame(content_frame, style='Dark.TFrame')
        right_panel.pack(side='right', fill='both', expand=True)
        
        self.create_results_panel(right_panel)
        
        # Durum çubuğu
        self.create_status_bar(main_container)
    
    def create_header(self, parent):
        """Başlık bölümü"""
        header_frame = ttk.Frame(parent, style='Dark.TFrame')
        header_frame.pack(fill='x', padx=20, pady=20)
        
        # Logo ve başlık
        title_frame = ttk.Frame(header_frame, style='Dark.TFrame')
        title_frame.pack(side='left')
        
        title = ttk.Label(title_frame, 
                         text="📊 BIST TARAYICI",
                         style='Title.TLabel')
        title.pack(anchor='w')
        
        subtitle = ttk.Label(title_frame,
                           text="TD Sequential + Heiken Ashi Haftalık Analiz",
                           foreground=self.colors['text_dim'],
                           background=self.colors['bg_dark'],
                           font=('Segoe UI', 11))
        subtitle.pack(anchor='w')
        
        # Saat
        self.time_label = ttk.Label(header_frame,
                                   text=datetime.now().strftime('%H:%M:%S'),
                                   foreground=self.colors['accent'],
                                   background=self.colors['bg_dark'],
                                   font=('Segoe UI', 14, 'bold'))
        self.time_label.pack(side='right')
        self.update_time()
    
    def create_control_panel(self, parent):
        """Sol kontrol paneli"""
        # Başlık
        header = ttk.Label(parent, text="TARAMA AYARLARI",
                         style='Header.TLabel')
        header.pack(pady=20, padx=20)
        
        # Tarama butonu
        self.scan_button = tk.Button(parent,
                                    text="🔍 TARAMAYI BAŞLAT",
                                    command=self.start_scan,
                                    bg=self.colors['accent'],
                                    fg=self.colors['bg_dark'],
                                    font=('Segoe UI', 13, 'bold'),
                                    relief='flat',
                                    padx=20,
                                    pady=15,
                                    cursor='hand2',
                                    activebackground=self.colors['success'])
        self.scan_button.pack(pady=10, padx=20, fill='x')
        
        # Durdur butonu
        self.stop_button = tk.Button(parent,
                                    text="⏸ DURDUR",
                                    command=self.stop_scan,
                                    bg=self.colors['danger'],
                                    fg='white',
                                    font=('Segoe UI', 11, 'bold'),
                                    relief='flat',
                                    padx=20,
                                    pady=10,
                                    cursor='hand2',
                                    state='disabled')
        self.stop_button.pack(pady=5, padx=20, fill='x')
        
        # İlerleme çubuğu
        progress_frame = ttk.Frame(parent, style='Card.TFrame')
        progress_frame.pack(pady=20, padx=20, fill='x')
        
        ttk.Label(progress_frame, text="İlerleme:",
                 style='Subtitle.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.progress = ttk.Progressbar(progress_frame, 
                                       mode='determinate',
                                       length=300)
        self.progress.pack(fill='x', pady=5)
        
        self.progress_label = ttk.Label(progress_frame,
                                       text="0 / 0 (%0)",
                                       style='Subtitle.TLabel')
        self.progress_label.pack(anchor='w')
        
        # İstatistikler
        stats_frame = ttk.LabelFrame(parent, text="İSTATİSTİKLER",
                                    style='Card.TFrame')
        stats_frame.pack(pady=20, padx=20, fill='x')
        
        self.stats_labels = {}
        stats = [
            ('total', 'Taranan Hisse:', '0'),
            ('buy9', 'Buy Setup 9:', '0'),
            ('sell9', 'Sell Setup 9:', '0'),
            ('other', 'Diğer Sinyaller:', '0')
        ]
        
        for key, label, value in stats:
            frame = ttk.Frame(stats_frame, style='Card.TFrame')
            frame.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(frame, text=label, style='Subtitle.TLabel').pack(side='left')
            self.stats_labels[key] = ttk.Label(frame, text=value,
                                              foreground=self.colors['accent'],
                                              background=self.colors['bg_medium'],
                                              font=('Segoe UI', 10, 'bold'))
            self.stats_labels[key].pack(side='right')
        
        # Ayarlar
        settings_frame = ttk.LabelFrame(parent, text="AYARLAR",
                                       style='Card.TFrame')
        settings_frame.pack(pady=20, padx=20, fill='both', expand=True)
        
        # Zaman aralığı seçimi
        ttk.Label(settings_frame, text="Zaman Aralığı:",
                 style='Subtitle.TLabel',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(15, 5))
        
        self.interval_var = tk.StringVar(value="1wk")
        intervals = [("📅 Haftalık", "1wk"), ("📆 Günlük", "1d")]
        
        interval_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        interval_frame.pack(anchor='w', padx=20, pady=5)
        
        for text, value in intervals:
            ttk.Radiobutton(interval_frame, text=text, value=value,
                          variable=self.interval_var).pack(anchor='w', pady=2)
        
        # Periyot seçimi
        ttk.Label(settings_frame, text="Geçmiş Veri Periyodu:",
                 style='Subtitle.TLabel',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(15, 5))
        
        self.period_var = tk.StringVar(value="3mo")
        periods = [("3 Ay", "3mo"), ("6 Ay", "6mo"), ("1 Yıl", "1y"), ("2 Yıl", "2y")]
        
        period_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        period_frame.pack(anchor='w', padx=20, pady=5)
        
        for text, value in periods:
            ttk.Radiobutton(period_frame, text=text, value=value,
                          variable=self.period_var).pack(anchor='w', pady=2)
        
        # Detaylı analiz
        ttk.Label(settings_frame, text="Ek Özellikler:",
                 style='Subtitle.TLabel',
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(15, 5))
        
        self.detailed_analysis_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame,
                       text="Detaylı Başarı Analizi (2 yıllık)",
                       variable=self.detailed_analysis_var).pack(anchor='w', padx=20, pady=5)
        
        # Bilgi notu
        info_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        info_frame.pack(fill='x', padx=10, pady=(20, 10))
        
        info_text = (
            "💡 Haftalık: Swing trade için\n"
            "💡 Günlük: Kısa vadeli işlemler için\n"
            "💡 Detaylı analiz tarama süresini uzatır"
        )
        
        info_label = ttk.Label(info_frame, text=info_text,
                              style='Subtitle.TLabel',
                              foreground=self.colors['text_dim'],
                              justify='left')
        info_label.pack(padx=10, pady=5)
    
    def create_results_panel(self, parent):
        """Sonuç paneli (Notebook)"""
        # Notebook oluştur
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True)
        
        # Sekme 1: Buy Setup 9
        self.buy_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(self.buy_frame, text='  🟢 BUY SETUP 9  ')
        self.create_buy_setup_tab()
        
        # Sekme 2: Sell Setup 9
        self.sell_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(self.sell_frame, text='  🔴 SELL SETUP 9  ')
        self.create_sell_setup_tab()
        
        # Sekme 3: Diğer Sinyaller
        self.other_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(self.other_frame, text='  ⚠️ DİĞER SİNYALLER  ')
        self.create_other_signals_tab()
        
        # Sekme 4: Geçmiş Analiz
        self.analysis_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(self.analysis_frame, text='  📊 BAŞARI ANALİZİ  ')
        self.create_analysis_tab()
        
        # Sekme 5: Log
        self.log_frame = ttk.Frame(self.notebook, style='Dark.TFrame')
        self.notebook.add(self.log_frame, text='  📝 LOG  ')
        self.create_log_tab()
    
    def create_buy_setup_tab(self):
        """Buy Setup 9 sekmesi"""
        # Treeview
        columns = ('Sembol', 'Fiyat', 'HA Renk', 'Trend Gücü', 'Tarih')
        
        self.buy_tree = ttk.Treeview(self.buy_frame, columns=columns,
                                    show='headings', height=20)
        
        # Sütun başlıkları
        for col in columns:
            self.buy_tree.heading(col, text=col)
            self.buy_tree.column(col, width=150, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.buy_frame, orient='vertical',
                                 command=self.buy_tree.yview)
        self.buy_tree.configure(yscrollcommand=scrollbar.set)
        
        self.buy_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        # Çift tıklama ile detay göster
        self.buy_tree.bind('<Double-1>', lambda e: self.show_stock_detail('buy'))
    
    def create_sell_setup_tab(self):
        """Sell Setup 9 sekmesi"""
        columns = ('Sembol', 'Fiyat', 'HA Renk', 'Trend Gücü', 'Tarih')
        
        self.sell_tree = ttk.Treeview(self.sell_frame, columns=columns,
                                     show='headings', height=20)
        
        for col in columns:
            self.sell_tree.heading(col, text=col)
            self.sell_tree.column(col, width=150, anchor='center')
        
        scrollbar = ttk.Scrollbar(self.sell_frame, orient='vertical',
                                 command=self.sell_tree.yview)
        self.sell_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sell_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
        
        self.sell_tree.bind('<Double-1>', lambda e: self.show_stock_detail('sell'))
    
    def create_other_signals_tab(self):
        """Diğer sinyaller sekmesi"""
        columns = ('Sembol', 'Fiyat', 'HA Renk', 'Buy', 'Sell', 'Trend', 'Tarih')
        
        self.other_tree = ttk.Treeview(self.other_frame, columns=columns,
                                      show='headings', height=20)
        
        for col in columns:
            self.other_tree.heading(col, text=col)
            self.other_tree.column(col, width=120, anchor='center')
        
        scrollbar = ttk.Scrollbar(self.other_frame, orient='vertical',
                                 command=self.other_tree.yview)
        self.other_tree.configure(yscrollcommand=scrollbar.set)
        
        self.other_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
    
    def create_analysis_tab(self):
        """Başarı analizi sekmesi"""
        columns = ('Sembol', 'Fiyat', 'Başarı %', 'Ort. Kazanç %', 'Sinyal Sayısı', 'Değerlendirme')
        
        self.analysis_tree = ttk.Treeview(self.analysis_frame, columns=columns,
                                         show='headings', height=20)
        
        widths = [100, 100, 120, 120, 120, 200]
        for i, col in enumerate(columns):
            self.analysis_tree.heading(col, text=col)
            self.analysis_tree.column(col, width=widths[i], anchor='center')
        
        scrollbar = ttk.Scrollbar(self.analysis_frame, orient='vertical',
                                 command=self.analysis_tree.yview)
        self.analysis_tree.configure(yscrollcommand=scrollbar.set)
        
        self.analysis_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
    
    def create_log_tab(self):
        """Log sekmesi"""
        self.log_text = scrolledtext.ScrolledText(self.log_frame,
                                                  bg=self.colors['bg_light'],
                                                  fg=self.colors['text'],
                                                  font=('Consolas', 10),
                                                  wrap='word')
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_status_bar(self, parent):
        """Durum çubuğu"""
        self.status_bar = ttk.Label(parent,
                                   text="Hazır",
                                   relief='flat',
                                   background=self.colors['bg_medium'],
                                   foreground=self.colors['text_dim'],
                                   font=('Segoe UI', 9))
        self.status_bar.pack(side='bottom', fill='x', padx=10, pady=5)
    
    def update_time(self):
        """Saati güncelle"""
        current_time = datetime.now().strftime('%H:%M:%S')
        self.time_label.configure(text=current_time)
        self.root.after(1000, self.update_time)
    
    def log(self, message, level='INFO'):
        """Log mesajı ekle"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        colors = {
            'INFO': self.colors['text'],
            'SUCCESS': self.colors['success'],
            'WARNING': self.colors['warning'],
            'ERROR': self.colors['danger']
        }
        
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.log_text.insert('end', log_entry)
        self.log_text.see('end')
        
        # Durum çubuğunu güncelle
        self.status_bar.configure(text=message)
    
    def start_scan(self):
        """Taramayı başlat"""
        if self.is_scanning:
            return
        
        self.is_scanning = True
        self.scan_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        
        # Sonuçları temizle
        self.clear_results()
        
        # Thread'de taramayı başlat
        scan_thread = threading.Thread(target=self.perform_scan, daemon=True)
        scan_thread.start()
    
    def stop_scan(self):
        """Taramayı durdur"""
        self.is_scanning = False
        self.scan_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.log("Tarama durduruldu", "WARNING")
    
    def clear_results(self):
        """Tüm sonuçları temizle"""
        for tree in [self.buy_tree, self.sell_tree, self.other_tree, self.analysis_tree]:
            for item in tree.get_children():
                tree.delete(item)
        
        self.scan_results = {
            'buy_setup_9': [],
            'sell_setup_9': [],
            'other_signals': []
        }
        
        self.log_text.delete(1.0, 'end')
        
        for key in self.stats_labels:
            self.stats_labels[key].configure(text='0')
    
    def perform_scan(self):
        """Ana tarama fonksiyonu"""
        interval_text = "Haftalık" if self.interval_var.get() == "1wk" else "Günlük"
        self.log(f"Tarama başlatıldı... ({interval_text} veriler)", "INFO")
        
        # Hisse listesini al
        hisseler = BISTStockScanner.bist_tum_hisseler_cek()
        total = len(hisseler)
        
        self.log(f"{total} hisse taranacak", "INFO")
        
        buy_setup_9_list = []
        sell_setup_9_list = []
        other_signals_list = []
        failed = 0
        
        for i, sembol in enumerate(hisseler, 1):
            if not self.is_scanning:
                break
            
            # İlerleme güncelle
            progress = (i / total) * 100
            self.root.after(0, self.update_progress, i, total, progress)
            
            try:
                result = self.scan_single_stock(sembol, self.period_var.get(), self.interval_var.get())
                
                if result:
                    if result['buy_setup_9']:
                        buy_setup_9_list.append(result)
                        self.root.after(0, self.add_to_tree, self.buy_tree, result, 'buy')
                    elif result['sell_setup_9']:
                        sell_setup_9_list.append(result)
                        self.root.after(0, self.add_to_tree, self.sell_tree, result, 'sell')
                    elif result['buy_setup'] >= 7 or result['sell_setup'] >= 7:
                        other_signals_list.append(result)
                        self.root.after(0, self.add_to_tree, self.other_tree, result, 'other')
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                self.log(f"{sembol} hatası: {str(e)}", "ERROR")
            
            # Rate limit
            if i % 10 == 0:
                time.sleep(0.5)
        
        # Tarama tamamlandı
        self.scan_results = {
            'buy_setup_9': buy_setup_9_list,
            'sell_setup_9': sell_setup_9_list,
            'other_signals': other_signals_list
        }
        
        self.root.after(0, self.scan_completed, total, failed)
        
        # Detaylı analiz yapılsın mı?
        if self.detailed_analysis_var.get() and buy_setup_9_list:
            self.root.after(0, self.perform_detailed_analysis, buy_setup_9_list)
    
    def scan_single_stock(self, sembol, period, interval):
        """Tek bir hisseyi tara"""
        try:
            hisse = yf.Ticker(sembol)
            df = hisse.history(period=period, interval=interval)
            
            if df.empty or len(df) < 10:
                return None
            
            df = BISTStockScanner.td_sequential_heiken_ashi(df)
            trend_gucu = BISTStockScanner.trend_gucu_hesapla(df)
            
            son_buy_setup = df['buy_setup'].iloc[-1]
            son_sell_setup = df['sell_setup'].iloc[-1]
            son_fiyat = df['Close'].iloc[-1]
            son_ha_close = df['HA_Close'].iloc[-1]
            son_ha_open = df['HA_Open'].iloc[-1]
            son_trend = df['ha_trend'].iloc[-1]
            
            ha_renk = "🟢 YEŞİL" if son_ha_close > son_ha_open else "🔴 KIRMIZI"
            
            return {
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
                'tarih': df.index[-1].strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            return None
    
    def perform_detailed_analysis(self, buy_list):
        """Detaylı başarı analizi yap"""
        self.log("Detaylı başarı analizi başlatıldı...", "INFO")
        
        for i, stock in enumerate(buy_list, 1):
            if not self.is_scanning:
                break
            
            self.log(f"Analiz: {stock['sembol']} [{i}/{len(buy_list)}]", "INFO")
            
            try:
                hisse = yf.Ticker(stock['sembol'] + '.IS')
                df = hisse.history(period="2y", interval="1wk")
                
                if df.empty or len(df) < 50:
                    continue
                
                df = BISTStockScanner.td_sequential_heiken_ashi(df)
                basari_orani, ort_kazanc, sinyal_sayisi = BISTStockScanner.buy_setup_basari_orani_analiz(df)
                
                if basari_orani is not None:
                    # Değerlendirme
                    if basari_orani >= 60:
                        degerlendirme = "✅ Yüksek Başarı"
                    elif basari_orani >= 40:
                        degerlendirme = "⚠️ Orta Başarı"
                    else:
                        degerlendirme = "❌ Düşük Başarı"
                    
                    self.root.after(0, self.add_to_analysis_tree, {
                        'sembol': stock['sembol'],
                        'fiyat': stock['son_fiyat'],
                        'basari_orani': basari_orani,
                        'ort_kazanc': ort_kazanc,
                        'sinyal_sayisi': sinyal_sayisi,
                        'degerlendirme': degerlendirme
                    })
                
            except Exception as e:
                self.log(f"Analiz hatası {stock['sembol']}: {str(e)}", "ERROR")
            
            if i % 5 == 0:
                time.sleep(0.3)
        
        self.log("Detaylı analiz tamamlandı", "SUCCESS")
    
    def update_progress(self, current, total, percent):
        """İlerleme çubuğunu güncelle"""
        self.progress['value'] = percent
        self.progress_label.configure(text=f"{current} / {total} (%{percent:.1f})")
        
        # İstatistikleri güncelle
        self.stats_labels['total'].configure(text=str(current))
        self.stats_labels['buy9'].configure(text=str(len(self.scan_results['buy_setup_9'])))
        self.stats_labels['sell9'].configure(text=str(len(self.scan_results['sell_setup_9'])))
        self.stats_labels['other'].configure(text=str(len(self.scan_results['other_signals'])))
    
    def add_to_tree(self, tree, result, signal_type):
        """Treeview'e sonuç ekle"""
        if signal_type == 'buy' or signal_type == 'sell':
            tree.insert('', 'end', values=(
                result['sembol'],
                f"{result['son_fiyat']:.2f} TL",
                result['ha_renk'],
                result['trend_gucu'],
                result['tarih']
            ))
        else:  # other
            tree.insert('', 'end', values=(
                result['sembol'],
                f"{result['son_fiyat']:.2f} TL",
                result['ha_renk'],
                result['buy_setup'],
                result['sell_setup'],
                result['trend_gucu'],
                result['tarih']
            ))
    
    def add_to_analysis_tree(self, data):
        """Analiz ağacına veri ekle"""
        self.analysis_tree.insert('', 'end', values=(
            data['sembol'],
            f"{data['fiyat']:.2f} TL",
            f"{data['basari_orani']:.1f}%",
            f"{data['ort_kazanc']:.2f}%",
            data['sinyal_sayisi'],
            data['degerlendirme']
        ))
    
    def scan_completed(self, total, failed):
        """Tarama tamamlandığında"""
        self.is_scanning = False
        self.scan_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        
        success = total - failed
        
        self.log(f"Tarama tamamlandı! Başarılı: {success}, Başarısız: {failed}", "SUCCESS")
        
        messagebox.showinfo("Tarama Tamamlandı",
                          f"Toplam {total} hisse tarandı\n"
                          f"Başarılı: {success}\n"
                          f"Buy Setup 9: {len(self.scan_results['buy_setup_9'])}\n"
                          f"Sell Setup 9: {len(self.scan_results['sell_setup_9'])}\n"
                          f"Diğer: {len(self.scan_results['other_signals'])}")
    
    def show_stock_detail(self, signal_type):
        """Hisse detayını göster (çift tıklama)"""
        tree = self.buy_tree if signal_type == 'buy' else self.sell_tree
        selection = tree.selection()
        
        if not selection:
            return
        
        item = tree.item(selection[0])
        sembol = item['values'][0]
        
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"{sembol} - Detaylı Bilgi")
        detail_window.geometry("600x400")
        detail_window.configure(bg=self.colors['bg_dark'])
        
        text = scrolledtext.ScrolledText(detail_window,
                                        bg=self.colors['bg_light'],
                                        fg=self.colors['text'],
                                        font=('Consolas', 10))
        text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Detaylı bilgileri göster
        text.insert('end', f"{'='*50}\n")
        text.insert('end', f"{sembol} - DETAYLI ANALİZ\n")
        text.insert('end', f"{'='*50}\n\n")
        
        for data in self.scan_results['buy_setup_9'] + self.scan_results['sell_setup_9']:
            if data['sembol'] == sembol:
                text.insert('end', f"Fiyat: {data['son_fiyat']} TL\n")
                text.insert('end', f"HA Kapanış: {data['ha_close']:.2f} TL\n")
                text.insert('end', f"HA Açılış: {data['ha_open']:.2f} TL\n")
                text.insert('end', f"HA Renk: {data['ha_renk']}\n")
                text.insert('end', f"Trend: {data['trend_gucu']}\n")
                text.insert('end', f"Buy Setup: {data['buy_setup']}\n")
                text.insert('end', f"Sell Setup: {data['sell_setup']}\n")
                text.insert('end', f"Tarih: {data['tarih']}\n")
                break


def main():
    """Ana program"""
    try:
        import yfinance
        import pandas
    except ImportError:
        messagebox.showerror("Hata",
                           "Gerekli kütüphaneler bulunamadı!\n\n"
                           "Lütfen şu komutu çalıştırın:\n"
                           "pip install yfinance pandas")
        return
    
    root = tk.Tk()
    app = BISTScannerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()