"""
🤖 BINANCE REAL-TIME 500 COIN SCANNER
Advanced Paper Trading + Auto TP/SL
Geri Dönük Başarı Analizi - %50+ Win Rate Filtresi

DÜZELTMELER:
- Yeniden tarama (HEMEN TARA) race condition düzeltildi
- Backtest ve Kapalı İşlemler sekmesi her tarama sonrası güncelleniyor
- Pozisyon ekranında USDT miktarı (kaç paralık) gösteriliyor
- Kapalı işlemlerde giriş tutarı ve işlem süresi gösteriliyor
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import ccxt
import pandas as pd
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# ============================================================================
# PAPER TRADING
# ============================================================================

class AdvancedPaperTradingAccount:
    def __init__(self, initial_balance=50000):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.positions = {}
        self.closed_trades = []
        self.trade_history = []
        self._lock = threading.Lock()

    def open_trade(self, sembol, entry_price, usdt_size=500, winrate=0, direction='long'):
        with self._lock:
            key = f"{sembol}_{direction}"
            if key in self.positions and self.positions[key]['status'] == 'open':
                return False, f"Açık {direction} var"
            if self.balance < usdt_size:
                return False, f"Bakiye yok ({self.balance:.2f})"

            quantity = usdt_size / entry_price

            if direction == 'long':
                take_profit = entry_price * 1.20   # +%20
                stop_loss   = entry_price * 0.95   # -%5
            else:
                take_profit = entry_price * 0.80   # -%20
                stop_loss   = entry_price * 1.05   # +%5

            self.positions[key] = {
                'sembol':        sembol,
                'direction':     direction,
                'entry_price':   entry_price,
                'entry_time':    datetime.now(),
                'quantity':      quantity,
                'usdt_size':     usdt_size,
                'status':        'open',
                'current_price': entry_price,
                'pnl':           0.0,
                'pnl_percent':   0.0,
                'stop_loss':     stop_loss,
                'take_profit':   take_profit,
                'highest_price': entry_price,
                'lowest_price':  entry_price,
                'winrate':       winrate,
            }

            self.balance -= usdt_size
            self.trade_history.append({
                'type': 'OPEN', 'direction': direction,
                'sembol': sembol, 'price': entry_price, 'time': datetime.now()
            })
            dir_sym = 'LONG' if direction == 'long' else 'SHORT'
            return True, f"{dir_sym} {sembol}: {quantity:.6f} adet @ {entry_price:.6f}  [{usdt_size:.0f} USDT | WR:{winrate:.1f}%]"

    def update_price(self, sembol, current_price):
        closed_list = []
        for direction in ('long', 'short'):
            key = f"{sembol}_{direction}"
            with self._lock:
                if key not in self.positions or self.positions[key]['status'] != 'open':
                    continue
                pos = self.positions[key]
                pos['current_price'] = current_price

                if direction == 'long':
                    pnl_value = (current_price - pos['entry_price']) * pos['quantity']
                else:
                    pnl_value = (pos['entry_price'] - current_price) * pos['quantity']

                pos['pnl']           = pnl_value
                pos['pnl_percent']   = pnl_value / pos['usdt_size'] * 100
                pos['highest_price'] = max(pos['highest_price'], current_price)
                pos['lowest_price']  = min(pos['lowest_price'],  current_price)

                if direction == 'long':
                    if current_price <= pos['stop_loss']:
                        r = self._close_trade_locked(key, current_price, "STOP LOSS")
                        if r: closed_list.append(r)
                    elif current_price >= pos['take_profit']:
                        r = self._close_trade_locked(key, current_price, "TAKE PROFIT")
                        if r: closed_list.append(r)
                else:
                    if current_price >= pos['stop_loss']:
                        r = self._close_trade_locked(key, current_price, "STOP LOSS")
                        if r: closed_list.append(r)
                    elif current_price <= pos['take_profit']:
                        r = self._close_trade_locked(key, current_price, "TAKE PROFIT")
                        if r: closed_list.append(r)

        return closed_list if closed_list else None

    def _close_trade_locked(self, key, exit_price, reason="MANUAL"):
        """Lock dışarıdan alınmış halde çağrılır."""
        if key not in self.positions or self.positions[key]['status'] != 'open':
            return None
        pos       = self.positions[key]
        direction = pos['direction']
        sembol    = pos['sembol']

        if direction == 'long':
            exit_value = pos['quantity'] * exit_price
            pnl        = exit_value - pos['usdt_size']
        else:
            pnl        = (pos['entry_price'] - exit_price) * pos['quantity']
            exit_value = pos['usdt_size'] + pnl

        pnl_pct  = pnl / pos['usdt_size'] * 100
        duration = (datetime.now() - pos['entry_time']).total_seconds()

        closed = {
            'sembol':           sembol,
            'key':              key,
            'direction':        direction,
            'entry_price':      pos['entry_price'],
            'exit_price':       exit_price,
            'quantity':         pos['quantity'],
            'usdt_size':        pos['usdt_size'],
            'pnl':              pnl,
            'pnl_percent':      pnl_pct,
            'reason':           reason,
            'duration_seconds': duration,
            'highest_price':    pos['highest_price'],
            'lowest_price':     pos['lowest_price'],
            'tp_level':         pos['take_profit'],
            'sl_level':         pos['stop_loss'],
            'winrate':          pos.get('winrate', 0),
            'exit_time':        datetime.now(),
        }
        self.closed_trades.append(closed)
        self.balance    += max(exit_value, 0)
        pos['status']    = 'closed'
        self.trade_history.append({
            'type': 'CLOSE', 'direction': direction, 'sembol': sembol,
            'reason': reason, 'price': exit_price, 'pnl': pnl_pct, 'time': datetime.now()
        })
        return closed

    def close_trade(self, key, exit_price, reason="MANUAL"):
        with self._lock:
            return self._close_trade_locked(key, exit_price, reason)

    def get_portfolio_value(self, prices_dict):
        total = self.balance
        for key, pos in self.positions.items():
            if pos['status'] != 'open':
                continue
            sym   = pos['sembol']
            price = prices_dict.get(sym, pos['entry_price'])
            if pos['direction'] == 'long':
                total += pos['quantity'] * price
            else:
                pnl    = (pos['entry_price'] - price) * pos['quantity']
                total += pos['usdt_size'] + pnl
        return total

    def get_stats(self):
        trades = self.closed_trades
        if not trades:
            return {'toplam_islem': 0, 'basarili_islem': 0, 'basarisiz_islem': 0,
                    'win_rate': 0, 'ort_kazanc': 0, 'toplam_pnl': 0, 'kazanc_faktoru': 0}
        total     = len(trades)
        winning   = sum(1 for t in trades if t['pnl'] > 0)
        losing    = sum(1 for t in trades if t['pnl'] < 0)
        total_pnl = sum(t['pnl']        for t in trades)
        avg_ret   = sum(t['pnl_percent'] for t in trades) / total
        win_pnl   = sum(t['pnl']         for t in trades if t['pnl'] > 0)
        loss_pnl  = sum(abs(t['pnl'])    for t in trades if t['pnl'] < 0)
        return {
            'toplam_islem':    total,
            'basarili_islem':  winning,
            'basarisiz_islem': losing,
            'win_rate':        winning / total * 100,
            'ort_kazanc':      avg_ret,
            'toplam_pnl':      total_pnl,
            'kazanc_faktoru':  win_pnl / loss_pnl if loss_pnl > 0 else 0,
        }


# ============================================================================
# SCANNER
# ============================================================================

class Advanced500Scanner:
    WINRATE_THRESHOLD  = 50.0
    SUPPORT_MAX_DIST   = 5.0
    SCAN_INTERVAL_SEC  = 30 * 60

    def __init__(self):
        try:
            self.exchange = ccxt.binance({'enableRateLimit': True})
        except Exception:
            self.exchange = None

        self.paper_trading   = AdvancedPaperTradingAccount(50000)
        self.buy_signals     = {}
        self.sell_signals    = {}
        self.current_prices  = {}
        self.is_running      = False
        self.is_scanning     = False
        self._scan_lock      = threading.Lock()   # ← YENİ: çift tarama engeli
        self.update_queue    = queue.Queue()
        self.scan_count      = 0
        self.total_signals   = 0
        self._valid_symbols  = None
        self._last_scan_time = 0

    # ── Semboller ──────────────────────────────────────────────────
    def get_valid_symbols(self):
        if self._valid_symbols is not None:
            return self._valid_symbols
        try:
            self.update_queue.put(('status', 'Binance sembolleri yükleniyor...'))
            markets = self.exchange.load_markets()
            usdt_pairs = [
                sym for sym, mkt in markets.items()
                if sym.endswith('/USDT')
                and mkt.get('spot', False)
                and mkt.get('active', False)
                and mkt.get('type', '') not in ('future', 'swap')
            ]
            self.update_queue.put(('status', f'{len(usdt_pairs)} sembol, volume sıralanıyor...'))
            try:
                tickers = self.exchange.fetch_tickers()
                vols = [(p, tickers.get(p, {}).get('quoteVolume') or 0) for p in usdt_pairs]
                vols.sort(key=lambda x: x[1], reverse=True)
                self._valid_symbols = [p for p, _ in vols[:500]]
            except Exception:
                self._valid_symbols = usdt_pairs[:500]
            self.update_queue.put(('status', f'{len(self._valid_symbols)} sembol hazır'))
            return self._valid_symbols
        except Exception as e:
            self.update_queue.put(('status', f'Sembol hatası: {e}'))
            self._valid_symbols = self._fallback()
            return self._valid_symbols

    def _fallback(self):
        return [
            "BTC/USDT","ETH/USDT","BNB/USDT","XRP/USDT","SOL/USDT","ADA/USDT",
            "DOGE/USDT","DOT/USDT","LINK/USDT","LTC/USDT","TRX/USDT","BCH/USDT",
            "XLM/USDT","AVAX/USDT","ATOM/USDT","UNI/USDT","AAVE/USDT","MATIC/USDT",
            "NEAR/USDT","VET/USDT","ALGO/USDT","MANA/USDT","FIL/USDT","ICP/USDT",
            "SAND/USDT","GALA/USDT","ARB/USDT","OP/USDT","APE/USDT","GMX/USDT",
            "PENDLE/USDT","INJ/USDT","SUI/USDT","SEI/USDT","BLUR/USDT","RENDER/USDT",
            "JUP/USDT","TIA/USDT","STX/USDT","TON/USDT","JTO/USDT","ETHFI/USDT",
            "ONDO/USDT","PYTH/USDT","WLD/USDT","BONK/USDT","SHIB/USDT","PEPE/USDT",
            "FLOKI/USDT","WIF/USDT","DYDX/USDT","COMP/USDT","CRV/USDT","SNX/USDT",
            "GRT/USDT","MKR/USDT","YFI/USDT","LUNC/USDT","RSR/USDT","MASK/USDT",
            "AXS/USDT","GMT/USDT","ANKR/USDT","MAGIC/USDT","HNT/USDT","ROSE/USDT",
            "ENS/USDT","RUNE/USDT","ZRX/USDT","HBAR/USDT","TAO/USDT","BEAM/USDT",
            "ACT/USDT","TRUMP/USDT","PNUT/USDT","DOGS/USDT","NEIRO/USDT","EIGEN/USDT",
            "SCR/USDT","IO/USDT","ZK/USDT","NOT/USDT","PORTAL/USDT","DYM/USDT",
            "STRK/USDT","MANTA/USDT","SAGA/USDT","W/USDT","ENA/USDT","LISTA/USDT",
            "ZRO/USDT","OMNI/USDT","REZ/USDT","WEMIX/USDT","BAKE/USDT","CFX/USDT",
            "CHZ/USDT","CTSI/USDT","EGLD/USDT","ELF/USDT","ENJ/USDT","FTM/USDT",
            "IMX/USDT","IOST/USDT","JASMY/USDT","KNC/USDT","KSM/USDT","LPT/USDT",
            "LRC/USDT","MINA/USDT","NMR/USDT","ONE/USDT","ONT/USDT","PEOPLE/USDT",
            "QNT/USDT","QTUM/USDT","RAY/USDT","RLC/USDT","SKL/USDT","STORJ/USDT",
            "THETA/USDT","TWT/USDT","UMA/USDT","WAVES/USDT","WOO/USDT","XEC/USDT",
            "XTZ/USDT","XVS/USDT","YGG/USDT","ZEC/USDT","ZIL/USDT","1INCH/USDT",
            "APT/USDT","ARK/USDT","AUDIO/USDT","BAL/USDT","BAND/USDT","BAT/USDT",
            "CLV/USDT","COTI/USDT","CYBER/USDT","DASH/USDT","DCR/USDT","EOS/USDT",
            "ETC/USDT","FET/USDT","FLOW/USDT","GAL/USDT","GLM/USDT","HOT/USDT",
            "ID/USDT","KAVA/USDT","MTL/USDT","NKN/USDT","OGN/USDT","POLS/USDT",
            "POWR/USDT","PROM/USDT","RDNT/USDT","SSV/USDT","SUPER/USDT","SUSHI/USDT",
            "SYN/USDT","VANRY/USDT","WRX/USDT","LOOM/USDT","TRIBE/USDT",
        ]

    # ── Heiken Ashi ────────────────────────────────────────────────
    def heiken_ashi(self, df):
        df = df.copy()
        df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        ha_open = [(df['open'].iloc[0] + df['close'].iloc[0]) / 2]
        for i in range(1, len(df)):
            ha_open.append((ha_open[-1] + df['HA_Close'].iloc[i-1]) / 2)
        df['HA_Open'] = ha_open
        df['HA_High'] = df[['high', 'HA_Open', 'HA_Close']].max(axis=1)
        df['HA_Low']  = df[['low',  'HA_Open', 'HA_Close']].min(axis=1)
        return df

    # ── TD Sequential ──────────────────────────────────────────────
    def td_sequential(self, df):
        df  = df.copy()
        df  = self.heiken_ashi(df)
        ha  = df['HA_Close'].values
        n   = len(ha)

        buy_setup  = [0] * n
        sell_setup = [0] * n
        bc = sc = 0
        for i in range(n):
            if i >= 4 and ha[i] < ha[i-4]:
                bc = min(bc + 1, 9)
            else:
                bc = 0
            buy_setup[i] = bc

            if i >= 4 and ha[i] > ha[i-4]:
                sc = min(sc + 1, 9)
            else:
                sc = 0
            sell_setup[i] = sc

        df['buy_setup']  = buy_setup
        df['sell_setup'] = sell_setup
        return df

    # ── Backtest ───────────────────────────────────────────────────
    def backtest_td9(self, df, signal_type='buy', tp_pct=0.20, sl_pct=0.05, forward_bars=20):
        setup_col = 'buy_setup' if signal_type == 'buy' else 'sell_setup'
        closes = df['close'].values
        highs  = df['high'].values
        lows   = df['low'].values
        n      = len(df)
        setups = df[setup_col].values

        total = wins = 0

        for i in range(4, n - forward_bars - 1):
            if int(setups[i]) != 9:
                continue
            entry = closes[i]
            if entry <= 0:
                continue

            tp = entry * (1 + tp_pct) if signal_type == 'buy' else entry * (1 - tp_pct)
            sl = entry * (1 - sl_pct) if signal_type == 'buy' else entry * (1 + sl_pct)

            total  += 1
            outcome = None

            for j in range(i + 1, min(i + forward_bars + 1, n)):
                h, l = highs[j], lows[j]
                if signal_type == 'buy':
                    if h >= tp: outcome = 'win';  break
                    if l <= sl: outcome = 'loss'; break
                else:
                    if l <= tp: outcome = 'win';  break
                    if h >= sl: outcome = 'loss'; break

            if outcome == 'win':
                wins += 1
            elif outcome is None:
                fin = closes[min(i + forward_bars, n - 1)]
                if signal_type == 'buy'  and fin > entry: wins += 1
                if signal_type == 'sell' and fin < entry: wins += 1

        wr = (wins / total * 100) if total > 0 else 0.0
        return wr, total, wins

    # ── Destek Seviyesi ───────────────────────────────────────────
    def find_support_level(self, df, lookback=50, tolerance=0.015):
        lows = df['low'].values[-lookback:]
        n    = len(lows)

        pivot_lows = []
        for i in range(2, n - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                pivot_lows.append(lows[i])

        if not pivot_lows:
            support     = float(min(lows))
            touch_count = 1
        else:
            best_support  = pivot_lows[0]
            best_touches  = 1
            for ref in pivot_lows:
                touches = sum(1 for l in pivot_lows if abs(l - ref) / ref <= tolerance)
                if touches > best_touches:
                    best_touches = touches
                    best_support = ref
            support     = best_support
            touch_count = best_touches

        current_price = float(df['close'].iloc[-1])
        dist_pct      = (current_price - support) / support * 100
        return support, touch_count, dist_pct

    # ── Direnç Seviyesi ───────────────────────────────────────────
    def find_resistance_level(self, df, lookback=50, tolerance=0.015):
        highs = df['high'].values[-lookback:]
        n     = len(highs)

        pivot_highs = []
        for i in range(2, n - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                pivot_highs.append(highs[i])

        if not pivot_highs:
            resistance  = float(max(highs))
            touch_count = 1
        else:
            best_res     = pivot_highs[0]
            best_touches = 1
            for ref in pivot_highs:
                touches = sum(1 for h in pivot_highs if abs(h - ref) / ref <= tolerance)
                if touches > best_touches:
                    best_touches = touches
                    best_res     = ref
            resistance  = best_res
            touch_count = best_touches

        current_price = float(df['close'].iloc[-1])
        dist_pct      = (resistance - current_price) / current_price * 100
        return resistance, touch_count, dist_pct

    def scan_crypto(self, sembol):
        if not self.exchange:
            return None
        try:
            ohlcv = self.exchange.fetch_ohlcv(sembol, '1h', limit=1000)
            if not ohlcv or len(ohlcv) < 50:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = self.td_sequential(df)

            son_buy   = int(df['buy_setup'].iloc[-1])
            son_sell  = int(df['sell_setup'].iloc[-1])
            son_price = float(df['close'].iloc[-1])
            ha_close  = float(df['HA_Close'].iloc[-1])
            ha_open   = float(df['HA_Open'].iloc[-1])

            total_bars = len(df)
            days_back  = round(total_bars / 24, 1)
            date_from  = df.index[0].strftime('%Y-%m-%d')
            date_to    = df.index[-1].strftime('%Y-%m-%d')

            buy_wr = buy_tot = buy_wins = 0
            sell_wr = sell_tot = sell_wins = 0

            if son_buy == 9:
                buy_wr, buy_tot, buy_wins = self.backtest_td9(df, 'buy')
            if son_sell == 9:
                sell_wr, sell_tot, sell_wins = self.backtest_td9(df, 'sell')

            support_price,    support_touches,    support_dist_pct    = self.find_support_level(df,    lookback=100)
            resistance_price, resistance_touches, resistance_dist_pct = self.find_resistance_level(df, lookback=100)

            wr_ok_buy  = buy_wr  >= self.WINRATE_THRESHOLD
            wr_ok_sell = sell_wr >= self.WINRATE_THRESHOLD
            supp_ok    = 0.0 < support_dist_pct    <= self.SUPPORT_MAX_DIST
            res_ok     = 0.0 < resistance_dist_pct <= self.SUPPORT_MAX_DIST
            buy_passed  = wr_ok_buy  and supp_ok
            sell_passed = wr_ok_sell and res_ok

            if support_dist_pct < 0:
                supp_status = f'DESTEK KIRILMIŞ ({support_dist_pct:+.1f}%)'
            elif support_dist_pct <= self.SUPPORT_MAX_DIST:
                supp_status = f'DESTEĞE YAKIN (+{support_dist_pct:.1f}%)'
            else:
                supp_status = f'DESTEK UZAK (+{support_dist_pct:.1f}%)'

            if resistance_dist_pct < 0:
                res_status = f'DİRENÇ KIRILMIŞ ({resistance_dist_pct:+.1f}%)'
            elif resistance_dist_pct <= self.SUPPORT_MAX_DIST:
                res_status = f'DİRENCE YAKIN (+{resistance_dist_pct:.1f}%)'
            else:
                res_status = f'DİRENÇ UZAK (+{resistance_dist_pct:.1f}%)'

            return {
                'sembol': sembol.split('/')[0],
                'full_symbol': sembol,
                'price': son_price,
                'buy_setup': son_buy,   'sell_setup': son_sell,
                'buy_9': son_buy == 9,  'sell_9': son_sell == 9,
                'ha_color': 'HAY' if ha_close > ha_open else 'AY',
                'buy_winrate': buy_wr, 'buy_total_signals': buy_tot, 'buy_wins': buy_wins,
                'buy_wr_ok':  wr_ok_buy,
                'sell_winrate': sell_wr, 'sell_total_signals': sell_tot, 'sell_wins': sell_wins,
                'sell_wr_ok': wr_ok_sell,
                'support_price':    round(support_price, 8),
                'support_touches':  support_touches,
                'support_dist_pct': round(support_dist_pct, 2),
                'support_ok':       supp_ok,
                'support_status':   supp_status,
                'resistance_price':    round(resistance_price, 8),
                'resistance_touches':  resistance_touches,
                'resistance_dist_pct': round(resistance_dist_pct, 2),
                'resistance_ok':       res_ok,
                'resistance_status':   res_status,
                'buy_passed':  buy_passed,
                'sell_passed': sell_passed,
                'total_bars': total_bars, 'days_back': days_back,
                'date_from':  date_from,  'date_to':   date_to,
            }
        except Exception:
            return None

    # ── Ana Tarama ────────────────────────────────────────────────
    def run_scan(self):
        # ── DÜZELTME: Çift tarama önleme ──────────────────────────
        if not self._scan_lock.acquire(blocking=False):
            self.update_queue.put(('status', 'Tarama zaten çalışıyor, atlandı'))
            return
        try:
            self._run_scan_internal()
        finally:
            self._scan_lock.release()

    def _run_scan_internal(self):
        if not self.exchange:
            self.update_queue.put(('status', 'Binance API hatası')); return

        self.is_scanning = True
        self.scan_count += 1
        kriptolar = self.get_valid_symbols()

        self.update_queue.put(('status', f'{len(kriptolar)} coin taranıyor (1H + Backtest)...'))
        self.buy_signals.clear()
        self.sell_signals.clear()

        ts = datetime.now().strftime('%H:%M:%S')
        self.update_queue.put(('coin_log', '='*70))
        self.update_queue.put(('coin_log', f'TARAMA #{self.scan_count}  başladı  {ts}'))
        self.update_queue.put(('coin_log', f'{len(kriptolar)} coin taranacak:'))
        for i in range(0, len(kriptolar), 10):
            chunk = kriptolar[i:i+10]
            self.update_queue.put(('coin_log', '  ' + '  '.join(s.split('/')[0] for s in chunk)))
        self.update_queue.put(('coin_log', '-'*70))

        completed = failed = 0

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(self.scan_crypto, s): s for s in kriptolar}

            for future in as_completed(futures):
                raw_sym   = futures[future]
                completed += 1
                try:
                    res = future.result(timeout=15)
                    if res:
                        coin = res['sembol']
                        self.current_prices[coin] = res['price']
                        signal_tag = ''

                        if res['buy_9']:
                            self.buy_signals[coin] = res
                            self.total_signals += 1
                            wr     = res['buy_winrate']
                            sdist  = res['support_dist_pct']
                            wr_ok  = res['buy_wr_ok']
                            s_stat = res['support_status']
                            verdict = ('GEÇTI-LONG' if res['buy_passed']
                                       else (f'ATILDI-WR:{wr:.0f}%<{self.WINRATE_THRESHOLD:.0f}%' if not wr_ok
                                             else f'ATILDI-{s_stat}'))
                            signal_tag += (f'  ***BUY9 WR:{wr:.1f}%({res["buy_wins"]}/{res["buy_total_signals"]})'
                                           f' | {s_stat} | {verdict}***')

                        if res['sell_9']:
                            self.sell_signals[coin] = res
                            self.total_signals += 1
                            wr     = res['sell_winrate']
                            rdist  = res['resistance_dist_pct']
                            wr_ok  = res['sell_wr_ok']
                            r_stat = res['resistance_status']
                            verdict = ('GEÇTI-SHORT' if res['sell_passed']
                                       else (f'ATILDI-WR:{wr:.0f}%<{self.WINRATE_THRESHOLD:.0f}%' if not wr_ok
                                             else f'ATILDI-{r_stat}'))
                            signal_tag += (f'  ***SELL9 WR:{wr:.1f}%({res["sell_wins"]}/{res["sell_total_signals"]})'
                                           f' | {r_stat} | {verdict}***')

                        ha_sym = 'YUK' if res['ha_color'] == 'HAY' else 'DUS'
                        self.update_queue.put(('coin_log',
                            f'[{completed:>3}/{len(kriptolar)}] {coin:<12} '
                            f'${res["price"]:>14.6f}  B:{res["buy_setup"]}  S:{res["sell_setup"]}  '
                            f'{ha_sym}{signal_tag}'))
                    else:
                        failed += 1
                        cn = raw_sym.split('/')[0]
                        self.update_queue.put(('coin_log',
                            f'[{completed:>3}/{len(kriptolar)}] {cn:<12} -- VERİ YOK'))
                except Exception as e:
                    failed += 1
                    cn = raw_sym.split('/')[0]
                    self.update_queue.put(('coin_log',
                        f'[{completed:>3}/{len(kriptolar)}] {cn:<12} -- HATA: {str(e)[:40]}'))

                self.update_queue.put(('progress', completed / len(kriptolar) * 100))
                if completed % 50 == 0:
                    self.update_queue.put(('status',
                        f'{completed}/{len(kriptolar)} tarandı | '
                        f'BUY:{len(self.buy_signals)} SELL:{len(self.sell_signals)} | HATA:{failed}'))

        q_buys  = sorted([(s, g) for s, g in self.buy_signals.items()  if g['buy_passed']],
                          key=lambda x: x[1]['buy_winrate'], reverse=True)
        q_sells = sorted([(s, g) for s, g in self.sell_signals.items() if g['sell_passed']],
                          key=lambda x: x[1]['sell_winrate'], reverse=True)
        w_buys  = [(s, g) for s, g in self.buy_signals.items()  if not g['buy_passed']]
        w_sells = [(s, g) for s, g in self.sell_signals.items() if not g['sell_passed']]

        sep     = '='*70
        summary = [
            sep,
            f'TARAMA #{self.scan_count} TAMAMLANDI  ({datetime.now().strftime("%H:%M:%S")})',
            f'Başarılı: {completed-failed}/{len(kriptolar)}  Hata: {failed}',
            f'Filtre: WR > %{self.WINRATE_THRESHOLD:.0f}  |  BUY→Desteğe <= %{self.SUPPORT_MAX_DIST:.0f}  |  SELL→Dirençe <= %{self.SUPPORT_MAX_DIST:.0f}',
            f'BUY9  toplam: {len(self.buy_signals)}  ->  LONG açılacak: {len(q_buys)}  Atılan: {len(w_buys)}',
            f'SELL9 toplam: {len(self.sell_signals)} ->  SHORT açılacak: {len(q_sells)}  Atılan: {len(w_sells)}',
        ]
        if q_buys:
            summary.append('--- LONG AÇILACAK ---')
            for s, g in q_buys[:10]:
                summary.append(
                    f'  -> {s:<12} WR:{g["buy_winrate"]:.1f}%  '
                    f'Dest:{g["support_dist_pct"]:+.1f}%  ${g["price"]:.6f}')
        if q_sells:
            summary.append('--- SHORT AÇILACAK ---')
            for s, g in q_sells[:10]:
                summary.append(
                    f'  -> {s:<12} WR:{g["sell_winrate"]:.1f}%  '
                    f'Direnc:{g["resistance_dist_pct"]:+.1f}%  ${g["price"]:.6f}')
        summary.append(sep)

        for line in summary:
            self.update_queue.put(('coin_log', line))
            self.update_queue.put(('log',      line))

        # ── Auto Trade ─────────────────────────────────────────────
        opened  = 0
        MAX_POS = 15
        MAX_NEW = 5

        self.update_queue.put(('log',
            f'--- AUTO TRADE: BUY:{len(q_buys)} kaliteli  SELL:{len(q_sells)} kaliteli ---'))

        for i, (sembol, sig) in enumerate(q_buys[:MAX_NEW]):
            try:
                open_count = sum(1 for p in self.paper_trading.positions.values() if p['status'] == 'open')
                if open_count >= MAX_POS:
                    sig['trade_result'] = 'MAX_POS'
                    break
                key = f"{sembol}_long"
                if key in self.paper_trading.positions and self.paper_trading.positions[key]['status'] == 'open':
                    sig['trade_result'] = 'HATA:Zaten açık'
                    continue
                ok, msg = self.paper_trading.open_trade(sembol, sig['price'], usdt_size=500, winrate=sig['buy_winrate'])
                self.update_queue.put(('log', f'  LONG -> {msg}'))
                sig['trade_result'] = 'ACILDI' if ok else f'HATA:{msg}'
                if ok: opened += 1
            except Exception as ex:
                sig['trade_result'] = f'EXCEPTION:{ex}'

        for sembol, sig in q_buys[MAX_NEW:]:
            sig.setdefault('trade_result', 'LIMIT_ASIM')

        for i, (sembol, sig) in enumerate(q_sells[:MAX_NEW]):
            try:
                open_count = sum(1 for p in self.paper_trading.positions.values() if p['status'] == 'open')
                if open_count >= MAX_POS:
                    sig['trade_result'] = 'MAX_POS'
                    break
                key = f"{sembol}_short"
                if key in self.paper_trading.positions and self.paper_trading.positions[key]['status'] == 'open':
                    sig['trade_result'] = 'HATA:Zaten short açık'
                    continue
                ok, msg = self.paper_trading.open_trade(
                    sembol, sig['price'], usdt_size=500, winrate=sig['sell_winrate'], direction='short')
                self.update_queue.put(('log', f'  SHORT -> {msg}'))
                sig['trade_result'] = 'SHORT_ACILDI' if ok else f'HATA:{msg}'
                if ok: opened += 1
            except Exception as ex:
                sig['trade_result'] = f'EXCEPTION:{ex}'

        for sembol, sig in q_sells[MAX_NEW:]:
            sig.setdefault('trade_result', 'LIMIT_ASIM')

        self.update_queue.put(('complete', {
            'buy_count':     len(self.buy_signals),
            'sell_count':    len(self.sell_signals),
            'qualified_buy': len(q_buys),
            'opened':        opened,
            'scan_count':    self.scan_count,
        }))
        # ── DÜZELTME: Tüm tabları yenile sinyali ──────────────────
        self.update_queue.put(('refresh_all', True))
        self._last_scan_time = time.time()
        self.is_scanning     = False

    # ── Canlı Fiyat ───────────────────────────────────────────────
    def fetch_live_prices(self):
        symbols_to_check = set()
        for key, pos in self.paper_trading.positions.items():
            if pos['status'] == 'open':
                symbols_to_check.add(pos['sembol'])

        if not symbols_to_check or not self.exchange:
            return

        for sym in symbols_to_check:
            try:
                ticker = self.exchange.fetch_ticker(f"{sym}/USDT")
                self.current_prices[sym] = float(ticker['last'])
            except Exception:
                pass

    # ── Sürekli Döngü ─────────────────────────────────────────────
    def run_continuous(self):
        self.is_running = True
        self.update_queue.put(('status', 'Sistem aktif'))
        last_price_fetch = 0

        while self.is_running:
            now       = time.time()
            elapsed   = now - self._last_scan_time
            remaining = max(0, self.SCAN_INTERVAL_SEC - elapsed)

            if now - last_price_fetch >= 30:
                self.fetch_live_prices()
                last_price_fetch = now

            if not self.is_scanning:
                symbols_to_check = set()
                for key, pos in self.paper_trading.positions.items():
                    if pos['status'] == 'open':
                        symbols_to_check.add(pos['sembol'])

                for sym in symbols_to_check:
                    if sym in self.current_prices:
                        results = self.paper_trading.update_price(sym, self.current_prices[sym])
                        if results:
                            for res in results:
                                icon    = 'KÂRZANÇ' if res['pnl'] > 0 else 'KAYIP'
                                dir_sym = 'LONG' if res['direction'] == 'long' else 'SHORT'
                                self.update_queue.put(('log',
                                    f'{icon} {dir_sym} KAPANDI: {sym} | '
                                    f'{res["reason"]} | {res["pnl_percent"]:.2f}% | '
                                    f'{res["usdt_size"]:.0f} USDT'))
                                self.update_queue.put(('refresh_closed', True))

            if not self.is_scanning and self.scan_count > 0:
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                self.update_queue.put(('countdown',
                    f'Sonraki tarama: {mins}dk {secs}sn  '
                    f'(her {self.SCAN_INTERVAL_SEC//60} dk)  '
                    f'Son tarama: #{self.scan_count}'))

            if not self.is_scanning and (self._last_scan_time == 0 or elapsed >= self.SCAN_INTERVAL_SEC):
                threading.Thread(target=self.run_scan, daemon=True).start()
                time.sleep(3)
            else:
                time.sleep(10)


# ============================================================================
# GUI
# ============================================================================

class AdvancedScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('BINANCE 500 COIN SCANNER - 1H + GERİ DÖNÜK BAŞARI ANALİZİ')
        self.root.geometry('1500x900')
        self.root.configure(bg='#0d0d0d')
        self.scanner = Advanced500Scanner()
        self.setup_ui()
        self.update_loop()

    def setup_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        tk.Label(main,
                 text='BINANCE 500 COIN SCANNER  |  1H  |  GERİ DÖNÜK BAŞARI ANALİZİ  |  >=50% WR FİLTRESİ',
                 font=('Arial', 13, 'bold'), bg='#0d0d0d', fg='#00FF88').pack(pady=6)

        btn = tk.Frame(main, bg='#0d0d0d')
        btn.pack(fill=tk.X, pady=4)

        def mkbtn(parent, text, cmd, bg, state=tk.NORMAL):
            b = tk.Button(parent, text=text, command=cmd, font=('Arial',11,'bold'),
                          bg=bg, fg='white', padx=14, pady=7, state=state)
            b.pack(side=tk.LEFT, padx=4)
            return b

        self.start_btn  = mkbtn(btn, 'BAŞLAT',    self.start_system,  '#007700')
        self.stop_btn   = mkbtn(btn, 'DURDUR',    self.stop_system,   '#CC0000', tk.DISABLED)
        self.rescan_btn = mkbtn(btn, 'HEMEN TARA', self.manual_scan,   '#003388', tk.DISABLED)
        mkbtn(btn, 'ÇIKIŞ', self.root.quit, '#550000')

        tk.Label(btn, text='Tarama aralığı (dk):', font=('Arial',9),
                 bg='#0d0d0d', fg='#AAAAAA').pack(side=tk.LEFT, padx=(12,2))
        self.interval_var = tk.IntVar(value=self.scanner.SCAN_INTERVAL_SEC // 60)
        interval_spin = tk.Spinbox(btn, from_=5, to=120, increment=5,
                                   textvariable=self.interval_var, width=5,
                                   font=('Arial',10), bg='#222222', fg='white',
                                   command=self.update_interval)
        interval_spin.pack(side=tk.LEFT, padx=2)
        interval_spin.bind('<Return>', lambda e: self.update_interval())

        self.status_label = tk.Label(btn, text='Hazır', font=('Arial',10),
                                     bg='#0d0d0d', fg='#FFFFFF')
        self.status_label.pack(side=tk.RIGHT, padx=8)

        self.countdown_label = tk.Label(btn, text='', font=('Arial', 10, 'bold'),
                                        bg='#0d0d0d', fg='#FFAA00')
        self.countdown_label.pack(side=tk.RIGHT, padx=8)

        self.coin_count_label = tk.Label(btn, text='Coin: -', font=('Arial',10),
                                         bg='#0d0d0d', fg='#888888')
        self.coin_count_label.pack(side=tk.RIGHT, padx=8)

        pf = tk.Frame(main, bg='#0d0d0d')
        pf.pack(fill=tk.X, pady=4)
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(pf, variable=self.progress_var, maximum=100).pack(fill=tk.X)

        nb = ttk.Notebook(main)
        nb.pack(fill=tk.BOTH, expand=True, pady=6)
        self.nb = nb

        def tab(title, fg='#00FF88'):
            st = scrolledtext.ScrolledText(nb, wrap=tk.WORD, font=('Courier', 9),
                                           bg='#111111', fg=fg, height=28)
            st.pack(fill=tk.BOTH, expand=True)
            nb.add(st, text=title)
            st.config(state=tk.DISABLED)
            return st

        self.t_positions = tab('AÇIK POZİSYONLAR')
        self.t_signals   = tab('SİNYALLER + WIN RATE')
        self.t_backtest  = tab('BACKTEST SONUÇLARI', '#AADDFF')
        self.t_closed    = tab('KAPALI İŞLEMLER')
        self.t_stats     = tab('İSTATİSTİKLER')
        self.t_log       = tab('LOG', '#FFFF88')
        self.t_scan_log  = tab('TARANAN COİNLER', '#88CCFF')

        self._append(self.t_log,      'Sistem hazır. BAŞLAT butonuna tıkla.')
        self._append(self.t_scan_log, 'Tarama başladığında her coin sıra ile loglanacak.')

    def _append(self, w, text, tag=None):
        w.config(state=tk.NORMAL)
        if tag:
            w.insert(tk.END, text + '\n', tag)
        else:
            w.insert(tk.END, text + '\n')
        w.see(tk.END)
        w.config(state=tk.DISABLED)

    def _set(self, w, text):
        w.config(state=tk.NORMAL)
        w.delete('1.0', tk.END)
        w.insert(tk.END, text)
        w.config(state=tk.DISABLED)

    # ── Kontroller ─────────────────────────────────────────────────
    def start_system(self):
        if not self.scanner.is_running:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.rescan_btn.config(state=tk.NORMAL)
            threading.Thread(target=self.scanner.run_continuous, daemon=True).start()

    def stop_system(self):
        self.scanner.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.rescan_btn.config(state=tk.DISABLED)
        self.status_label.config(text='Durduruldu')

    def manual_scan(self):
        """DÜZELTME: is_scanning bayrağını hemen set edip thread başlat."""
        if self.scanner.is_scanning:
            self.add_log('Tarama zaten çalışıyor...')
            return
        self.scanner._last_scan_time = 0
        self.add_log('Manuel tarama başlatılıyor...')
        threading.Thread(target=self.scanner.run_scan, daemon=True).start()

    def update_interval(self):
        mins = self.interval_var.get()
        mins = max(5, min(120, mins))
        self.scanner.SCAN_INTERVAL_SEC = mins * 60
        self.interval_var.set(mins)
        self.add_log(f'Tarama aralığı güncellendi: {mins} dakika')

    def add_log(self, msg):
        self._append(self.t_log, f'[{datetime.now().strftime("%H:%M:%S")}] {msg}')

    def add_coin_log(self, msg):
        w = self.t_scan_log
        w.config(state=tk.NORMAL)
        upper = msg.upper()
        if 'GECTI' in upper or 'GEÇTİ' in upper:
            tag = 'pass'; w.tag_config(tag, foreground='#00FF66', font=('Courier', 9, 'bold'))
        elif 'HATA' in upper or 'YOK' in upper:
            tag = 'err';  w.tag_config(tag, foreground='#555555')
        elif 'TARAMA' in upper or '===' in msg or '---' in msg:
            tag = 'hdr';  w.tag_config(tag, foreground='#FFD700', font=('Courier', 9, 'bold'))
        elif '->' in msg:
            tag = 'detail'; w.tag_config(tag, foreground='#AADDFF')
        else:
            tag = None
        if tag:
            w.insert(tk.END, msg + '\n', tag)
        else:
            w.insert(tk.END, msg + '\n')
        w.see(tk.END)
        w.config(state=tk.DISABLED)

    # ── Tab Güncellemeleri ─────────────────────────────────────────

    def update_positions(self):
        pt  = self.scanner.paper_trading
        pv  = pt.get_portfolio_value(self.scanner.current_prices)
        pnl = pv - pt.initial_balance
        pnl_pct = pnl / pt.initial_balance * 100
        ops = {k: v for k, v in pt.positions.items() if v['status'] == 'open'}
        long_ops  = {k: v for k, v in ops.items() if v['direction'] == 'long'}
        short_ops = {k: v for k, v in ops.items() if v['direction'] == 'short'}

        L = [
            'AÇIK POZİSYONLAR  (LONG: TP+20% SL-5%  |  SHORT: TP-20% SL+5%)',
            '='*145,
            f'Bakiye: {pt.balance:>12,.2f} USDT  |  Long: {len(long_ops)}  Short: {len(short_ops)}  |  '
            f'Portföy: {pv:>12,.2f} USDT  |  P&L: {pnl:+.2f} USDT ({pnl_pct:+.2f}%)',
            '-'*145,
            # ── DÜZELTME: USDT sütunu eklendi ──
            f'{"Yön":<6} {"Coin":<10} {"USDT":>8} {"Adet":>12} {"Giriş":>14} {"Güncel":>14} '
            f'{"TP":>14} {"SL":>14} {"PnL $":>10} {"PnL %":>7} {"WR":>6}  TP Uzak  SL Uzak',
            '-'*145,
        ]

        if ops:
            for key, pos in sorted(ops.items()):
                sym     = pos['sembol']
                dire    = pos['direction']
                cur     = self.scanner.current_prices.get(sym, pos['entry_price'])
                icon    = '+' if pos['pnl'] > 0 else ('-' if pos['pnl'] < 0 else '=')
                dir_sym = 'LONG ' if dire == 'long' else 'SHORT'

                if dire == 'long':
                    dtp   = (pos['take_profit'] - cur) / cur * 100
                    dsl   = (cur - pos['stop_loss'])  / cur * 100
                    pnl_v = (cur - pos['entry_price']) * pos['quantity']
                else:
                    dtp   = (cur - pos['take_profit']) / cur * 100
                    dsl   = (pos['stop_loss'] - cur)   / cur * 100
                    pnl_v = (pos['entry_price'] - cur) * pos['quantity']

                pnl_pct_pos = pnl_v / pos['usdt_size'] * 100
                wr          = pos.get('winrate', 0)
                usdt_size   = pos.get('usdt_size', 500)
                quantity    = pos.get('quantity', 0)

                L.append(
                    f'{dir_sym} {sym:<10} {usdt_size:>7.0f}$ {quantity:>12.6f} '
                    f'{pos["entry_price"]:>14.6f} {cur:>14.6f} '
                    f'{pos["take_profit"]:>14.6f} {pos["stop_loss"]:>14.6f} '
                    f'[{icon}]{pnl_v:>8.2f}$ {pnl_pct_pos:>6.2f}%  '
                    f'{wr:>4.1f}%  TP:{dtp:+.2f}%  SL:{dsl:+.2f}%'
                )
        else:
            L.append('  Açık pozisyon yok.')

        self._set(self.t_positions, '\n'.join(L))

    def update_signals(self):
        THR   = self.scanner.WINRATE_THRESHOLD
        SDIST = self.scanner.SUPPORT_MAX_DIST
        L = [
            'SİNYALLER + GERİ DÖNÜK BAŞARI + DESTEK/DİRENÇ ANALİZİ',
            f'BUY9  : WR > %{THR:.0f}  VE  Desteğe uzaklık <= %{SDIST:.0f}  → LONG aç',
            f'SELL9 : WR > %{THR:.0f}  VE  Dirençe uzaklık <= %{SDIST:.0f}  → SHORT aç',
            '='*130,
        ]

        def buy_block():
            sigs = self.scanner.buy_signals
            if not sigs: return
            rows = sorted(sigs.items(), key=lambda x: x[1].get('buy_winrate', 0), reverse=True)
            L.append(f'\nBUY SETUP 9  ({len(rows)} sinyal)')
            L.append(f'  {"Coin":<12} {"Fiyat":>16}  {"WR":>8}  {"K/T":>7}  {"USDT":>7}  {"Destek":>12}  {"Uzaklık":>8}  Durum')
            L.append('  ' + '-'*110)
            for coin, sig in rows:
                wr     = sig.get('buy_winrate', 0)
                tot    = sig.get('buy_total_signals', 0)
                wins   = sig.get('buy_wins', 0)
                passed = sig.get('buy_passed', False)
                wr_ok  = sig.get('buy_wr_ok', False)
                s_ok   = sig.get('support_ok', False)
                sdist  = sig.get('support_dist_pct', 0)
                supp   = sig.get('support_price', 0)
                tr     = sig.get('trade_result', None)

                wr_sym = '[**]' if wr >= 80 else ('[OK]' if wr >= THR else '[--]')
                d_sym  = '[OK]' if s_ok else '[--]'

                if not passed:
                    parts = []
                    if not wr_ok: parts.append(f'WR:{wr:.0f}%<{THR:.0f}%')
                    if not s_ok:
                        parts.append(f'DESTEK KIRILMIŞ({sdist:.1f}%)' if sdist < 0 else f'Dest uzak(+{sdist:.1f}%)')
                    durum = 'ATILDI (' + ', '.join(parts) + ')'
                elif tr == 'ACILDI':       durum = '✔ LONG AÇIK  [500 USDT]'
                elif tr and tr.startswith('HATA'): durum = f'✘ {tr[5:]}'
                elif tr == 'MAX_POS':      durum = '⚠ MAKS POZ'
                elif tr == 'LIMIT_ASIM':   durum = '⚠ LIMIT'
                else:                      durum = '⏳ bekleniyor'

                L.append(f'  {coin:<12} ${sig["price"]:>15.6f}  {wr_sym}{wr:>5.1f}%  '
                         f'{wins:>3}/{tot:<3}  {"500":>6}$  ${supp:>11.5f}  {d_sym}{sdist:>+6.1f}%  {durum}')

        def sell_block():
            sigs = self.scanner.sell_signals
            if not sigs: return
            rows = sorted(sigs.items(), key=lambda x: x[1].get('sell_winrate', 0), reverse=True)
            L.append(f'\nSELL SETUP 9  ({len(rows)} sinyal)')
            L.append(f'  {"Coin":<12} {"Fiyat":>16}  {"WR":>8}  {"K/T":>7}  {"USDT":>7}  {"Direnç":>12}  {"Uzaklık":>8}  Durum')
            L.append('  ' + '-'*110)
            for coin, sig in rows:
                wr     = sig.get('sell_winrate', 0)
                tot    = sig.get('sell_total_signals', 0)
                wins   = sig.get('sell_wins', 0)
                passed = sig.get('sell_passed', False)
                wr_ok  = sig.get('sell_wr_ok', False)
                r_ok   = sig.get('resistance_ok', False)
                rdist  = sig.get('resistance_dist_pct', 0)
                res    = sig.get('resistance_price', 0)
                tr     = sig.get('trade_result', None)

                wr_sym = '[**]' if wr >= 80 else ('[OK]' if wr >= THR else '[--]')
                d_sym  = '[OK]' if r_ok else '[--]'

                if not passed:
                    parts = []
                    if not wr_ok: parts.append(f'WR:{wr:.0f}%<{THR:.0f}%')
                    if not r_ok:
                        parts.append(f'DİRENÇ KIRILMIŞ({rdist:.1f}%)' if rdist < 0 else f'Direnc uzak(+{rdist:.1f}%)')
                    durum = 'ATILDI (' + ', '.join(parts) + ')'
                elif tr == 'SHORT_ACILDI': durum = '✔ SHORT AÇIK [500 USDT]'
                elif tr and tr.startswith('HATA'): durum = f'✘ {tr[5:]}'
                elif tr == 'MAX_POS':      durum = '⚠ MAKS POZ'
                elif tr == 'LIMIT_ASIM':   durum = '⚠ LIMIT'
                else:                      durum = '⏳ bekleniyor'

                L.append(f'  {coin:<12} ${sig["price"]:>15.6f}  {wr_sym}{wr:>5.1f}%  '
                         f'{wins:>3}/{tot:<3}  {"500":>6}$  ${res:>11.5f}  {d_sym}{rdist:>+6.1f}%  {durum}')

        buy_block()
        sell_block()

        if not self.scanner.buy_signals and not self.scanner.sell_signals:
            L.append('\nHenüz sinyal yok. Tarama bekleniyor...')

        self._set(self.t_signals, '\n'.join(L))

    def update_backtest(self):
        THR   = self.scanner.WINRATE_THRESHOLD
        SDIST = self.scanner.SUPPORT_MAX_DIST
        rows  = []
        for coin, sig in self.scanner.buy_signals.items():
            rows.append({'coin': coin, 'type': 'BUY',
                         'price': sig['price'], 'wr': sig.get('buy_winrate', 0),
                         'wins': sig.get('buy_wins', 0), 'total': sig.get('buy_total_signals', 0),
                         'passed': sig.get('buy_passed', False), 'wr_ok': sig.get('buy_wr_ok', False),
                         'lvl_ok': sig.get('support_ok', False), 'lvl': sig.get('support_price', 0),
                         'ldist': sig.get('support_dist_pct', 0), 'ltouches': sig.get('support_touches', 0),
                         'lvl_lbl': 'DESTEK', 'days': sig.get('days_back', 0)})
        for coin, sig in self.scanner.sell_signals.items():
            rows.append({'coin': coin, 'type': 'SELL',
                         'price': sig['price'], 'wr': sig.get('sell_winrate', 0),
                         'wins': sig.get('sell_wins', 0), 'total': sig.get('sell_total_signals', 0),
                         'passed': sig.get('sell_passed', False), 'wr_ok': sig.get('sell_wr_ok', False),
                         'lvl_ok': sig.get('resistance_ok', False), 'lvl': sig.get('resistance_price', 0),
                         'ldist': sig.get('resistance_dist_pct', 0), 'ltouches': sig.get('resistance_touches', 0),
                         'lvl_lbl': 'DİRENÇ', 'days': sig.get('days_back', 0)})
        rows.sort(key=lambda x: x['wr'], reverse=True)
        passed = sum(1 for r in rows if r['passed'])

        L = [
            'BACKTEST + DESTEK/DİRENÇ ANALİZİ',
            f'BUY9  → Desteğe uzaklık <= %{SDIST:.0f}  +  WR > %{THR:.0f}  →  LONG aç',
            f'SELL9 → Dirençe uzaklık <= %{SDIST:.0f}  +  WR > %{THR:.0f}  →  SHORT aç',
            f'Veri  : ~1000 mum (1H) = ~41 gün  |  TP:%20  SL:%5  İleri:20 bar',
            '='*145,
            f'  {"Coin":<12} {"Tip":<5} {"WR":>9}  {"K/T":>7}  {"Fiyat":>14}  '
            f'{"Sev.":<7} {"Seviye":>12}  {"Uzaklık":>8}  {"Test":>4}  {"Gün":>4}  Karar',
            '-'*145,
        ]
        for r in rows:
            wr_sym = '[**]' if r['wr'] >= 80 else ('[OK]' if r['wr'] >= THR else '[--]')
            d_sym  = '[OK]' if r['lvl_ok'] else '[--]'
            if r['passed']:
                karar = 'GEÇTI ✔ LONG AÇILDI' if r['type'] == 'BUY' else 'GEÇTI ✔ SHORT AÇILDI'
            else:
                parts = []
                if not r['wr_ok']:  parts.append(f'WR:{r["wr"]:.0f}%<{THR:.0f}%')
                if not r['lvl_ok']: parts.append(
                    f'{r["lvl_lbl"]} KIRILMIŞ({r["ldist"]:.1f}%)' if r['ldist'] < 0
                    else f'{r["lvl_lbl"]} UZAK(+{r["ldist"]:.1f}%)')
                karar = 'ATILDI (' + ', '.join(parts) + ')'
            L.append(
                f'  {r["coin"]:<12} {r["type"]:<5} {wr_sym}{r["wr"]:>6.1f}%  '
                f'{r["wins"]:>3}/{r["total"]:<3}  ${r["price"]:>13.6f}  '
                f'{r["lvl_lbl"]:<7} ${r["lvl"]:>11.5f}  {d_sym}{r["ldist"]:>+6.1f}%  '
                f'{r["ltouches"]:>3}x  {r["days"]:>3.0f}g  {karar}'
            )
        L += [
            '-'*145,
            f'  Toplam: {len(rows)}  |  Filtre geçen: {passed}  |  Atılan: {len(rows)-passed}',
            f'  Tarama #{self.scanner.scan_count}  -  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        ]
        if not rows:
            L.append('\n  Henüz backtest sonucu yok. Tarama bekleniyor...')
        self._set(self.t_backtest, '\n'.join(L))

    def update_closed(self):
        """DÜZELTME: usdt_size, süre ve net kâr/zarar tutarı eklendi."""
        trades = self.scanner.paper_trading.closed_trades
        L = [
            'KAPALI İŞLEMLER  (En son üstte)',
            '='*160,
            f'  {"Yön":<6} {"Coin":<10} {"USDT":>7} {"Giriş":>14} {"Çıkış":>14} '
            f'{"TP":>14} {"SL":>14} {"PnL $":>10} {"PnL %":>8} {"WR":>6}  {"Süre":>8}  Sebep',
            '-'*160,
        ]
        if trades:
            for t in reversed(trades[-60:]):   # en yeni üstte
                icon     = '[+]' if t['pnl'] > 0 else '[-]'
                wr       = t.get('winrate', 0)
                dir_sym  = 'LONG ' if t.get('direction', 'long') == 'long' else 'SHORT'
                usdt_sz  = t.get('usdt_size', 500)
                dur_sec  = t.get('duration_seconds', 0)
                if dur_sec < 60:
                    dur_str = f'{int(dur_sec)}sn'
                elif dur_sec < 3600:
                    dur_str = f'{int(dur_sec/60)}dk'
                else:
                    dur_str = f'{dur_sec/3600:.1f}sa'

                L.append(
                    f'  {dir_sym} {t["sembol"]:<10} {usdt_sz:>6.0f}$ '
                    f'{t["entry_price"]:>14.6f} {t["exit_price"]:>14.6f} '
                    f'{t["tp_level"]:>14.6f} {t["sl_level"]:>14.6f} '
                    f'{icon}{t["pnl"]:>8.2f}$ {t["pnl_percent"]:>7.2f}%  '
                    f'{wr:>4.1f}%  {dur_str:>7}  {t["reason"]}'
                )
        else:
            L.append('  Henüz kapalı işlem yok.')

        total_pnl = sum(t['pnl'] for t in trades)
        wins      = sum(1 for t in trades if t['pnl'] > 0)
        L += [
            '-'*160,
            f'  Toplam İşlem: {len(trades)}  |  Kârlı: {wins}  |  Zararlı: {len(trades)-wins}  |  '
            f'Net P&L: {total_pnl:+.2f} USDT',
        ]
        self._set(self.t_closed, '\n'.join(L))

    def update_stats(self):
        s  = self.scanner.paper_trading.get_stats()
        pt = self.scanner.paper_trading
        pv = pt.get_portfolio_value(self.scanner.current_prices)
        gain     = pv - pt.initial_balance
        gain_pct = gain / pt.initial_balance * 100

        # Coin bazlı kâr/zarar tablosu
        coin_stats = {}
        for t in pt.closed_trades:
            c = t['sembol']
            if c not in coin_stats:
                coin_stats[c] = {'pnl': 0, 'count': 0, 'wins': 0, 'usdt': 0}
            coin_stats[c]['pnl']   += t['pnl']
            coin_stats[c]['count'] += 1
            coin_stats[c]['usdt']  += t.get('usdt_size', 500)
            if t['pnl'] > 0:
                coin_stats[c]['wins'] += 1

        L = [
            'TRADE İSTATİSTİKLERİ',
            '='*70,
            f'Tarama         : #{self.scanner.scan_count}',
            f'Taranan Coin   : {len(self.scanner._valid_symbols) if self.scanner._valid_symbols else "-"}',
            f'Toplam Sinyal  : {self.scanner.total_signals}',
            f'WR Eşiği       : >= %{self.scanner.WINRATE_THRESHOLD:.0f}',
            '',
            f'Başlangıç      : {pt.initial_balance:>12,.2f} USDT',
            f'Güncel Portföy : {pv:>12,.2f} USDT',
            f'Toplam P&L     : {gain:>+12,.2f} USDT ({gain_pct:+.2f}%)',
            '',
            '--- İşlem Özeti ---',
            f'Toplam  : {s["toplam_islem"]}',
            f'Başarılı: {s["basarili_islem"]}',
            f'Zarar   : {s["basarisiz_islem"]}',
            f'Win Rate: {s["win_rate"]:.1f}%',
            f'Ort Kaz : {s["ort_kazanc"]:+.2f}%',
            f'Kâr Fak : {s["kazanc_faktoru"]:.2f}',
        ]

        # COİN BAZLI TABLO
        if coin_stats:
            L.append('')
            L.append('--- Coin Bazlı Kâr/Zarar ---')
            L.append(f'  {"Coin":<12} {"İşlem":>6}  {"USDT Toplam":>12}  {"Net Kâr $":>10}  {"WR%":>6}')
            L.append('  ' + '-'*55)
            for coin, cs in sorted(coin_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
                wr_c = cs['wins'] / cs['count'] * 100 if cs['count'] > 0 else 0
                icon = '+' if cs['pnl'] >= 0 else '-'
                L.append(
                    f'  {coin:<12} {cs["count"]:>6}  {cs["usdt"]:>11.0f}$  '
                    f'[{icon}]{cs["pnl"]:>8.2f}$  {wr_c:>5.1f}%'
                )

        if s['toplam_islem'] > 0:
            L.append('')
            L.append('--- Son 15 İşlem ---')
            for t in reversed(pt.closed_trades[-15:]):
                icon    = '[+]' if t['pnl'] > 0 else '[-]'
                dir_sym = 'L' if t.get('direction', 'long') == 'long' else 'S'
                usdt_sz = t.get('usdt_size', 500)
                L.append(
                    f'{icon} {dir_sym} {t["sembol"]:<12} {usdt_sz:.0f}$ → '
                    f'{t["pnl_percent"]:+7.2f}%  ({t["pnl"]:+.2f}$)  '
                    f'WR:{t.get("winrate",0):.0f}%  {t["reason"]}'
                )
        self._set(self.t_stats, '\n'.join(L))

    # ── Queue Döngüsü ──────────────────────────────────────────────
    def check_queue(self):
        refresh_all    = False
        refresh_closed = False
        try:
            while True:
                mtype, mdata = self.scanner.update_queue.get_nowait()
                if mtype == 'status':
                    self.status_label.config(text=str(mdata)[:60])
                    self.add_log(str(mdata))
                elif mtype == 'progress':
                    self.progress_var.set(mdata)
                elif mtype == 'countdown':
                    self.countdown_label.config(text=str(mdata))
                elif mtype == 'log':
                    self.add_log(str(mdata))
                elif mtype == 'coin_log':
                    self.add_coin_log(str(mdata))
                elif mtype == 'complete':
                    d = mdata
                    self.add_log(
                        f'Tarama #{d["scan_count"]} BİTTİ  '
                        f'BUY9:{d["buy_count"]}  SELL9:{d["sell_count"]}  '
                        f'Kaliteli:{d["qualified_buy"]}  Açılan:{d["opened"]}')
                    self.progress_var.set(100)
                    if self.scanner._valid_symbols:
                        self.coin_count_label.config(text=f'Coin: {len(self.scanner._valid_symbols)}')
                elif mtype == 'refresh_all':
                    # ── DÜZELTME: Tarama bitti, TÜM sekmeleri güncelle ──
                    refresh_all = True
                elif mtype == 'refresh_closed':
                    refresh_closed = True
        except Exception:
            pass

        # Pozisyon her saniye güncellenir
        self.update_positions()

        # Diğer sekmeler tarama sinyaliyle VEYA 5 sn geçince güncellenir
        now = time.time()
        if refresh_all or not hasattr(self, '_last_tab_update') or now - self._last_tab_update >= 5:
            self.update_signals()
            self.update_backtest()
            self.update_closed()
            self.update_stats()
            self._last_tab_update = now
        elif refresh_closed:
            self.update_closed()
            self.update_stats()

        self.root.after(1000, self.check_queue)

    def update_loop(self):
        self.check_queue()


# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    try:
        import ccxt, pandas  # noqa
    except ImportError:
        import tkinter.messagebox as mb
        r = tk.Tk(); r.withdraw()
        mb.showerror('Eksik Kütüphane', 'pip install ccxt pandas')
        r.destroy(); exit(1)

    root = tk.Tk()
    AdvancedScannerGUI(root)
    root.mainloop()