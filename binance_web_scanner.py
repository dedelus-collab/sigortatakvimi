"""
BINANCE TD9 SCANNER — Web Arayüzü (DüüÜZELTİLMİŞ)
Çalıştır: python binance_web_scanner.py
Tarayıcı: http://localhost:5050

DÜZELTMELER:
1. HEMEN TARA: force_scan bayrağı ile anında çalışır, tarama sırasında tıklanırsa
   mevcut tarama biter bitmez yeni tarama başlar.
2. Backtest sekmesi: her tarama sonrası doğru veri gönderilir (buy+sell ayrı satır).
3. Kapalı İşlemler sekmesi: kapanma anında anlık güncellenir, usdt_size gösterilir.
4. Pozisyonlar + Kapalı İşlemler: kaç USDT'lik alındığı (Boyut) sütunu eklendi.
"""

import threading, time, json, queue, webbrowser
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, Response, render_template_string, request

try:
    import ccxt, pandas as pd
    DEPS_OK = True
except ImportError:
    DEPS_OK = False

# ============================================================================
# PAPER TRADING
# ============================================================================
class PaperTrading:
    def __init__(self, balance=50000):
        self.balance   = balance
        self.initial   = balance
        self.positions = {}
        self.closed    = []
        self._lock     = threading.Lock()

    def open_trade(self, sym, price, size=500, winrate=0, direction='long'):
        with self._lock:
            key = f"{sym}_{direction}"
            if key in self.positions and self.positions[key]['status'] == 'open':
                return False, f"Zaten açık {direction}"
            if self.balance < size:
                return False, f"Bakiye yetersiz ({self.balance:.0f})"
            qty = size / price
            tp  = price * 1.20 if direction == 'long' else price * 0.80
            sl  = price * 0.95 if direction == 'long' else price * 1.05
            self.positions[key] = {
                'sym': sym, 'direction': direction,
                'entry': price, 'qty': qty, 'size': size,
                'tp': tp, 'sl': sl,
                'cur': price, 'pnl': 0.0, 'pnl_pct': 0.0,
                'winrate': winrate, 'status': 'open',
                'time': datetime.now().strftime('%H:%M:%S')
            }
            self.balance -= size
            dir_label = 'LONG' if direction == 'long' else 'SHORT'
            return True, f"{dir_label} {sym} @ {price:.6f} [{size:.0f} USDT | WR:{winrate:.1f}%]"

    def update_price(self, sym, price):
        closed = []
        for d in ('long', 'short'):
            key = f"{sym}_{d}"
            with self._lock:
                if key not in self.positions or self.positions[key]['status'] != 'open':
                    continue
                p = self.positions[key]
                p['cur'] = price
                pnl = (price - p['entry']) * p['qty'] if d == 'long' else (p['entry'] - price) * p['qty']
                p['pnl']     = pnl
                p['pnl_pct'] = pnl / p['size'] * 100
                reason = None
                if d == 'long':
                    if price <= p['sl']:  reason = 'STOP LOSS'
                    elif price >= p['tp']: reason = 'TAKE PROFIT'
                else:
                    if price >= p['sl']:  reason = 'STOP LOSS'
                    elif price <= p['tp']: reason = 'TAKE PROFIT'
                if reason:
                    ev = price * p['qty'] if d == 'long' else p['size'] + pnl
                    self.balance += max(ev, 0)
                    p['status'] = 'closed'
                    rec = {**p, 'exit': price, 'reason': reason,
                           'close_time': datetime.now().strftime('%H:%M:%S')}
                    self.closed.append(rec)
                    closed.append(rec)
        return closed

    def portfolio_value(self, prices):
        total = self.balance
        for key, p in self.positions.items():
            if p['status'] != 'open': continue
            pr = prices.get(p['sym'], p['entry'])
            if p['direction'] == 'long':
                total += p['qty'] * pr
            else:
                total += p['size'] + (p['entry'] - pr) * p['qty']
        return total

    def stats(self):
        if not self.closed:
            return {'total': 0, 'wins': 0, 'losses': 0, 'wr': 0, 'pnl': 0, 'kf': 0}
        wins     = [t for t in self.closed if t['pnl'] > 0]
        losses   = [t for t in self.closed if t['pnl'] <= 0]
        win_pnl  = sum(t['pnl'] for t in wins)
        loss_pnl = sum(abs(t['pnl']) for t in losses)
        return {
            'total':   len(self.closed),
            'wins':    len(wins),
            'losses':  len(losses),
            'wr':      len(wins) / len(self.closed) * 100,
            'pnl':     sum(t['pnl'] for t in self.closed),
            'kf':      win_pnl / loss_pnl if loss_pnl else 0,
        }

# ============================================================================
# SCANNER
# ============================================================================
class Scanner:
    WR_THRESH  = 50.0
    SUPP_MAX   = 5.0
    SCAN_EVERY = 30 * 60
    TRADE_SIZE = 500
    MAX_POS    = 15
    MAX_NEW    = 5

    def __init__(self):
        self.pt          = PaperTrading()
        self.exchange    = None
        self.symbols     = None
        self.buy_sigs    = {}
        self.sell_sigs   = {}
        self.all_results = []
        self.prices      = {}
        self.is_scanning = False
        self.is_running  = False
        self.force_scan  = False          # ← YENİ: HEMEN TARA bayrağı
        self._scan_lock  = threading.Lock()
        self.scan_count  = 0
        self.last_scan   = 0
        self.logs        = []
        self.scan_logs   = []
        self.clients     = []
        self._lock       = threading.Lock()

    # ─── SSE ─────────────────────────────────────────────────────────
    def push(self, event, data):
        msg = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        with self._lock:
            dead = []
            for q in self.clients:
                try:    q.put_nowait(msg)
                except: dead.append(q)
            for q in dead: self.clients.remove(q)

    def add_log(self, msg, kind='normal'):
        entry = {'t': datetime.now().strftime('%H:%M:%S'), 'msg': msg, 'kind': kind}
        self.logs = self.logs[-500:]
        self.logs.append(entry)
        self.push('log', entry)

    def add_scan_log(self, msg, kind='normal'):
        entry = {'t': datetime.now().strftime('%H:%M:%S'), 'msg': msg, 'kind': kind}
        self.scan_logs = self.scan_logs[-2000:]
        self.scan_logs.append(entry)
        self.push('scanlog', entry)

    # ─── Bağlantı ────────────────────────────────────────────────────
    def connect(self):
        try:
            self.exchange = ccxt.binance({'enableRateLimit': True})
            self.push('status', {'text': 'Binance bağlandı', 'scanning': False})
            return True
        except Exception as e:
            self.add_log(f'Bağlantı hatası: {e}', 'err')
            return False

    def get_symbols(self):
        if self.symbols: return self.symbols
        try:
            self.push('status', {'text': 'Semboller yükleniyor...', 'scanning': True})
            mkts  = self.exchange.load_markets()
            pairs = [s for s, m in mkts.items()
                     if s.endswith('/USDT') and m.get('spot') and m.get('active')
                     and m.get('type', '') not in ('future', 'swap')]
            try:
                tickers = self.exchange.fetch_tickers()
                pairs.sort(key=lambda s: tickers.get(s, {}).get('quoteVolume') or 0, reverse=True)
            except: pass
            self.symbols = pairs[:500]
            return self.symbols
        except Exception as e:
            self.add_log(f'Sembol hatası: {e}', 'err')
            return self._fallback()

    def _fallback(self):
        return ["BTC/USDT","ETH/USDT","BNB/USDT","XRP/USDT","SOL/USDT","ADA/USDT",
                "DOGE/USDT","DOT/USDT","LINK/USDT","LTC/USDT","TRX/USDT","BCH/USDT",
                "XLM/USDT","AVAX/USDT","ATOM/USDT","UNI/USDT","AAVE/USDT","MATIC/USDT",
                "NEAR/USDT","ARB/USDT","OP/USDT","SUI/USDT","INJ/USDT","TON/USDT",
                "PEPE/USDT","BONK/USDT","WIF/USDT","SHIB/USDT","FLOKI/USDT","TIA/USDT",
                "HBAR/USDT","FET/USDT","RENDER/USDT","TAO/USDT","ENA/USDT","WLD/USDT"]

    # ─── Algoritma ───────────────────────────────────────────────────
    def heiken_ashi(self, df):
        ha_c = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        ha_o = [(df['open'].iloc[0] + df['close'].iloc[0]) / 2]
        for i in range(1, len(df)):
            ha_o.append((ha_o[-1] + ha_c.iloc[i - 1]) / 2)
        df = df.copy()
        df['ha_c'] = ha_c.values
        df['ha_o'] = ha_o
        return df

    def td_sequential(self, df):
        df  = self.heiken_ashi(df)
        ha  = df['ha_c'].values
        n   = len(ha)
        buy = [0] * n
        sell= [0] * n
        bc = sc = 0
        for i in range(n):
            bc = min(bc + 1, 9) if i >= 4 and ha[i] < ha[i - 4] else 0
            sc = min(sc + 1, 9) if i >= 4 and ha[i] > ha[i - 4] else 0
            buy[i] = bc; sell[i] = sc
        df['buy9']  = buy
        df['sell9'] = sell
        return df

    def backtest(self, df, sig_type, tp=0.20, sl=0.05, fwd=20):
        col    = 'buy9' if sig_type == 'buy' else 'sell9'
        closes = df['close'].values
        highs  = df['high'].values
        lows   = df['low'].values
        setups = df[col].values
        n      = len(df)
        total = wins = 0
        for i in range(4, n - fwd - 1):
            if int(setups[i]) != 9: continue
            entry = closes[i]
            if entry <= 0: continue
            tp_p = entry * (1 + tp) if sig_type == 'buy' else entry * (1 - tp)
            sl_p = entry * (1 - sl) if sig_type == 'buy' else entry * (1 + sl)
            total += 1; outcome = None
            for j in range(i + 1, min(i + fwd + 1, n)):
                h, l = highs[j], lows[j]
                if sig_type == 'buy':
                    if h >= tp_p: outcome = 'win';  break
                    if l <= sl_p: outcome = 'loss'; break
                else:
                    if l <= tp_p: outcome = 'win';  break
                    if h >= sl_p: outcome = 'loss'; break
            if outcome == 'win': wins += 1
            elif outcome is None:
                fin = closes[min(i + fwd, n - 1)]
                if sig_type == 'buy'  and fin > entry: wins += 1
                if sig_type == 'sell' and fin < entry: wins += 1
        return float(wins / total * 100 if total else 0.0), int(total), int(wins)

    def find_support(self, df, lb=100, tol=0.015):
        lows = df['low'].values[-lb:]
        n    = len(lows)
        pivs = [lows[i] for i in range(2, n - 2)
                if lows[i] < lows[i-1] and lows[i] < lows[i-2]
                and lows[i] < lows[i+1] and lows[i] < lows[i+2]]
        if not pivs:
            sup = float(min(lows)); tc = 1
        else:
            best = pivs[0]; btc = 1
            for ref in pivs:
                tc = sum(1 for l in pivs if abs(l - ref) / ref <= tol)
                if tc > btc: btc = tc; best = ref
            sup = best; tc = btc
        price = float(df['close'].iloc[-1])
        return float(sup), int(tc), float((price - sup) / sup * 100)

    def find_resistance(self, df, lb=100, tol=0.015):
        highs = df['high'].values[-lb:]
        n     = len(highs)
        pivs  = [highs[i] for i in range(2, n - 2)
                 if highs[i] > highs[i-1] and highs[i] > highs[i-2]
                 and highs[i] > highs[i+1] and highs[i] > highs[i+2]]
        if not pivs:
            res = float(max(highs)); tc = 1
        else:
            best = pivs[0]; btc = 1
            for ref in pivs:
                tc = sum(1 for h in pivs if abs(h - ref) / ref <= tol)
                if tc > btc: btc = tc; best = ref
            res = best; tc = btc
        price = float(df['close'].iloc[-1])
        return float(res), int(tc), float((res - price) / price * 100)

    def scan_one(self, symbol):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=1000)
            if not ohlcv or len(ohlcv) < 50: return None
            df = pd.DataFrame(ohlcv, columns=['timestamp','open','high','low','close','volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = self.td_sequential(df)

            price   = float(df['close'].iloc[-1])
            buy9    = int(df['buy9'].iloc[-1])
            sell9   = int(df['sell9'].iloc[-1])
            ha_bull = float(df['ha_c'].iloc[-1]) > float(df['ha_o'].iloc[-1])

            bwr = btot = bwins = swr = stot = swins = 0
            if buy9  == 9: bwr, btot, bwins = self.backtest(df, 'buy')
            if sell9 == 9: swr, stot, swins = self.backtest(df, 'sell')

            sup,  stc,  sdist = self.find_support(df)
            res,  rtc,  rdist = self.find_resistance(df)

            bwr_ok  = bool(bwr  >= self.WR_THRESH)
            swr_ok  = bool(swr  >= self.WR_THRESH)
            supp_ok = bool(0.0 < sdist <= self.SUPP_MAX)
            res_ok  = bool(0.0 < rdist <= self.SUPP_MAX)

            return {
                'sym': symbol.split('/')[0], 'full': symbol,
                'price': float(price), 'ha_bull': bool(ha_bull),
                'buy9': int(buy9),   'sell9': int(sell9),
                'bwr': float(bwr),   'btot': int(btot),  'bwins': int(bwins), 'bwr_ok': bwr_ok,
                'swr': float(swr),   'stot': int(stot),  'swins': int(swins), 'swr_ok': swr_ok,
                'sup': float(sup),   'stc': int(stc),    'sdist': float(sdist), 'supp_ok': supp_ok,
                'res': float(res),   'rtc': int(rtc),    'rdist': float(rdist), 'res_ok': res_ok,
                'buy_passed':  bool(buy9 == 9 and bwr_ok and supp_ok),
                'sell_passed': bool(sell9 == 9 and swr_ok and res_ok),
                'days': float(round(len(df) / 24, 1)),
            }
        except: return None

    # ─── Fiyat & TP/SL ───────────────────────────────────────────────
    def fetch_live_prices(self):
        syms = set(p['sym'] for p in self.pt.positions.values() if p['status'] == 'open')
        if not syms or not self.exchange: return
        for sym in syms:
            try:
                t = self.exchange.fetch_ticker(f"{sym}/USDT")
                self.prices[sym] = float(t['last'])
            except: pass

    def check_tpsl(self):
        syms = set(p['sym'] for p in self.pt.positions.values() if p['status'] == 'open')
        any_closed = False
        for sym in syms:
            if sym not in self.prices: continue
            closed = self.pt.update_price(sym, self.prices[sym])
            for c in closed:
                any_closed = True
                icon = '💰' if c['pnl'] > 0 else '🔴'
                dir_l = c['direction'].upper()
                self.add_log(
                    f"{icon} {dir_l} KAPANDI: {c['sym']} | {c['reason']} | "
                    f"{c['pnl_pct']:+.2f}% | {c['size']:.0f} USDT",
                    'signal' if c['pnl'] > 0 else 'short')
        self.push('positions', self.positions_data())
        # ── DÜZELTME: kapanma varsa kapalı işlemler de hemen güncellenir ──
        if any_closed:
            self.push('stats',  self.stats_data())
            self.push('closed', self.closed_data())

    # ─── Ana tarama ──────────────────────────────────────────────────
    def run_scan(self):
        """Lock ile çift tarama önlenir."""
        if not self._scan_lock.acquire(blocking=False):
            self.add_log('Tarama zaten çalışıyor, atlandı.', 'err')
            return
        try:
            self._do_scan()
        except Exception as e:
            self.add_log(f'Tarama hatası: {e}', 'err')
            # Hata durumunda da last_scan güncelle — aksi halde döngü hemen tekrar başlatır
            if self.last_scan == 0:
                self.last_scan = time.time()
        finally:
            # Her durumda bayrakları sıfırla — aksi halde döngü takılır
            self.is_scanning = False
            self.force_scan  = False
            self._scan_lock.release()
            self.push('status', {'text': 'Sistem hazır — sonraki tarama bekleniyor', 'scanning': False})

    def _do_scan(self):
        # is_scanning=True zaten run_loop'ta thread başlamadan set edildi
        # force_scan sıfırla
        self.scan_count += 1
        self.buy_sigs.clear()
        self.sell_sigs.clear()
        self.all_results = []
        sc = self.scan_count

        self.push('status', {'text': f'Tarama #{sc} başladı...', 'scanning': True})
        self.add_scan_log('=' * 60, 'header')
        self.add_scan_log(f'TARAMA #{sc}  —  {datetime.now().strftime("%H:%M:%S")}', 'header')

        symbols = self.get_symbols()
        total   = len(symbols)
        done    = failed = 0

        with ThreadPoolExecutor(max_workers=15) as ex:
            futs = {ex.submit(self.scan_one, s): s for s in symbols}
            for fut in as_completed(futs):
                sym = futs[fut]
                done += 1
                try:
                    r = fut.result(timeout=20)
                    if r:
                        self.prices[r['sym']] = r['price']
                        tags = []

                        if r['buy9'] == 9:
                            self.buy_sigs[r['sym']] = r
                            self.all_results.append({**r, '_row_type': 'BUY'})
                            wr_s    = f"WR:{r['bwr']:.0f}% ({r['bwins']}/{r['btot']})"
                            d_s     = f"DEST:{r['sdist']:+.1f}%"
                            verdict = 'LONG✓' if r['buy_passed'] else ('WR↓' if not r['bwr_ok'] else 'DEST↑')
                            tags.append(f"BUY9 {wr_s} {d_s} [{verdict}]")

                        if r['sell9'] == 9:
                            self.sell_sigs[r['sym']] = r
                            self.all_results.append({**r, '_row_type': 'SELL'})
                            wr_s    = f"WR:{r['swr']:.0f}% ({r['swins']}/{r['stot']})"
                            d_s     = f"RES:{r['rdist']:+.1f}%"
                            verdict = 'SHORT✓' if r['sell_passed'] else ('WR↓' if not r['swr_ok'] else 'RES↑')
                            tags.append(f"SELL9 {wr_s} {d_s} [{verdict}]")

                        kind    = 'signal' if any('✓' in t for t in tags) else \
                                  'short'  if tags else 'normal'
                        tag_str = '  '.join(tags) if tags else ''
                        ha      = '▲' if r['ha_bull'] else '▽'
                        self.add_scan_log(
                            f"[{done:>3}/{total}] {r['sym']:<10} ${r['price']:>14.6f}  {ha}  {tag_str}", kind)
                    else:
                        failed += 1
                        self.add_scan_log(f"[{done:>3}/{total}] {sym.split('/')[0]:<10} -- VERİ YOK", 'err')
                except Exception as e:
                    failed += 1
                    self.add_scan_log(f"[{done:>3}/{total}] {sym.split('/')[0]:<10} -- HATA", 'err')

                if done % 25 == 0:
                    self.push('progress', {'pct': done / total * 100})
                    self.push('status', {
                        'text': f'{done}/{total} tarandı | B:{len(self.buy_sigs)} S:{len(self.sell_sigs)}',
                        'scanning': True})
                    # ── Tarama sırasında da backtest + sinyal sekmesini güncelle ──
                    if self.all_results:
                        self.push('backtest', self.backtest_data())
                        self.push('signals',  self.signals_data())

        # Kaliteli sinyaller
        q_buys  = sorted([r for r in self.buy_sigs.values()  if r['buy_passed']],
                         key=lambda x: x['bwr'], reverse=True)
        q_sells = sorted([r for r in self.sell_sigs.values() if r['sell_passed']],
                         key=lambda x: x['swr'], reverse=True)

        self.add_scan_log('=' * 60, 'header')
        self.add_scan_log(f'TAMAMLANDI #{sc} | Başarılı:{done-failed}/{total} | Hata:{failed}', 'header')
        self.add_scan_log(f'BUY9:{len(self.buy_sigs)} → LONG açılacak:{len(q_buys)}', 'header')
        self.add_scan_log(f'SELL9:{len(self.sell_sigs)} → SHORT açılacak:{len(q_sells)}', 'header')

        # İşlem aç
        opened = 0
        for r in q_buys[:self.MAX_NEW]:
            oc = sum(1 for p in self.pt.positions.values() if p['status'] == 'open')
            if oc >= self.MAX_POS: break
            ok, msg = self.pt.open_trade(r['sym'], r['price'], self.TRADE_SIZE, r['bwr'], 'long')
            r['trade_result'] = 'LONG_OK' if ok else f'ERR:{msg}'
            self.add_log(f"{'✅ LONG AÇILDI' if ok else '❌ AÇILAMADI'}: {msg}",
                         'signal' if ok else 'err')
            if ok: opened += 1

        for r in q_sells[:self.MAX_NEW]:
            oc = sum(1 for p in self.pt.positions.values() if p['status'] == 'open')
            if oc >= self.MAX_POS: break
            ok, msg = self.pt.open_trade(r['sym'], r['price'], self.TRADE_SIZE, r['swr'], 'short')
            r['trade_result'] = 'SHORT_OK' if ok else f'ERR:{msg}'
            self.add_log(f"{'✅ SHORT AÇILDI' if ok else '❌ AÇILAMADI'}: {msg}",
                         'short' if ok else 'err')
            if ok: opened += 1

        # ── DÜZELTME: Tüm sekmelere veri gönder ──
        self.push('signals',   self.signals_data())
        self.push('backtest',  self.backtest_data())
        self.push('positions', self.positions_data())
        self.push('stats',     self.stats_data())
        self.push('closed',    self.closed_data())
        self.push('progress',  {'pct': 100})
        self.push('status',    {'text': f'Tarama #{sc} bitti | {opened} işlem açıldı', 'scanning': False})
        self.last_scan   = time.time()
        # is_scanning=False ve force_scan=False -> run_scan finally bloğu halleder

    # ─── Data helpers ────────────────────────────────────────────────
    def backtest_data(self):
        """Her satır bağımsız: bir coin'in BUY ve SELL sinyalleri ayrı satır."""
        return {'results': self.all_results}

    def signals_data(self):
        buys  = sorted(self.buy_sigs.values(),  key=lambda x: x['bwr'], reverse=True)
        sells = sorted(self.sell_sigs.values(), key=lambda x: x['swr'], reverse=True)
        return {'buys': list(buys), 'sells': list(sells)}

    def positions_data(self):
        rows = []
        for key, p in self.pt.positions.items():
            if p['status'] != 'open': continue
            price = self.prices.get(p['sym'], p['entry'])
            if p['direction'] == 'long':
                pnl = (price - p['entry']) * p['qty']
                dtp = (p['tp'] - price) / price * 100
                dsl = (price - p['sl'])  / price * 100
            else:
                pnl = (p['entry'] - price) * p['qty']
                dtp = (price - p['tp']) / price * 100
                dsl = (p['sl'] - price) / price * 100
            pnl_pct = pnl / p['size'] * 100
            rows.append({**p, 'cur': price, 'pnl': pnl, 'pnl_pct': pnl_pct,
                         'dtp': dtp, 'dsl': dsl})
        return {'positions': rows, 'balance': self.pt.balance,
                'portfolio': self.pt.portfolio_value(self.prices),
                'initial': self.pt.initial}

    def closed_data(self):
        """Son 100 kapalı işlem, en yeni başta."""
        return {'closed': list(reversed(self.pt.closed[-100:]))}

    def stats_data(self):
        s = self.pt.stats()
        return {**s, 'balance': self.pt.balance, 'initial': self.pt.initial,
                'portfolio': self.pt.portfolio_value(self.prices),
                'closed': list(reversed(self.pt.closed[-30:]))}

    # ─── Sürekli döngü ───────────────────────────────────────────────
    def run_loop(self):
        self.is_running = True
        last_price = 0
        while self.is_running:
            try:
                now = time.time()

                # Canlı fiyat (her 30s)
                if now - last_price >= 30:
                    try:
                        self.fetch_live_prices()
                        self.check_tpsl()
                    except Exception as e:
                        self.add_log(f'Fiyat güncelleme hatası: {e}', 'err')
                    last_price = now

                # Geri sayım
                if self.last_scan > 0 and not self.is_scanning:
                    try:
                        rem  = max(0, self.SCAN_EVERY - (now - self.last_scan))
                        m, s = int(rem // 60), int(rem % 60)
                        self.push('countdown', {
                            'text': f'Sonraki tarama: {m:02d}:{s:02d}',
                            'interval': self.SCAN_EVERY // 60,
                            'scan': self.scan_count
                        })
                    except Exception:
                        pass

                # Tarama zamanlaması
                elapsed      = now - self.last_scan if self.last_scan > 0 else self.SCAN_EVERY + 1
                time_is_up   = elapsed >= self.SCAN_EVERY
                should_scan  = (not self.is_scanning and
                                (self.force_scan or self.last_scan == 0 or time_is_up))

                if should_scan:
                    self.is_scanning = True  # thread başlamadan önce işaretle
                    t = threading.Thread(target=self.run_scan, daemon=True)
                    t.start()

            except Exception as e:
                # Döngü hiçbir zaman ölmemeli — hataları yut ve devam et
                try:
                    self.add_log(f'run_loop hatası (devam ediliyor): {e}', 'err')
                except Exception:
                    pass

            time.sleep(5)

    def start(self):
        if not DEPS_OK:  return False
        if not self.connect(): return False
        threading.Thread(target=self.run_loop, daemon=True).start()
        return True

    def set_interval(self, minutes):
        self.SCAN_EVERY = max(5, min(120, int(minutes))) * 60

    def set_wr(self, val):
        self.WR_THRESH = max(0, min(100, float(val)))

    def set_dist(self, val):
        self.SUPP_MAX = max(1, min(20, float(val)))

# ============================================================================
# HTML
# ============================================================================
HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TD9 SCANNER</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Rajdhani:wght@400;600;700&display=swap');
:root{
  --bg:#060609;--bg2:#0c0c14;--bg3:#101018;
  --border:#1c1c30;--border2:#242438;
  --accent:#00e87a;--red:#ff2d55;--yellow:#ffcc00;--blue:#2196f3;--purple:#9c27b0;
  --text:#c0c8d8;--dim:#4a5068;
  --mono:'JetBrains Mono',monospace;--sans:'Rajdhani',sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden}
body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14px;display:flex;flex-direction:column}
body::before{content:'';position:fixed;inset:0;
  background-image:linear-gradient(rgba(0,232,122,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,232,122,.025) 1px,transparent 1px);
  background-size:32px 32px;pointer-events:none;z-index:0}
header{display:flex;align-items:center;gap:12px;padding:8px 18px;
  border-bottom:1px solid var(--border);background:rgba(6,6,9,.97);
  flex-shrink:0;z-index:10;position:relative}
.logo{font-family:var(--mono);font-size:16px;color:var(--accent);letter-spacing:2px;
  text-shadow:0 0 15px rgba(0,232,122,.4)}
.logo small{display:block;color:var(--dim);font-size:9px;letter-spacing:1px;margin-top:-2px}
.hstats{display:flex;gap:16px;margin:0 8px}
.hstat{text-align:center}
.hstat-v{font-family:var(--mono);font-size:14px;font-weight:700}
.hstat-l{font-size:9px;color:var(--dim);text-transform:uppercase;letter-spacing:1px}
.g{color:var(--accent)}.r{color:var(--red)}.y{color:var(--yellow)}.b{color:var(--blue)}.dim{color:var(--dim)}
.hcontrols{display:flex;gap:8px;align-items:center;margin-left:auto}
.cfg{display:flex;align-items:center;gap:5px}
.cfg label{font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}
.cfg input{width:48px;background:var(--bg3);border:1px solid var(--border2);color:var(--accent);
  font-family:var(--mono);font-size:12px;padding:4px 6px;border-radius:3px;text-align:center}
#countdown{font-family:var(--mono);font-size:11px;color:var(--yellow);
  padding:4px 10px;border:1px solid rgba(255,204,0,.2);border-radius:3px;
  background:rgba(255,204,0,.04);min-width:150px;text-align:center}
button{font-family:var(--sans);font-weight:700;font-size:12px;
  padding:6px 14px;border:none;border-radius:3px;cursor:pointer;
  transition:all .15s;text-transform:uppercase;letter-spacing:.5px}
.b-green{background:var(--accent);color:#000}
.b-green:hover{background:#00ffaa;box-shadow:0 0 16px rgba(0,232,122,.4)}
.b-red{background:var(--red);color:#fff}
.b-red:hover{box-shadow:0 0 16px rgba(255,45,85,.4)}
.b-blue{background:var(--blue);color:#fff}
.b-blue:hover{box-shadow:0 0 16px rgba(33,150,243,.4)}
.b-dim{background:var(--border2);color:var(--dim)}
.b-dim:hover{color:var(--text);background:#2a2a42}
button:disabled{opacity:.35;cursor:not-allowed;box-shadow:none!important}
#pbar{height:2px;background:var(--border);flex-shrink:0;z-index:10;position:relative}
#pfill{height:100%;width:0%;background:var(--accent);transition:width .4s;box-shadow:0 0 8px rgba(0,232,122,.5)}
#sbar{padding:3px 18px;font-family:var(--mono);font-size:10px;color:var(--dim);
  background:var(--bg2);border-bottom:1px solid var(--border);flex-shrink:0;z-index:9;position:relative}
.tabs{display:flex;gap:1px;padding:8px 18px 0;
  background:var(--bg2);border-bottom:1px solid var(--border);flex-shrink:0;z-index:9;position:relative}
.tab{font-weight:700;font-size:11px;padding:7px 14px;cursor:pointer;
  border-radius:3px 3px 0 0;letter-spacing:.5px;text-transform:uppercase;color:var(--dim);
  border:1px solid transparent;border-bottom:none;transition:all .15s;font-family:var(--sans)}
.tab:hover{color:var(--text)}
.tab.on{color:var(--accent);background:var(--bg);border-color:var(--border);text-shadow:0 0 8px rgba(0,232,122,.3)}
.tbadge{display:inline-block;background:var(--red);color:#fff;font-size:9px;
  padding:1px 5px;border-radius:10px;margin-left:4px;font-family:var(--mono);vertical-align:middle}
#content{flex:1;overflow:hidden;position:relative;z-index:1}
.panel{display:none;height:100%;overflow:auto;padding:14px 18px;flex-direction:column;gap:10px}
.panel.on{display:flex}
.tbl-wrap{border:1px solid var(--border);border-radius:4px;overflow:hidden;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:11px;min-width:600px}
thead th{padding:7px 10px;text-align:left;font-family:var(--sans);font-size:9px;font-weight:700;
  letter-spacing:1px;text-transform:uppercase;color:var(--dim);
  background:var(--bg2);border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:2;white-space:nowrap}
tbody tr{border-bottom:1px solid rgba(28,28,48,.6);transition:background .1s}
tbody tr:hover{background:rgba(0,232,122,.03)}
td{padding:6px 10px;white-space:nowrap}
.badge{display:inline-block;padding:2px 6px;border-radius:2px;
  font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.5px}
.bg{background:rgba(0,232,122,.12);color:var(--accent);border:1px solid rgba(0,232,122,.25)}
.br{background:rgba(255,45,85,.12);color:var(--red);border:1px solid rgba(255,45,85,.25)}
.by{background:rgba(255,204,0,.12);color:var(--yellow);border:1px solid rgba(255,204,0,.25)}
.bb{background:rgba(33,150,243,.12);color:var(--blue);border:1px solid rgba(33,150,243,.25)}
.bd{background:rgba(74,80,104,.1);color:var(--dim);border:1px solid rgba(74,80,104,.2)}
.pfbar{display:flex;gap:24px;padding:10px 16px;background:var(--bg2);
  border:1px solid var(--border);border-radius:4px;flex-wrap:wrap;flex-shrink:0}
.pfitem{display:flex;flex-direction:column;gap:1px}
.pfval{font-family:var(--mono);font-size:15px;font-weight:700}
.pflbl{font-size:9px;color:var(--dim);text-transform:uppercase;letter-spacing:1px}
.logbox{flex:1;background:var(--bg3);border:1px solid var(--border);border-radius:4px;
  padding:10px 12px;font-family:var(--mono);font-size:11px;line-height:1.8;overflow-y:auto;min-height:100px}
.log-normal{color:var(--text)}.log-signal{color:var(--accent);font-weight:700}
.log-short{color:var(--red);font-weight:700}.log-header{color:var(--yellow)}.log-err{color:var(--dim)}
.log-t{color:var(--dim);margin-right:6px}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:4px;padding:12px 16px}
.card-title{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
  color:var(--dim);margin-bottom:10px;display:flex;align-items:center;gap:8px}
.card-title::before{content:'';display:block;width:3px;height:11px;background:var(--accent);border-radius:2px}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}
.scard{background:var(--bg3);border:1px solid var(--border2);border-radius:4px;padding:10px 14px}
.scard-v{font-family:var(--mono);font-size:20px;font-weight:700;margin-bottom:2px}
.scard-l{font-size:9px;color:var(--dim);text-transform:uppercase;letter-spacing:1px}
.empty{padding:30px;text-align:center;color:var(--dim);font-family:var(--mono);font-size:11px}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}
</style>
</head>
<body>

<header>
  <div class="logo">TD9 SCAN<small>BINANCE • PAPER TRADING</small></div>
  <div class="hstats">
    <div class="hstat"><div class="hstat-v g"  id="h-balance">--</div><div class="hstat-l">Bakiye</div></div>
    <div class="hstat"><div class="hstat-v b"  id="h-portfolio">--</div><div class="hstat-l">Portföy</div></div>
    <div class="hstat"><div class="hstat-v g"  id="h-pnl">--</div><div class="hstat-l">P&amp;L</div></div>
    <div class="hstat"><div class="hstat-v y"  id="h-open">0</div><div class="hstat-l">Açık Pos</div></div>
    <div class="hstat"><div class="hstat-v"    id="h-scan">0</div><div class="hstat-l">Tarama</div></div>
    <div class="hstat"><div class="hstat-v y"  id="h-coins">--</div><div class="hstat-l">Sinyal</div></div>
  </div>
  <div class="hcontrols">
    <div class="cfg"><label>Aralık(dk)</label><input type="number" id="cfg-interval" value="30" min="5" max="120" step="5"></div>
    <div class="cfg"><label>WR%</label><input type="number" id="cfg-wr" value="50" min="0" max="100"></div>
    <div class="cfg"><label>Mesafe%</label><input type="number" id="cfg-dist" value="5" min="1" max="20"></div>
    <button class="b-dim"   id="btn-apply" onclick="applyConfig()">UYGULA</button>
    <div id="countdown">Bağlanıyor...</div>
    <button class="b-green" id="btn-start" onclick="doStart()">▶ BAŞLAT</button>
    <button class="b-red"   id="btn-stop"  onclick="doStop()"  disabled>■ DURDUR</button>
    <button class="b-blue"  id="btn-scan"  onclick="doScan()"  disabled>⟳ HEMEN TARA</button>
  </div>
</header>

<div id="pbar"><div id="pfill"></div></div>
<div id="sbar">Bağlantı bekleniyor...</div>

<div class="tabs">
  <div class="tab on" onclick="showTab('positions')" id="tab-positions">Açık Pozisyonlar</div>
  <div class="tab"    onclick="showTab('signals')"   id="tab-signals">Sinyaller <span id="bdg-signals" class="tbadge" style="display:none">0</span></div>
  <div class="tab"    onclick="showTab('backtest')"  id="tab-backtest">Backtest</div>
  <div class="tab"    onclick="showTab('closed')"    id="tab-closed">Kapalı İşlemler <span id="bdg-closed" class="tbadge" style="display:none">0</span></div>
  <div class="tab"    onclick="showTab('stats')"     id="tab-stats">İstatistik</div>
  <div class="tab"    onclick="showTab('log')"       id="tab-log">Log</div>
  <div class="tab"    onclick="showTab('scanlog')"   id="tab-scanlog">Tarama Logu</div>
</div>

<div id="content">

<!-- POSITIONS -->
<div class="panel on" id="panel-positions">
  <div class="pfbar">
    <div class="pfitem"><div class="pfval g" id="pf-balance">--</div><div class="pflbl">Serbest Bakiye</div></div>
    <div class="pfitem"><div class="pfval b" id="pf-portfolio">--</div><div class="pflbl">Toplam Portföy</div></div>
    <div class="pfitem"><div class="pfval"   id="pf-pnl">--</div><div class="pflbl">Toplam P&amp;L</div></div>
    <div class="pfitem"><div class="pfval"   id="pf-open">0</div><div class="pflbl">Açık Pozisyon</div></div>
  </div>
  <div class="tbl-wrap" style="flex:1;overflow:auto">
    <table>
      <thead><tr>
        <th>Yön</th><th>Coin</th>
        <th title="İşlem büyüklüğü (USDT)">Boyut</th>
        <th>Giriş $</th><th>Güncel $</th><th>TP $</th><th>SL $</th>
        <th>PnL $</th><th>PnL %</th><th>WR%</th><th>TP↑</th><th>SL↓</th><th>Açılış</th>
      </tr></thead>
      <tbody id="tbody-positions"><tr><td colspan="13" class="empty">Açık pozisyon yok</td></tr></tbody>
    </table>
  </div>
</div>

<!-- SIGNALS -->
<div class="panel" id="panel-signals">
  <div class="tbl-wrap" style="flex:1;overflow:auto">
    <table>
      <thead><tr>
        <th>Tip</th><th>Coin</th><th>Fiyat $</th><th>WR%</th><th>K/T</th>
        <th>Boyut</th><th>Seviye $</th><th>Mesafe</th><th>HA</th><th>Durum</th>
      </tr></thead>
      <tbody id="tbody-signals"><tr><td colspan="10" class="empty">Sinyal bekleniyor</td></tr></tbody>
    </table>
  </div>
</div>

<!-- BACKTEST -->
<div class="panel" id="panel-backtest">
  <div class="tbl-wrap" style="flex:1;overflow:auto">
    <table>
      <thead><tr>
        <th>Tip</th><th>Coin</th><th>Fiyat $</th><th>WR%</th><th>K/T</th>
        <th>Sev. Türü</th><th>Seviye $</th><th>Mesafe</th><th>Test</th><th>Gün</th><th>Karar</th>
      </tr></thead>
      <tbody id="tbody-backtest"><tr><td colspan="11" class="empty">Backtest sonucu bekleniyor</td></tr></tbody>
    </table>
  </div>
</div>

<!-- CLOSED TRADES -->
<div class="panel" id="panel-closed">
  <div id="closed-summary" class="pfbar" style="flex-shrink:0"></div>
  <div class="tbl-wrap" style="flex:1;overflow:auto">
    <table>
      <thead><tr>
        <th>Yön</th><th>Coin</th>
        <th title="Kullanılan USDT">Boyut</th>
        <th>Giriş $</th><th>Çıkış $</th>
        <th>PnL $</th><th>PnL %</th><th>WR%</th><th>Sebep</th><th>Kapanış</th>
      </tr></thead>
      <tbody id="tbody-closed"><tr><td colspan="10" class="empty">Kapalı işlem yok</td></tr></tbody>
    </table>
  </div>
</div>

<!-- STATS -->
<div class="panel" id="panel-stats">
  <div class="sgrid" id="sgrid"></div>
  <div class="card" style="flex:1">
    <div class="card-title">Son Kapalı İşlemler</div>
    <div class="tbl-wrap">
      <table><thead><tr>
        <th>Yön</th><th>Coin</th><th>Boyut</th><th>Giriş</th><th>Çıkış</th><th>PnL%</th><th>Sebep</th>
      </tr></thead>
      <tbody id="tbody-stats-closed"></tbody></table>
    </div>
  </div>
</div>

<!-- LOG -->
<div class="panel" id="panel-log">
  <div class="logbox" id="logbox"></div>
</div>

<!-- SCANLOG -->
<div class="panel" id="panel-scanlog">
  <div class="logbox" id="scanlogbox"></div>
</div>

</div><!-- /content -->

<script>
const $ = id => document.getElementById(id);
const FMT = (n, d=2) => n == null ? '--' : Number(n).toFixed(d);

// ── TABS ─────────────────────────────────────────────────────────
function showTab(id){
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('on'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
  $('panel-'+id).classList.add('on');
  $('tab-'+id).classList.add('on');
}

// ── SSE ──────────────────────────────────────────────────────────
let sse = null;
function connectSSE(){
  if(sse) sse.close();
  sse = new EventSource('/stream');
  sse.addEventListener('status',    e => onStatus(JSON.parse(e.data)));
  sse.addEventListener('progress',  e => { $('pfill').style.width=(JSON.parse(e.data).pct||0)+'%'; });
  sse.addEventListener('countdown', e => onCountdown(JSON.parse(e.data)));
  sse.addEventListener('log',       e => addLog(JSON.parse(e.data)));
  sse.addEventListener('scanlog',   e => addScanLog(JSON.parse(e.data)));
  sse.addEventListener('signals',   e => renderSignals(JSON.parse(e.data)));
  sse.addEventListener('backtest',  e => renderBacktest(JSON.parse(e.data)));
  sse.addEventListener('positions', e => renderPositions(JSON.parse(e.data)));
  sse.addEventListener('stats',     e => renderStats(JSON.parse(e.data)));
  // ── DÜZELTME: closed olayını dinle ──
  sse.addEventListener('closed',    e => renderClosed(JSON.parse(e.data)));
  sse.onerror = () => { $('sbar').textContent='Bağlantı kesildi, yeniden bağlanılıyor...'; setTimeout(connectSSE,3000); };
}

// ── CONTROLS ─────────────────────────────────────────────────────
function doStart(){
  fetch('/start').then(r=>r.json()).then(d=>{
    if(d.ok){
      $('btn-start').disabled=true; $('btn-stop').disabled=false; $('btn-scan').disabled=false;
    } else alert('Başlatılamadı: '+d.msg);
  });
}
function doStop(){
  fetch('/stop').then(()=>{ $('btn-stop').disabled=true; $('btn-start').disabled=false; $('btn-scan').disabled=true; });
}
function doScan(){
  // ── DÜZELTME: force_scan endpoint ──
  fetch('/scan_now').then(r=>r.json()).then(d=>{
    $('sbar').textContent = d.scanning ? 'Tarama zaten devam ediyor — biter bitmez yeni tarama başlayacak.' : 'Manuel tarama başlatıldı...';
  });
}
function applyConfig(){
  const iv=$('cfg-interval').value, wr=$('cfg-wr').value, d=$('cfg-dist').value;
  fetch(`/config?interval=${iv}&wr=${wr}&dist=${d}`).then(r=>r.json()).then(d=>{
    $('sbar').textContent=`Ayarlar güncellendi: Aralık=${d.interval}dk WR>%${d.wr} Mesafe<%${d.dist}`;
  });
}

// ── STATUS ───────────────────────────────────────────────────────
function onStatus(d){
  $('sbar').textContent = d.text||'';
  if(d.scanning!==undefined) $('pfill').style.width = d.scanning?'5%':'100%';
}
function onCountdown(d){
  $('countdown').textContent = d.text + '  (her '+d.interval+'dk)';
  $('h-scan').textContent = d.scan;
}

// ── LOG ──────────────────────────────────────────────────────────
function addLog(e){
  const box=$('logbox'), div=document.createElement('div');
  div.className='log-'+e.kind;
  div.innerHTML=`<span class="log-t">${e.t}</span>${esc(e.msg)}`;
  box.appendChild(div);
  if(box.children.length>600) box.removeChild(box.firstChild);
  box.scrollTop=box.scrollHeight;
}
function addScanLog(e){
  const box=$('scanlogbox'), div=document.createElement('div');
  div.className='log-'+e.kind;
  div.innerHTML=`<span class="log-t">${e.t}</span>${esc(e.msg)}`;
  box.appendChild(div);
  if(box.children.length>2000) box.removeChild(box.firstChild);
  box.scrollTop=box.scrollHeight;
}
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ── POSITIONS ────────────────────────────────────────────────────
function renderPositions(d){
  const pf=d.portfolio||0, bal=d.balance||0, init=d.initial||50000;
  const pnl=pf-init, pnlPct=pnl/init*100;
  $('h-balance').textContent   = '$'+FMT(bal,0);
  $('h-portfolio').textContent = '$'+FMT(pf,0);
  $('h-pnl').textContent       = (pnl>=0?'+':'')+FMT(pnl,0)+'$';
  $('h-pnl').className         = 'hstat-v '+(pnl>=0?'g':'r');
  $('pf-balance').textContent   = '$'+FMT(bal,2);
  $('pf-portfolio').textContent = '$'+FMT(pf,2);
  $('pf-pnl').textContent       = (pnl>=0?'+':'')+FMT(pnl,2)+'$ ('+FMT(pnlPct,2)+'%)';
  $('pf-pnl').className         = 'pfval '+(pnl>=0?'g':'r');
  const rows=d.positions||[];
  $('h-open').textContent  = rows.length;
  $('pf-open').textContent = rows.length;
  const tbody=$('tbody-positions');
  if(!rows.length){
    tbody.innerHTML='<tr><td colspan="13" class="empty">Açık pozisyon yok</td></tr>'; return;
  }
  tbody.innerHTML=rows.map(p=>{
    const dir=p.direction==='long';
    const badge=dir?'<span class="badge bg">LONG</span>':'<span class="badge br">SHORT</span>';
    const cl=p.pnl_pct>=0?'g':'r';
    return `<tr>
      <td>${badge}</td>
      <td><b>${p.sym}</b></td>
      <td class="y"><b>${FMT(p.size,0)} $</b></td>
      <td class="b">$${FMT(p.entry,6)}</td>
      <td>$${FMT(p.cur,6)}</td>
      <td class="g">$${FMT(p.tp,6)}</td>
      <td class="r">$${FMT(p.sl,6)}</td>
      <td class="${cl}">${p.pnl>=0?'+':''}${FMT(p.pnl,2)}$</td>
      <td class="${cl}">${p.pnl_pct>=0?'+':''}${FMT(p.pnl_pct,2)}%</td>
      <td class="y">${FMT(p.winrate,1)}%</td>
      <td class="g">${FMT(p.dtp,2)}%</td>
      <td class="r">${FMT(p.dsl,2)}%</td>
      <td class="dim">${p.time||'--'}</td>
    </tr>`;
  }).join('');
}

// ── SIGNALS ──────────────────────────────────────────────────────
function renderSignals(d){
  const buys=d.buys||[], sells=d.sells||[];
  const total=buys.length+sells.length;
  const bdg=$('bdg-signals');
  if(total){ bdg.textContent=total; bdg.style.display=''; } else bdg.style.display='none';
  $('h-coins').textContent = total||'--';
  const rows=[];
  buys.forEach(r  => rows.push(sigRow(r,'buy')));
  sells.forEach(r => rows.push(sigRow(r,'sell')));
  $('tbody-signals').innerHTML = rows.length ? rows.join('') :
    '<tr><td colspan="10" class="empty">Sinyal bulunamadı</td></tr>';
}
function sigRow(r, type){
  const isBuy=type==='buy';
  const wr=isBuy?r.bwr:r.swr, tot=isBuy?r.btot:r.stot, wins=isBuy?r.bwins:r.swins;
  const passed=isBuy?r.buy_passed:r.sell_passed;
  const dist=isBuy?r.sdist:r.rdist, lvl=isBuy?r.sup:r.res;
  const tr=r.trade_result||'';
  const dirBadge=isBuy?'<span class="badge bg">BUY9</span>':'<span class="badge br">SELL9</span>';
  const wrCl=wr>=80?'g':wr>=50?'b':'dim';
  const distCl=Math.abs(dist)<=5?'g':'r';
  const ha=r.ha_bull?'<span class="g">▲</span>':'<span class="r">▽</span>';
  let durum;
  if(!passed){
    const p=[];
    if(isBuy&&!r.bwr_ok||!isBuy&&!r.swr_ok) p.push('WR düşük');
    if(isBuy&&!r.supp_ok||!isBuy&&!r.res_ok) p.push(dist<0?(isBuy?'Destek kırıldı':'Direnç kırıldı'):'Uzak');
    durum=`<span class="badge bd">ATILDI: ${p.join(', ')}</span>`;
  } else if(tr==='LONG_OK')  durum='<span class="badge bg">✔ LONG 500$</span>';
  else if(tr==='SHORT_OK')   durum='<span class="badge br">✔ SHORT 500$</span>';
  else if(tr&&tr.startsWith('ERR')) durum=`<span class="badge by">✘ ${tr.slice(4)}</span>`;
  else                       durum='<span class="badge by">⏳ bekle</span>';
  return `<tr>
    <td>${dirBadge}</td><td><b>${r.sym}</b></td>
    <td class="b">$${FMT(r.price,6)}</td>
    <td class="${wrCl}"><b>${FMT(wr,1)}%</b></td>
    <td>${wins}/${tot}</td>
    <td class="y">500$</td>
    <td>$${FMT(lvl,5)}</td>
    <td class="${distCl}">${dist>=0?'+':''}${FMT(dist,1)}%</td>
    <td>${ha}</td>
    <td>${durum}</td>
  </tr>`;
}

// ── BACKTEST ─────────────────────────────────────────────────────
function renderBacktest(d){
  const all=d.results||[];
  const rows=[];
  all.forEach(r=>{
    // _row_type varsa kullan, yoksa buy9/sell9 kontrol et
    const rt=r._row_type;
    const hasBuy  = rt ? rt==='BUY'  : r.buy9===9;
    const hasSell = rt ? rt==='SELL' : r.sell9===9;
    if(hasBuy){
      rows.push({sym:r.sym, price:r.price, type:'BUY',
        wr:r.bwr||0, wins:r.bwins||0, tot:r.btot||0,
        wr_ok:r.bwr_ok, lvl_ok:r.supp_ok, lvl:r.sup||0, dist:r.sdist||0, tc:r.stc||0,
        lbl:'DESTEK', passed:r.buy_passed, days:r.days||0});
    }
    if(hasSell){
      rows.push({sym:r.sym, price:r.price, type:'SELL',
        wr:r.swr||0, wins:r.swins||0, tot:r.stot||0,
        wr_ok:r.swr_ok, lvl_ok:r.res_ok, lvl:r.res||0, dist:r.rdist||0, tc:r.rtc||0,
        lbl:'DİRENÇ', passed:r.sell_passed, days:r.days||0});
    }
  });
  rows.sort((a,b)=>b.wr-a.wr);
  const tbody=$('tbody-backtest');
  if(!rows.length){
    tbody.innerHTML='<tr><td colspan="11" class="empty">Henüz TD9=9 sinyali yok — tarama devam ediyor...</td></tr>'; return;
  }
  const passed=rows.filter(r=>r.passed).length;
  tbody.innerHTML=rows.map(r=>{
    const badge=r.type==='BUY'?'<span class="badge bg">BUY9</span>':'<span class="badge br">SELL9</span>';
    const wrCl=r.wr>=80?'g':r.wr>=50?'b':'dim';
    const distCl=r.dist>=0&&r.dist<=5?'g':'r';
    let karar;
    if(r.passed){
      karar=r.type==='BUY'?'<span class="badge bg">✔ LONG AÇILDI</span>':'<span class="badge br">✔ SHORT AÇILDI</span>';
    } else {
      const p=[];
      if(!r.wr_ok) p.push(`WR:${FMT(r.wr,0)}%<50%`);
      if(!r.lvl_ok) p.push(r.dist<0?`${r.lbl} KIRILDI`:`${r.lbl} UZAK`);
      karar=`<span class="badge bd">ATILDI (${p.join(', ')})</span>`;
    }
    return `<tr>
      <td>${badge}</td><td><b>${r.sym}</b></td>
      <td class="b">$${FMT(r.price,6)}</td>
      <td class="${wrCl}"><b>${FMT(r.wr,1)}%</b></td>
      <td>${r.wins}/${r.tot}</td>
      <td class="dim">${r.lbl}</td>
      <td>$${FMT(r.lvl,5)}</td>
      <td class="${distCl}">${r.dist>=0?'+':''}${FMT(r.dist,1)}%</td>
      <td>${r.tc}x</td>
      <td>${r.days}g</td>
      <td>${karar}</td>
    </tr>`;
  }).join('') + `<tr><td colspan="5" style="padding:6px 10px;color:var(--dim);font-size:10px">
    Toplam: ${rows.length} | Geçen: ${passed} | Atılan: ${rows.length-passed}
  </td><td colspan="6"></td></tr>`;
}

// ── CLOSED TRADES ─────────────────────────────────────────────────
function renderClosed(d){
  const closed=d.closed||[];
  const bdg=$('bdg-closed');
  if(closed.length){ bdg.textContent=closed.length; bdg.style.display=''; } else bdg.style.display='none';

  // Özet bar
  const totalPnl=closed.reduce((a,t)=>a+t.pnl,0);
  const wins=closed.filter(t=>t.pnl>0).length;
  $('closed-summary').innerHTML=`
    <div class="pfitem"><div class="pfval">${closed.length}</div><div class="pflbl">Toplam İşlem</div></div>
    <div class="pfitem"><div class="pfval g">${wins}</div><div class="pflbl">Kazanan</div></div>
    <div class="pfitem"><div class="pfval r">${closed.length-wins}</div><div class="pflbl">Kaybeden</div></div>
    <div class="pfitem"><div class="pfval ${closed.length?FMT(wins/closed.length*100,0)>50?'g':'r':''}">${closed.length?FMT(wins/closed.length*100,1)+'%':'--'}</div><div class="pflbl">WR%</div></div>
    <div class="pfitem"><div class="pfval ${totalPnl>=0?'g':'r'}">${totalPnl>=0?'+':''}${FMT(totalPnl,2)}$</div><div class="pflbl">Net PnL</div></div>
  `;

  const tbody=$('tbody-closed');
  if(!closed.length){
    tbody.innerHTML='<tr><td colspan="10" class="empty">Kapalı işlem yok</td></tr>'; return;
  }
  tbody.innerHTML=closed.map(t=>{
    const badge=t.direction==='long'?'<span class="badge bg">LONG</span>':'<span class="badge br">SHORT</span>';
    const cl=t.pnl>=0?'g':'r';
    const rc=t.reason==='TAKE PROFIT'?'g':'r';
    return `<tr>
      <td>${badge}</td>
      <td><b>${t.sym}</b></td>
      <td class="y"><b>${FMT(t.size,0)}$</b></td>
      <td class="b">$${FMT(t.entry,6)}</td>
      <td>$${FMT(t.exit,6)}</td>
      <td class="${cl}">${t.pnl>=0?'+':''}${FMT(t.pnl,2)}$</td>
      <td class="${cl}">${t.pnl_pct>=0?'+':''}${FMT(t.pnl_pct,2)}%</td>
      <td class="y">${FMT(t.winrate,1)}%</td>
      <td class="${rc}">${t.reason}</td>
      <td class="dim">${t.close_time||'--'}</td>
    </tr>`;
  }).join('');
}

// ── STATS ────────────────────────────────────────────────────────
function renderStats(d){
  const pf=d.portfolio||0, init=d.initial||50000;
  const pnl=pf-init, pnlPct=pnl/init*100;
  const cards=[
    {v:'$'+FMT(d.balance,0),  l:'Serbest Bakiye', cl:'g'},
    {v:'$'+FMT(pf,0),         l:'Portföy',        cl:'b'},
    {v:(pnl>=0?'+':'')+FMT(pnl,0)+'$', l:'Toplam P&L', cl:pnl>=0?'g':'r'},
    {v:FMT(pnlPct,2)+'%',     l:'Portföy %',      cl:pnlPct>=0?'g':'r'},
    {v:d.total||0,             l:'Toplam İşlem',   cl:''},
    {v:d.wins||0,              l:'Kazanan',        cl:'g'},
    {v:d.losses||0,            l:'Kaybeden',       cl:'r'},
    {v:FMT(d.wr,1)+'%',       l:'Gerçek WR',      cl:(d.wr||0)>=50?'g':'r'},
    {v:(d.pnl>=0?'+':'')+FMT(d.pnl,2)+'$', l:'Net PnL', cl:(d.pnl||0)>=0?'g':'r'},
    {v:FMT(d.kf,2),            l:'Kazanç Faktörü', cl:(d.kf||0)>=1?'g':'r'},
  ];
  $('sgrid').innerHTML=cards.map(c=>
    `<div class="scard"><div class="scard-v ${c.cl}">${c.v}</div><div class="scard-l">${c.l}</div></div>`
  ).join('');
  const closed=d.closed||[];
  $('tbody-stats-closed').innerHTML=closed.map(t=>`<tr>
    <td>${t.direction==='long'?'<span class="badge bg">L</span>':'<span class="badge br">S</span>'}</td>
    <td><b>${t.sym}</b></td>
    <td class="y">${FMT(t.size,0)}$</td>
    <td class="b">$${FMT(t.entry,6)}</td>
    <td>$${FMT(t.exit,6)}</td>
    <td class="${t.pnl_pct>=0?'g':'r'}">${t.pnl_pct>=0?'+':''}${FMT(t.pnl_pct,2)}%</td>
    <td class="${t.reason==='TAKE PROFIT'?'g':'r'}">${t.reason}</td>
  </tr>`).join('')||'<tr><td colspan="7" class="empty">Kapanmış işlem yok</td></tr>';
}

// ── INIT ─────────────────────────────────────────────────────────
connectSSE();
fetch('/state').then(r=>r.json()).then(d=>{
  if(d.positions) renderPositions(d.positions);
  if(d.signals)   renderSignals(d.signals);
  if(d.backtest)  renderBacktest(d.backtest);
  if(d.stats)     renderStats(d.stats);
  if(d.closed_data) renderClosed(d.closed_data);
  if(d.running){ $('btn-start').disabled=true; $('btn-stop').disabled=false; $('btn-scan').disabled=false; }
  (d.logs||[]).forEach(e=>addLog(e));
  (d.scan_logs||[]).forEach(e=>addScanLog(e));
});
</script>
</body>
</html>"""

# ============================================================================
# FLASK APP
# ============================================================================
app     = Flask(__name__)
scanner = Scanner()

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/stream')
def stream():
    q = queue.Queue()
    with scanner._lock:
        scanner.clients.append(q)
    def gen():
        yield f"event: status\ndata: {json.dumps({'text':'Bağlandı','scanning':scanner.is_scanning})}\n\n"
        try:
            while True:
                try:
                    msg = q.get(timeout=20)
                    yield msg
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            with scanner._lock:
                if q in scanner.clients: scanner.clients.remove(q)
    return Response(gen(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/start')
def start():
    if not DEPS_OK:
        return {'ok': False, 'msg': 'ccxt veya pandas yüklü değil. pip install ccxt pandas flask'}
    if scanner.is_running:
        return {'ok': True, 'msg': 'Zaten çalışıyor'}
    ok = scanner.start()
    return {'ok': ok, 'msg': '' if ok else 'Bağlantı hatası'}

@app.route('/stop')
def stop():
    scanner.is_running = False
    scanner.push('status', {'text': 'Durduruldu', 'scanning': False})
    return {'ok': True}

@app.route('/scan_now')
def scan_now():
    """DÜZELTME: Tarama yoksa anında başlat, varsa force_scan bayrağı koy."""
    if not scanner.is_scanning:
        scanner.last_scan = 0      # döngü hemen tetikler
        return {'ok': True, 'scanning': False}
    else:
        scanner.force_scan = True  # mevcut tarama bitince başlar
        return {'ok': True, 'scanning': True}

@app.route('/config')
def config():
    iv = request.args.get('interval', 30)
    wr = request.args.get('wr', 50)
    d  = request.args.get('dist', 5)
    scanner.set_interval(iv)
    scanner.set_wr(wr)
    scanner.set_dist(d)
    return {'ok': True, 'interval': scanner.SCAN_EVERY // 60,
            'wr': scanner.WR_THRESH, 'dist': scanner.SUPP_MAX}

@app.route('/state')
def state():
    return {
        'running':     scanner.is_running,
        'positions':   scanner.positions_data(),
        'signals':     scanner.signals_data(),
        'backtest':    scanner.backtest_data(),
        'stats':       scanner.stats_data(),
        'closed_data': scanner.closed_data(),
        'logs':        scanner.logs[-200:],
        'scan_logs':   scanner.scan_logs[-500:],
    }

# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    if not DEPS_OK:
        print("HATA: Gerekli kütüphaneler eksik.")
        print("  pip install ccxt pandas flask")
        exit(1)
    PORT = 5050
    print(f"""
╔══════════════════════════════════════════╗
║     BINANCE TD9 SCANNER — WEB UI        ║
╠══════════════════════════════════════════╣
║  Tarayıcı: http://localhost:{PORT}        ║
║  Durdurmak: Ctrl+C                       ║
╚══════════════════════════════════════════╝
""")
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
