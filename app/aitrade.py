import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ccxt
import warnings
warnings.filterwarnings('ignore')

class HeikinAshiTrader:
    """
    Heikin-Ashi mum formasyonları ile trading botu - 3 Yıllık Backtest
    """
    
    def __init__(self, symbol='BTC/USDT', risk_percent=2.0, timeframe='D'):
        self.symbol = symbol
        self.risk_percent = risk_percent
        self.timeframe = timeframe
        self.position = None
        self.trades = []
        
    def fetch_historical_data(self, years=3):
        """3 yıllık gerçek veriyi Binance'den çek"""
        print(f"\n📊 {self.symbol} için {years} yıllık veri çekiliyor...")
        
        try:
            exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
            
            # Zaman aralığını hesapla
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years*365)
            
            # Timeframe'e göre kaç bar gerekli
            timeframe_minutes = {
                '1h': 60, '4h': 240, '1d': 1440
            }
            minutes = timeframe_minutes.get(self.timeframe, 240)
            total_bars = (years * 365 * 24 * 60) // minutes
            
            all_data = []
            since = int(start_date.timestamp() * 1000)
            
            # Veriyi parça parça çek
            while len(all_data) < total_bars:
                try:
                    ohlcv = exchange.fetch_ohlcv(
                        self.symbol, 
                        self.timeframe, 
                        since=since, 
                        limit=1000
                    )
                    
                    if not ohlcv:
                        break
                        
                    all_data.extend(ohlcv)
                    since = ohlcv[-1][0] + 1
                    
                    print(f"✓ {len(all_data)} bar çekildi...", end='\r')
                    
                    if len(ohlcv) < 1000:
                        break
                        
                except Exception as e:
                    print(f"\n⚠️ Veri çekme hatası: {e}")
                    break
            
            # DataFrame oluştur
            df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            print(f"\n✅ {len(df)} bar başarıyla çekildi!")
            print(f"📅 Tarih aralığı: {df.index[0]} - {df.index[-1]}")
            
            return df
            
        except Exception as e:
            print(f"\n❌ Hata: {e}")
            print("⚠️ Demo veri kullanılacak...")
            return self.create_demo_data(years)
    
    def create_demo_data(self, years=3):
        """API çalışmazsa demo veri oluştur"""
        print(f"\n🔧 {years} yıllık demo veri oluşturuluyor...")
        
        # Timeframe'e göre bar sayısı
        bars_per_day = {'1h': 24, '4h': 6, '1d': 1}
        total_bars = years * 365 * bars_per_day.get(self.timeframe, 6)
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=years*365), 
            periods=total_bars, 
            freq=self.timeframe
        )
        
        # Gerçekçi fiyat hareketi
        np.random.seed(42)
        base_price = 30000
        trend = np.cumsum(np.random.randn(total_bars) * 200)
        seasonal = 5000 * np.sin(np.arange(total_bars) * 2 * np.pi / (365 * bars_per_day.get(self.timeframe, 6)))
        noise = np.random.randn(total_bars) * 500
        
        prices = base_price + trend + seasonal + noise
        prices = np.maximum(prices, 10000)  # Minimum fiyat
        
        df = pd.DataFrame({
            'open': prices + np.random.randn(total_bars) * 100,
            'high': prices + abs(np.random.randn(total_bars)) * 300,
            'low': prices - abs(np.random.randn(total_bars)) * 300,
            'close': prices,
            'volume': np.random.randint(1000, 10000, total_bars)
        }, index=dates)
        
        # High/Low düzelt
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)
        
        print(f"✅ {len(df)} bar demo veri oluşturuldu!")
        return df
    
    def calculate_heikin_ashi(self, df):
        """Heikin-Ashi mumlarını hesapla"""
        ha_df = df.copy()
        
        # Heikin-Ashi formülleri
        ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        ha_df['ha_open'] = 0.0
        ha_df.iloc[0, ha_df.columns.get_loc('ha_open')] = (df['open'].iloc[0] + df['close'].iloc[0]) / 2
        
        for i in range(1, len(ha_df)):
            ha_df.iloc[i, ha_df.columns.get_loc('ha_open')] = (
                ha_df['ha_open'].iloc[i-1] + ha_df['ha_close'].iloc[i-1]
            ) / 2
        
        ha_df['ha_high'] = ha_df[['high', 'ha_open', 'ha_close']].max(axis=1)
        ha_df['ha_low'] = ha_df[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        # Mum rengi
        ha_df['ha_color'] = np.where(ha_df['ha_close'] > ha_df['ha_open'], 'green', 'red')
        
        # Mum gövde büyüklüğü
        ha_df['ha_body'] = abs(ha_df['ha_close'] - ha_df['ha_open'])
        
        # Üst ve alt fitil
        ha_df['ha_upper_shadow'] = ha_df['ha_high'] - ha_df[['ha_open', 'ha_close']].max(axis=1)
        ha_df['ha_lower_shadow'] = ha_df[['ha_open', 'ha_close']].min(axis=1) - ha_df['ha_low']
        
        return ha_df
    
    def calculate_trend_strength(self, df, period=10):
        """Trend gücünü hesapla"""
        df = df.copy()
        
        # Ardışık yeşil/kırmızı mumları say
        df['consecutive_green'] = 0
        df['consecutive_red'] = 0
        
        green_count = 0
        red_count = 0
        
        for i in range(len(df)):
            if df['ha_color'].iloc[i] == 'green':
                green_count += 1
                red_count = 0
            else:
                red_count += 1
                green_count = 0
            
            df.iloc[i, df.columns.get_loc('consecutive_green')] = green_count
            df.iloc[i, df.columns.get_loc('consecutive_red')] = red_count
        
        # Hareketli ortalama ile trend
        df['ha_ema_20'] = df['ha_close'].ewm(span=20, adjust=False).mean()
        df['ha_ema_50'] = df['ha_close'].ewm(span=50, adjust=False).mean()
        
        # Trend yönü
        df['trend'] = np.where(df['ha_ema_20'] > df['ha_ema_50'], 'up', 'down')
        
        return df
    
    def detect_patterns(self, df):
        """Heikin-Ashi formasyonlarını tespit et"""
        df = df.copy()
        df['pattern'] = ''
        
        for i in range(5, len(df)):
            # Güçlü yükseliş trendi (3+ ardışık yeşil mum)
            if df['consecutive_green'].iloc[i] >= 3 and df['trend'].iloc[i] == 'up':
                # Düşük alt fitil = güçlü alıcı baskısı
                avg_body = df['ha_body'].iloc[i-3:i+1].mean()
                if df['ha_lower_shadow'].iloc[i] < avg_body * 0.3:
                    df.iloc[i, df.columns.get_loc('pattern')] = 'Strong Uptrend'
            
            # Güçlü düşüş trendi (3+ ardışık kırmızı mum)
            elif df['consecutive_red'].iloc[i] >= 3 and df['trend'].iloc[i] == 'down':
                # Düşük üst fitil = güçlü satıcı baskısı
                avg_body = df['ha_body'].iloc[i-3:i+1].mean()
                if df['ha_upper_shadow'].iloc[i] < avg_body * 0.3:
                    df.iloc[i, df.columns.get_loc('pattern')] = 'Strong Downtrend'
            
            # Dönüş sinyali: Kırmızıdan yeşile
            elif (df['ha_color'].iloc[i] == 'green' and 
                  df['consecutive_red'].iloc[i-1] >= 3):
                # Büyük gövdeli yeşil mum
                if df['ha_body'].iloc[i] > df['ha_body'].iloc[i-3:i].mean() * 1.5:
                    df.iloc[i, df.columns.get_loc('pattern')] = 'Bullish Reversal'
            
            # Dönüş sinyali: Yeşilden kırmızıya
            elif (df['ha_color'].iloc[i] == 'red' and 
                  df['consecutive_green'].iloc[i-1] >= 3):
                # Büyük gövdeli kırmızı mum
                if df['ha_body'].iloc[i] > df['ha_body'].iloc[i-3:i].mean() * 1.5:
                    df.iloc[i, df.columns.get_loc('pattern')] = 'Bearish Reversal'
            
            # Doji benzeri (kararsızlık)
            elif df['ha_body'].iloc[i] < df['ha_body'].iloc[i-10:i].mean() * 0.3:
                df.iloc[i, df.columns.get_loc('pattern')] = 'Indecision'
        
        return df
    
    def generate_signals(self, df):
        """Alım satım sinyali üret"""
        df = df.copy()
        df['signal'] = 0
        df['signal_type'] = ''
        
        for i in range(50, len(df)):
            # ALIŞ SİNYALLERİ
            
            # 1. Güçlü yükseliş reversal
            if df['pattern'].iloc[i] == 'Bullish Reversal':
                if df['ha_close'].iloc[i] > df['ha_ema_20'].iloc[i]:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    df.iloc[i, df.columns.get_loc('signal_type')] = 'Bullish Reversal + EMA'
            
            # 2. Güçlü yükseliş trendi devam
            elif df['pattern'].iloc[i] == 'Strong Uptrend':
                # Düzeltme sonrası devam
                if (df['consecutive_green'].iloc[i] == 3 and 
                    df['consecutive_red'].iloc[i-1] <= 2 and
                    df['ha_close'].iloc[i] > df['ha_ema_50'].iloc[i]):
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    df.iloc[i, df.columns.get_loc('signal_type')] = 'Uptrend Continuation'
            
            # 3. Trend ve momentum birleşimi
            elif (df['consecutive_green'].iloc[i] >= 2 and
                  df['ha_close'].iloc[i] > df['ha_ema_20'].iloc[i] and
                  df['ha_ema_20'].iloc[i] > df['ha_ema_50'].iloc[i] and
                  df['ha_body'].iloc[i] > df['ha_body'].iloc[i-10:i].mean()):
                df.iloc[i, df.columns.get_loc('signal')] = 1
                df.iloc[i, df.columns.get_loc('signal_type')] = 'Strong Momentum'
            
            # SATIŞ SİNYALLERİ
            
            # 1. Düşüş reversal
            if df['pattern'].iloc[i] == 'Bearish Reversal':
                if df['ha_close'].iloc[i] < df['ha_ema_20'].iloc[i]:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    df.iloc[i, df.columns.get_loc('signal_type')] = 'Bearish Reversal'
            
            # 2. Güçlü düşüş trendi
            elif df['pattern'].iloc[i] == 'Strong Downtrend':
                df.iloc[i, df.columns.get_loc('signal')] = -1
                df.iloc[i, df.columns.get_loc('signal_type')] = 'Strong Downtrend'
            
            # 3. Trend kırılması
            elif (df['consecutive_red'].iloc[i] >= 2 and
                  df['ha_close'].iloc[i] < df['ha_ema_20'].iloc[i] and
                  df['ha_ema_20'].iloc[i] < df['ha_ema_50'].iloc[i]):
                df.iloc[i, df.columns.get_loc('signal')] = -1
                df.iloc[i, df.columns.get_loc('signal_type')] = 'Trend Break'
        
        return df
    
    def calculate_position_size(self, price, stop_loss_price, account_balance):
        """Pozisyon büyüklüğünü hesapla"""
        risk_amount = account_balance * (self.risk_percent / 100)
        price_diff = abs(price - stop_loss_price)
        
        if price_diff == 0:
            return 0
            
        position_size = risk_amount / price_diff
        
        # Maksimum pozisyon kontrolü (%50 sermaye)
        max_position = (account_balance * 0.5) / price
        position_size = min(position_size, max_position)
        
        return position_size
    
    def backtest(self, df, initial_balance=10000):
        """Stratejiyi backtest et"""
        print("\n🔄 Heikin-Ashi hesaplamaları yapılıyor...")
        df = self.calculate_heikin_ashi(df)
        df = self.calculate_trend_strength(df)
        df = self.detect_patterns(df)
        df = self.generate_signals(df)
        
        print("📈 Backtest başlatılıyor...")
        
        balance = initial_balance
        position = None
        trades = []
        equity_curve = []
        
        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            ha_close = df['ha_close'].iloc[i]
            signal = df['signal'].iloc[i]
            current_equity = balance
            
            # Açık pozisyon varsa equity güncelle
            if position:
                unrealized_pnl = (current_price - position['entry_price']) * position['position_size']
                current_equity = balance + unrealized_pnl
            
            equity_curve.append({
                'date': df.index[i],
                'equity': current_equity
            })
            
            # ALIŞ sinyali
            if signal == 1 and position is None:
                # Stop loss: Son 20 barın HA en düşüğü
                stop_loss = df['ha_low'].iloc[max(0, i-20):i+1].min() * 0.98
                
                position_size = self.calculate_position_size(
                    current_price, stop_loss, balance
                )
                
                if position_size > 0:
                    # Take profit: ATR bazlı dinamik hedef
                    atr = df['ha_body'].iloc[i-14:i+1].mean()
                    take_profit = current_price + (atr * 2.5)
                    
                    position = {
                        'entry_price': current_price,
                        'entry_date': df.index[i],
                        'position_size': position_size,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'signal_type': df['signal_type'].iloc[i],
                        'entry_ha_color': df['ha_color'].iloc[i]
                    }
                
            # Pozisyon çıkış kontrolü
            elif position is not None:
                # Stop loss
                if df['low'].iloc[i] <= position['stop_loss']:
                    exit_price = position['stop_loss']
                    pnl = (exit_price - position['entry_price']) * position['position_size']
                    balance += pnl
                    
                    trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': df.index[i],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_percent': (pnl / (position['entry_price'] * position['position_size'])) * 100,
                        'exit_reason': 'Stop Loss',
                        'signal_type': position['signal_type'],
                        'hold_days': (df.index[i] - position['entry_date']).days
                    })
                    position = None
                    
                # Take profit
                elif df['high'].iloc[i] >= position['take_profit']:
                    exit_price = position['take_profit']
                    pnl = (exit_price - position['entry_price']) * position['position_size']
                    balance += pnl
                    
                    trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': df.index[i],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_percent': (pnl / (position['entry_price'] * position['position_size'])) * 100,
                        'exit_reason': 'Take Profit',
                        'signal_type': position['signal_type'],
                        'hold_days': (df.index[i] - position['entry_date']).days
                    })
                    position = None
                    
                # Satış sinyali
                elif signal == -1:
                    exit_price = current_price
                    pnl = (exit_price - position['entry_price']) * position['position_size']
                    balance += pnl
                    
                    trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': df.index[i],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_percent': (pnl / (position['entry_price'] * position['position_size'])) * 100,
                        'exit_reason': 'Sell Signal',
                        'signal_type': position['signal_type'],
                        'hold_days': (df.index[i] - position['entry_date']).days
                    })
                    position = None
                
                # Trailing stop (3+ kırmızı mum)
                elif (df['consecutive_red'].iloc[i] >= 3 and 
                      position['entry_ha_color'] == 'green'):
                    exit_price = current_price
                    pnl = (exit_price - position['entry_price']) * position['position_size']
                    balance += pnl
                    
                    trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': df.index[i],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_percent': (pnl / (position['entry_price'] * position['position_size'])) * 100,
                        'exit_reason': 'Trailing Stop',
                        'signal_type': position['signal_type'],
                        'hold_days': (df.index[i] - position['entry_date']).days
                    })
                    position = None
            
            # İlerleme göster
            if i % 100 == 0:
                progress = (i / len(df)) * 100
                print(f"⏳ İlerleme: %{progress:.1f} - Bakiye: ${balance:,.2f}", end='\r')
        
        self.trades = trades
        self.equity_curve = pd.DataFrame(equity_curve)
        
        print(f"\n✅ Backtest tamamlandı! Toplam {len(trades)} işlem yapıldı.")
        
        return df, trades, balance
    
    def calculate_metrics(self, initial_balance, final_balance, trades):
        """Detaylı performans metrikleri"""
        metrics = {}
        
        metrics['initial_balance'] = initial_balance
        metrics['final_balance'] = final_balance
        metrics['total_pnl'] = final_balance - initial_balance
        metrics['total_return'] = ((final_balance - initial_balance) / initial_balance) * 100
        metrics['total_trades'] = len(trades)
        
        if not trades:
            return metrics
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        metrics['winning_trades'] = len(winning_trades)
        metrics['losing_trades'] = len(losing_trades)
        metrics['win_rate'] = (len(winning_trades) / len(trades)) * 100 if trades else 0
        
        metrics['avg_win'] = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        metrics['avg_loss'] = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        metrics['avg_hold_days'] = np.mean([t['hold_days'] for t in trades])
        
        if losing_trades and winning_trades:
            metrics['profit_factor'] = abs(sum([t['pnl'] for t in winning_trades]) / sum([t['pnl'] for t in losing_trades]))
        else:
            metrics['profit_factor'] = 0
        
        if hasattr(self, 'equity_curve'):
            equity = self.equity_curve['equity'].values
            cummax = np.maximum.accumulate(equity)
            drawdown = (equity - cummax) / cummax * 100
            metrics['max_drawdown'] = abs(drawdown.min())
        else:
            metrics['max_drawdown'] = 0
        
        returns = [t['pnl_percent'] for t in trades]
        if returns:
            metrics['sharpe_ratio'] = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            metrics['sharpe_ratio'] = 0
        
        return metrics
    
    def print_results(self, initial_balance, final_balance, trades):
        """Detaylı sonuçları yazdır"""
        metrics = self.calculate_metrics(initial_balance, final_balance, trades)
        
        print("\n" + "="*80)
        print(f"HEİKİN-ASHİ STRATEGY - 3 YILLIK BACKTEST SONUÇLARI")
        print(f"Sembol: {self.symbol} | Timeframe: {self.timeframe} | Risk: %{self.risk_percent}")
        print("="*80)
        
        print(f"\n💰 SERMAYE ANALİZİ:")
        print(f"   Başlangıç: ${metrics['initial_balance']:,.2f}")
        print(f"   Final:      ${metrics['final_balance']:,.2f}")
        print(f"   Kar/Zarar:  ${metrics['total_pnl']:,.2f}")
        print(f"   Getiri:     %{metrics['total_return']:.2f}")
        
        print(f"\n📊 İŞLEM İSTATİSTİKLERİ:")
        print(f"   Toplam İşlem:    {metrics['total_trades']}")
        print(f"   Kazanan:         {metrics['winning_trades']} (%{metrics['win_rate']:.1f})")
        print(f"   Kaybeden:        {metrics['losing_trades']}")
        print(f"   Ort. Kazanç:     ${metrics['avg_win']:,.2f}")
        print(f"   Ort. Kayıp:      ${metrics['avg_loss']:,.2f}")
        print(f"   Ort. Tutma Süresi: {metrics['avg_hold_days']:.1f} gün")
        
        print(f"\n📈 RİSK METRİKLERİ:")
        print(f"   Profit Factor:   {metrics['profit_factor']:.2f}")
        print(f"   Max Drawdown:    %{metrics['max_drawdown']:.2f}")
        print(f"   Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
        
        if trades:
            print(f"\n🏆 EN İYİ 5 İŞLEM:")
            best_trades = sorted(trades, key=lambda x: x['pnl'], reverse=True)[:5]
            for i, trade in enumerate(best_trades, 1):
                print(f"\n   {i}. {trade['signal_type']}")
                print(f"      Tarih: {trade['entry_date'].strftime('%Y-%m-%d')} → {trade['exit_date'].strftime('%Y-%m-%d')}")
                print(f"      Fiyat: ${trade['entry_price']:,.2f} → ${trade['exit_price']:,.2f}")
                print(f"      Kar: ${trade['pnl']:,.2f} (%{trade['pnl_percent']:.2f})")
                print(f"      Çıkış: {trade['exit_reason']}")
            
            print(f"\n💔 EN KÖTÜ 5 İŞLEM:")
            worst_trades = sorted(trades, key=lambda x: x['pnl'])[:5]
            for i, trade in enumerate(worst_trades, 1):
                print(f"\n   {i}. {trade['signal_type']}")
                print(f"      Tarih: {trade['entry_date'].strftime('%Y-%m-%d')} → {trade['exit_date'].strftime('%Y-%m-%d')}")
                print(f"      Fiyat: ${trade['entry_price']:,.2f} → ${trade['exit_price']:,.2f}")
                print(f"      Zarar: ${trade['pnl']:,.2f} (%{trade['pnl_percent']:.2f})")
                print(f"      Çıkış: {trade['exit_reason']}")
        
        print("\n" + "="*80)
        print("📌 HEİKİN-ASHİ SINYAL TİPLERİ:")
        print("   • Bullish Reversal + EMA: Güçlü yükseliş dönüşü")
        print("   • Uptrend Continuation: Trend devamı")
        print("   • Strong Momentum: Güçlü momentum")
        print("="*80)


# ANA PROGRAM
if __name__ == "__main__":
    print("="*80)
    print("HEİKİN-ASHİ TRADING BOT - 3 YILLIK BACKTEST")
    print("="*80)
    
    # Parametreler
    SYMBOL = 'BTC/USDT'
    TIMEFRAME = '4h'  # 1h, 4h, 1d
    RISK_PERCENT = 2.0
    INITIAL_BALANCE = 10000
    YEARS = 3
    
    # Bot oluştur
    trader = HeikinAshiTrader(
        symbol=SYMBOL, 
        risk_percent=RISK_PERCENT,
        timeframe=TIMEFRAME
    )
    
    # Veriyi çek
    df = trader.fetch_historical_data(years=YEARS)
    
    # Backtest çalıştır
    df_with_signals, trades, final_balance = trader.backtest(df, INITIAL_BALANCE)
    
    # Sonuçları göster
    trader.print_results(INITIAL_BALANCE, final_balance, trades)
    
    print("\n💡 HEİKİN-ASHİ AVANTAJLARI:")
    print("   ✓ Trend daha net görülür")
    print("   ✓ Gürültü azalır")
    print("   ✓ D")