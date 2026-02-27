"""
NASDAQ & S&P 500 & Russell 2000 TD Sequential + Heiken Ashi Weekly Scanner
Automatically scans all stocks in NASDAQ 100, S&P 500, and Russell 2000 indices
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
import time
warnings.filterwarnings('ignore')

def get_nasdaq_100_stocks():
    """
    Get NASDAQ 100 stocks
    Current major components
    """
    nasdaq_100 = [
        # Mega Cap Tech
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
        "AVGO", "COST", "NFLX", "AMD", "ADBE", "PEP", "CSCO", "TMUS",
        
        # Large Tech & Software
        "INTC", "CMCSA", "TXN", "QCOM", "INTU", "AMAT", "HON", "AMGN",
        "BKNG", "ADP", "SBUX", "GILD", "ADI", "VRTX", "ISRG", "LRCX",
        
        # Mid-Large Tech
        "REGN", "PANW", "MU", "MELI", "KLAC", "SNPS", "CDNS", "PYPL",
        "NXPI", "ABNB", "MAR", "ORLY", "MNST", "CRWD", "WDAY", "FTNT",
        
        # Growth & Innovation
        "MRVL", "ASML", "ADSK", "LULU", "DXCM", "CHTR", "AZN", "PCAR",
        "CPRT", "CTAS", "PAYX", "ODFL", "TTD", "ROST", "FAST", "VRSK",
        
        # Tech & Services
        "IDXX", "EA", "TEAM", "ON", "GEHC", "DDOG", "CTSH", "BIIB",
        "BKR", "XEL", "ANSS", "ZS", "ILMN", "MRNA", "EXC", "FANG",
        
        # Additional Components
        "WBD", "SIRI", "ALGN", "EBAY", "ENPH", "DLTR", "JD", "PDD",
        "RIVN", "LCID", "COIN", "ZM", "DOCU", "RBLX", "HOOD", "DASH"
    ]
    
    # Remove duplicates and sort
    nasdaq_100 = sorted(list(set(nasdaq_100)))
    print(f"✓ Loaded {len(nasdaq_100)} NASDAQ 100 stocks")
    return nasdaq_100

def get_sp500_stocks():
    """
    Get S&P 500 major stocks
    Focus on large and mega-cap stocks
    """
    sp500_major = [
        # Mega Cap
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
        "LLY", "AVGO", "JPM", "V", "UNH", "XOM", "MA", "WMT",
        
        # Large Cap Tech
        "ORCL", "HD", "COST", "NFLX", "CRM", "BAC", "AMD", "PG",
        "ABBV", "KO", "MRK", "PEP", "CSCO", "ACN", "TMUS", "ADBE",
        
        # Large Cap Financial & Healthcare
        "CVX", "LIN", "MCD", "WFC", "ABT", "TMO", "NKE", "DHR",
        "PM", "CMCSA", "VZ", "DIS", "INTC", "TXN", "QCOM", "NEE",
        
        # Large Industrial & Consumer
        "UPS", "COP", "BMY", "RTX", "HON", "LOW", "SPGI", "UNP",
        "AMGN", "INTU", "T", "PFE", "BA", "CAT", "GE", "DE",
        
        # Financial Services
        "AXP", "BLK", "GS", "MS", "C", "SCHW", "CB", "MMC",
        "USB", "PNC", "TFC", "COF", "AIG", "MET", "PRU", "ALL",
        
        # Healthcare & Pharma
        "JNJ", "GILD", "REGN", "VRTX", "ISRG", "CI", "HUM", "CVS",
        "ELV", "BSX", "MDT", "SYK", "ZTS", "AMGN", "BIIB", "MRNA",
        
        # Consumer & Retail
        "SBUX", "TGT", "BKNG", "MAR", "ABNB", "ORLY", "GM", "F",
        "CMG", "YUM", "LULU", "NKE", "TJX", "DG", "ROST", "ULTA",
        
        # Energy & Utilities
        "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL", "KMI",
        "WMB", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL",
        
        # Industrials
        "LMT", "GD", "NOC", "RTX", "BA", "HON", "UNP", "UPS",
        "FDX", "NSC", "CSX", "WM", "EMR", "ETN", "ITW", "PH",
        
        # Materials & Chemicals
        "LIN", "APD", "SHW", "ECL", "DD", "DOW", "NEM", "FCX",
        "NUE", "VMC", "MLM", "PPG", "CF", "MOS", "ALB", "FMC",
        
        # Communication Services
        "GOOGL", "META", "DIS", "NFLX", "CMCSA", "T", "VZ", "TMUS",
        "PARA", "WBD", "FOX", "FOXA", "MTCH", "LYV", "NWSA", "NWS",
        
        # Real Estate
        "PLD", "AMT", "CCI", "EQIX", "PSA", "WELL", "DLR", "O",
        "SPG", "VICI", "SBAC", "AVB", "EQR", "ARE", "VTR", "MAA",
        
        # Additional Major Stocks
        "AMAT", "ADI", "LRCX", "KLAC", "SNPS", "CDNS", "MCHP", "TER",
        "ADP", "PAYX", "FAST", "VRSK", "CTAS", "CPRT", "ODFL", "CHRW",
        "SQ", "PYPL", "FIS", "FISV", "ADP", "PAYX", "BR", "TRU"
    ]
    
    # Remove duplicates and sort
    sp500_major = sorted(list(set(sp500_major)))
    print(f"✓ Loaded {len(sp500_major)} S&P 500 stocks")
    return sp500_major

def get_russell_2000_stocks():
    """
    Get Russell 2000 major stocks
    Focus on liquid small-cap stocks
    """
    russell_2000 = [
        # Top Small-Cap Tech
        "SMCI", "IONQ", "CVNA", "GTLS", "FOUR", "DOCN", "FRSH", "NCNO",
        "TENB", "ALKT", "GTLB", "PCOR", "ASAN", "CELH", "BROS", "CAVA",
        
        # Small-Cap Healthcare & Biotech
        "KRYS", "PTGX", "VERV", "TMDX", "NTRA", "NARI", "VERA", "CGEM",
        "KROS", "REPX", "GLUE", "RYTM", "DNLI", "IMVT", "CRNX", "BCYC",
        
        # Small-Cap Financial
        "COOP", "CADE", "WTFC", "FFIN", "VBTX", "UMBF", "UBSI", "FNB",
        "ONB", "IBOC", "CASH", "COLB", "SFNC", "WAFD", "HWC", "SBCF",
        
        # Small-Cap Industrial & Restaurant
        "ROAD", "SHAK", "WING", "TXRH", "BLMN", "DIN", "PLAY", "BJRI",
        "CHUY", "DINE", "CAKE", "TAST", "KRUS", "RUTH", "DENN", "RRGB",
        
        # Small-Cap Energy
        "SM", "CIVI", "MTDR", "CHRD", "MGY", "GPOR", "CNX", "VNOM",
        "REI", "CRGY", "PR", "AR", "NOG", "TALO", "CRK", "WKC",
        
        # Small-Cap Consumer & Retail
        "CASY", "TSCO", "BOOT", "CAL", "AEO", "ANF", "EXPR", "URBN",
        "GES", "PLCE", "HIBB", "BGFV", "DKS", "ASO", "SCVL", "VSCO",
        
        # Small-Cap REITs
        "IVT", "BNL", "HIW", "DEI", "SLG", "JBGS", "BXP", "KRC",
        "CUZ", "PGRE", "PDM", "OPI", "AHH", "BRX", "SVC", "UE",
        
        # Small-Cap Materials
        "ATKR", "LTHM", "MP", "HWKN", "HAYN", "SLVM", "AMR", "IE",
        "CENX", "KALU", "CRS", "ZEUS", "GFF", "MTRN", "OMI", "DNOW",
        
        # Small-Cap Utilities
        "AWR", "YORW", "MSEX", "SJW", "ARTNA", "OTTR", "NWE", "AVA",
        "POR", "BKH", "NWN", "SR", "UTL", "MGEE", "CPK", "CALM",
        
        # Small-Cap Communication
        "SATS", "GOGO", "IRDM", "VSAT", "GILT", "TGNA", "NXST", "GTN",
        "SSP", "THRY", "GDEN", "IMAX", "CNK", "MSGM", "FUBO", "SHEN",
        
        # Emerging Small-Cap
        "RKLB", "LUNR", "ACHR", "JOBY", "EVTL", "ASTS", "SPIR", "PL",
        "RDW", "GATO", "CMPO", "VZIO", "SONO", "KOSS", "HEAR", "GPRO",
        
        # Small-Cap Retail & Others
        "FIVE", "OLLI", "BURL", "MNRO", "GCO", "PSMT", "CONN", "LE",
        "AAN", "SAH", "ABG", "BBWI", "PETS", "WOOF", "CHWY", "SITE"
    ]
    
    # Remove duplicates and sort
    russell_2000 = sorted(list(set(russell_2000)))
    print(f"✓ Loaded {len(russell_2000)} Russell 2000 stocks")
    return russell_2000

def heiken_ashi(df):
    """
    Calculate Heiken Ashi candles
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
    TD Sequential calculation on Heiken Ashi candles
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
    
    # Trend analysis
    df['ha_trend'] = 'NEUTRAL'
    for i in range(len(df)):
        if df['HA_Close'].iloc[i] > df['HA_Open'].iloc[i]:
            df.loc[df.index[i], 'ha_trend'] = 'BULLISH'
        elif df['HA_Close'].iloc[i] < df['HA_Open'].iloc[i]:
            df.loc[df.index[i], 'ha_trend'] = 'BEARISH'
    
    return df

def calculate_trend_strength(df):
    """
    Calculate trend strength
    """
    if len(df) < 5:
        return "UNCLEAR"
    
    last_5 = df.tail(5)
    bullish_count = (last_5['ha_trend'] == 'BULLISH').sum()
    bearish_count = (last_5['ha_trend'] == 'BEARISH').sum()
    
    if bullish_count >= 4:
        return "STRONG BULLISH"
    elif bearish_count >= 4:
        return "STRONG BEARISH"
    elif bullish_count >= 3:
        return "MODERATE BULLISH"
    elif bearish_count >= 3:
        return "MODERATE BEARISH"
    else:
        return "INDECISIVE"

def analyze_buy_setup_success_rate(df):
    """
    Analyze historical Buy Setup 9 signals and their success rate
    Returns success rate and average gain percentage
    """
    buy_setup_9_signals = []
    
    # Find all Buy Setup 9 occurrences in historical data
    for i in range(len(df)):
        if df['buy_setup'].iloc[i] == 9:
            buy_setup_9_signals.append(i)
    
    if len(buy_setup_9_signals) == 0:
        return None, None, 0
    
    successful_signals = 0
    total_gain = 0
    gains_list = []
    
    # Analyze each Buy Setup 9 signal
    for signal_idx in buy_setup_9_signals:
        # Need at least 20 days after signal to analyze
        if signal_idx + 20 >= len(df):
            continue
        
        signal_price = df['Close'].iloc[signal_idx]
        
        # Check prices for next 20 days
        max_price_after = df['Close'].iloc[signal_idx+1:signal_idx+21].max()
        
        # Calculate gain percentage
        gain_pct = ((max_price_after - signal_price) / signal_price) * 100
        gains_list.append(gain_pct)
        total_gain += gain_pct
        
        # Count as successful if gained more than 2%
        if gain_pct > 2:
            successful_signals += 1
    
    if len(gains_list) == 0:
        return None, None, 0
    
    success_rate = (successful_signals / len(gains_list)) * 100
    avg_gain = total_gain / len(gains_list)
    
    return success_rate, avg_gain, len(gains_list)

def scan_stock(symbol, period="3mo"):
    """
    Scan a single stock
    """
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval="1d")
        
        if df.empty or len(df) < 10:
            return None
        
        df = td_sequential_heiken_ashi(df)
        trend_strength = calculate_trend_strength(df)
        
        last_buy_setup = df['buy_setup'].iloc[-1]
        last_sell_setup = df['sell_setup'].iloc[-1]
        last_price = df['Close'].iloc[-1]
        last_ha_close = df['HA_Close'].iloc[-1]
        last_ha_open = df['HA_Open'].iloc[-1]
        last_trend = df['ha_trend'].iloc[-1]
        
        ha_color = "🟢 GREEN" if last_ha_close > last_ha_open else "🔴 RED"
        
        result = {
            'symbol': symbol,
            'last_price': round(last_price, 2),
            'ha_close': round(last_ha_close, 2),
            'ha_open': round(last_ha_open, 2),
            'ha_color': ha_color,
            'ha_trend': last_trend,
            'trend_strength': trend_strength,
            'buy_setup_9': last_buy_setup == 9,
            'sell_setup_9': last_sell_setup == 9,
            'buy_setup': int(last_buy_setup),
            'sell_setup': int(last_sell_setup),
            'date': df.index[-1].strftime('%Y-%m-%d'),
            'success_rate': None,
            'avg_gain': None,
            'signal_count': 0
        }
        
        return result
        
    except Exception as e:
        return None

def analyze_buy_setup_with_history(symbol):
    """
    Detailed analysis with longer historical data for Buy Setup 9 stocks
    """
    try:
        stock = yf.Ticker(symbol)
        # Get 2 years of data for better historical analysis
        df = stock.history(period="2y", interval="1d")
        
        if df.empty or len(df) < 50:
            return None
        
        df = td_sequential_heiken_ashi(df)
        
        # Analyze historical Buy Setup 9 success rate
        success_rate, avg_gain, signal_count = analyze_buy_setup_success_rate(df)
        
        # Get current signal info
        last_buy_setup = df['buy_setup'].iloc[-1]
        last_price = df['Close'].iloc[-1]
        last_ha_close = df['HA_Close'].iloc[-1]
        last_ha_open = df['HA_Open'].iloc[-1]
        trend_strength = calculate_trend_strength(df)
        
        ha_color = "🟢 GREEN" if last_ha_close > last_ha_open else "🔴 RED"
        
        result = {
            'symbol': symbol,
            'last_price': round(last_price, 2),
            'ha_close': round(last_ha_close, 2),
            'ha_open': round(last_ha_open, 2),
            'ha_color': ha_color,
            'trend_strength': trend_strength,
            'success_rate': round(success_rate, 1) if success_rate else None,
            'avg_gain': round(avg_gain, 2) if avg_gain else None,
            'signal_count': signal_count,
            'date': df.index[-1].strftime('%Y-%m-%d')
        }
        
        return result
        
    except Exception as e:
        return None

def scan_all_stocks(index_name="NASDAQ"):
    """
    Scan all stocks in the selected index
    """
    print("=" * 100)
    print(f"US STOCK MARKET - TD SEQUENTIAL + HEIKEN ASHI SCANNER - {index_name}")
    print("=" * 100)
    print(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    
    # Get stock list
    if index_name == "NASDAQ":
        stocks = get_nasdaq_100_stocks()
    elif index_name == "SP500":
        stocks = get_sp500_stocks()
    elif index_name == "RUSSELL2000":
        stocks = get_russell_2000_stocks()
    else:  # ALL
        nasdaq = get_nasdaq_100_stocks()
        sp500 = get_sp500_stocks()
        russell = get_russell_2000_stocks()
        stocks = sorted(list(set(nasdaq + sp500 + russell)))
        print(f"Combined List: {len(stocks)} unique stocks")
    
    print(f"Total Stocks to Scan: {len(stocks)}")
    print("=" * 100)
    print("\nStarting scan... (This may take several minutes)\n")
    
    buy_setup_9_list = []
    sell_setup_9_list = []
    other_signals = []
    failed = 0
    
    # Progress tracking
    total = len(stocks)
    
    # Scan each stock
    for i, symbol in enumerate(stocks, 1):
        # Show progress
        percent = (i / total) * 100
        print(f"Progress: [{i}/{total}] {percent:.1f}% - {symbol:10s}", end='\r')
        
        result = scan_stock(symbol)
        
        if result:
            if result['buy_setup_9']:
                buy_setup_9_list.append(result)
            elif result['sell_setup_9']:
                sell_setup_9_list.append(result)
            elif result['buy_setup'] >= 7 or result['sell_setup'] >= 7:
                other_signals.append(result)
        else:
            failed += 1
        
        # Brief pause to respect API rate limits
        if i % 10 == 0:
            time.sleep(0.5)
    
    print("\n" + "=" * 100)
    print(f"✓ Scan completed!")
    print(f"  • Successful: {total - failed}")
    print(f"  • Failed: {failed}")
    print("=" * 100)
    
    # Display results - BUY SETUP 9
    print("\n🟢 BUY SETUP 9 (BUY SIGNAL) - Heiken Ashi Weekly:")
    print("-" * 100)
    if buy_setup_9_list:
        # Sort by trend strength
        buy_setup_9_sorted = sorted(buy_setup_9_list, 
                                    key=lambda x: (x['ha_color'] == "🟢 GREEN", 
                                                  "INDECISIVE" in x['trend_strength'],
                                                  "MODERATE" in x['trend_strength']), 
                                    reverse=True)
        for s in buy_setup_9_sorted:
            print(f"  {s['symbol']:8s} | Price: ${s['last_price']:10.2f} | HA: {s['ha_color']} | "
                  f"Trend: {s['trend_strength']:20s} | {s['date']}")
    else:
        print("  No signals found")
    
    # HISTORICAL SUCCESS RATE ANALYSIS FOR BUY SETUP 9
    if buy_setup_9_list:
        print("\n" + "=" * 100)
        print("📊 HISTORICAL BUY SETUP 9 SUCCESS RATE ANALYSIS")
        print("=" * 100)
        print("Analyzing past Buy Setup 9 signals for each stock (2-year history)...")
        print("Success = Price increased >2% within 20 days after signal\n")
        
        historical_results = []
        
        for i, s in enumerate(buy_setup_9_sorted, 1):
            print(f"Analyzing {s['symbol']}... [{i}/{len(buy_setup_9_sorted)}]", end='\r')
            
            hist_data = analyze_buy_setup_with_history(s['symbol'])
            if hist_data:
                historical_results.append(hist_data)
            
            # Brief pause
            if i % 5 == 0:
                time.sleep(0.3)
        
        print("\n" + "-" * 100)
        
        if historical_results:
            # Sort by success rate
            historical_results_sorted = sorted(
                historical_results, 
                key=lambda x: (x['success_rate'] if x['success_rate'] else 0), 
                reverse=True
            )
            
            print(f"\n{'Symbol':<10} {'Price':<12} {'HA Color':<12} {'Trend':<20} "
                  f"{'Success Rate':<15} {'Avg Gain':<12} {'Signals':<10}")
            print("-" * 100)
            
            total_success = 0
            total_signals = 0
            valid_stocks = 0
            
            for h in historical_results_sorted:
                if h['success_rate'] is not None:
                    success_indicator = "✅" if h['success_rate'] >= 60 else "⚠️" if h['success_rate'] >= 40 else "❌"
                    gain_indicator = "📈" if h['avg_gain'] and h['avg_gain'] > 5 else "📊" if h['avg_gain'] and h['avg_gain'] > 2 else "📉"
                    
                    print(f"{h['symbol']:<10} ${h['last_price']:<11.2f} {h['ha_color']:<12} {h['trend_strength']:<20} "
                          f"{success_indicator} {h['success_rate']:>5.1f}%{'':<7} {gain_indicator} {h['avg_gain']:>6.2f}%{'':<3} {h['signal_count']:>3} times")
                    
                    total_success += h['success_rate']
                    total_signals += h['signal_count']
                    valid_stocks += 1
                else:
                    print(f"{h['symbol']:<10} ${h['last_price']:<11.2f} {h['ha_color']:<12} {h['trend_strength']:<20} "
                          f"{'N/A':<15} {'N/A':<12} {'N/A':<10}")
            
            # Overall statistics
            if valid_stocks > 0:
                avg_success_rate = total_success / valid_stocks
                print("\n" + "=" * 100)
                print("📈 OVERALL STATISTICS:")
                print(f"  • Average Success Rate: {avg_success_rate:.1f}%")
                print(f"  • Total Historical Signals Analyzed: {total_signals}")
                print(f"  • Stocks with Valid History: {valid_stocks}/{len(buy_setup_9_list)}")
                print("=" * 100)
                
                # Recommendations
                print("\n💡 INTERPRETATION:")
                print(f"  ✅ Success Rate ≥60%: High probability stocks")
                print(f"  ⚠️  Success Rate 40-60%: Moderate probability stocks")
                print(f"  ❌ Success Rate <40%: Lower probability stocks")
                print(f"  📈 Avg Gain >5%: Strong potential")
                print(f"  📊 Avg Gain 2-5%: Moderate potential")
                print(f"  📉 Avg Gain <2%: Weak potential")
        else:
            print("  Not enough historical data for analysis")
        
        print("=" * 100)
    
    # SELL SETUP 9
    print("\n🔴 SELL SETUP 9 (SELL SIGNAL) - Heiken Ashi Weekly:")
    print("-" * 100)
    if sell_setup_9_list:
        sell_setup_9_sorted = sorted(sell_setup_9_list, 
                                     key=lambda x: (x['ha_color'] == "🔴 RED", 
                                                   "INDECISIVE" in x['trend_strength'],
                                                   "MODERATE" in x['trend_strength']), 
                                     reverse=True)
        for s in sell_setup_9_sorted:
            print(f"  {s['symbol']:8s} | Price: ${s['last_price']:10.2f} | HA: {s['ha_color']} | "
                  f"Trend: {s['trend_strength']:20s} | {s['date']}")
    else:
        print("  No signals found")
    
    # OTHER SIGNALS (7-8)
    print("\n⚠️  OTHER IMPORTANT SIGNALS (7-8):")
    print("-" * 100)
    if other_signals:
        # Show first 20
        for s in other_signals[:20]:
            if s['buy_setup'] >= 7:
                print(f"  {s['symbol']:8s} | Price: ${s['last_price']:10.2f} | HA: {s['ha_color']} | "
                      f"Buy: {s['buy_setup']} | Trend: {s['trend_strength']:20s} | {s['date']}")
            if s['sell_setup'] >= 7:
                print(f"  {s['symbol']:8s} | Price: ${s['last_price']:10.2f} | HA: {s['ha_color']} | "
                      f"Sell: {s['sell_setup']} | Trend: {s['trend_strength']:20s} | {s['date']}")
        
        if len(other_signals) > 20:
            print(f"\n  ... and {len(other_signals) - 20} more signals")
    else:
        print("  No signals found")
    
    # HIGHLIGHTS - Buy Setup 9
    if buy_setup_9_list:
        print("\n" + "=" * 100)
        print("⭐ HIGHLIGHTED BUY SETUP 9 SIGNALS:")
        print("=" * 100)
        
        # Filter green HA + Indecisive/Moderate trend
        highlights = [s for s in buy_setup_9_list 
                     if s['ha_color'] == "🟢 GREEN" 
                     and ("INDECISIVE" in s['trend_strength'] or "MODERATE" in s['trend_strength'])]
        
        if highlights:
            for s in highlights[:10]:
                print(f"\n🔹 {s['symbol']} - ${s['last_price']}")
                print(f"   • HA Close: ${s['ha_close']:.2f} | HA Open: ${s['ha_open']:.2f}")
                print(f"   • Last Candle: {s['ha_color']}")
                print(f"   • Trend Status: {s['trend_strength']}")
                print(f"   ✅ POSITIVE: Ideal buy opportunity - Green HA + Weakening trend")
        else:
            print("  No ideal signals found. Review the list above.")
    
    # HIGHLIGHTS - Sell Setup 9
    if sell_setup_9_list:
        print("\n" + "=" * 100)
        print("⭐ HIGHLIGHTED SELL SETUP 9 SIGNALS:")
        print("=" * 100)
        
        highlights = [s for s in sell_setup_9_list 
                     if s['ha_color'] == "🔴 RED" 
                     and ("INDECISIVE" in s['trend_strength'] or "MODERATE" in s['trend_strength'])]
        
        if highlights:
            for s in highlights[:10]:
                print(f"\n🔹 {s['symbol']} - ${s['last_price']}")
                print(f"   • HA Close: ${s['ha_close']:.2f} | HA Open: ${s['ha_open']:.2f}")
                print(f"   • Last Candle: {s['ha_color']}")
                print(f"   • Trend Status: {s['trend_strength']}")
                print(f"   ✅ CAUTION: Ideal sell opportunity - Red HA + Weakening trend")
        else:
            print("  No ideal signals found. Review the list above.")
    
    # SUMMARY
    print("\n" + "=" * 100)
    print("📊 OVERALL SUMMARY:")
    print(f"  • Total Stocks Scanned: {total}")
    print(f"  • Buy Setup 9 Signals: {len(buy_setup_9_list)} stocks")
    print(f"  • Sell Setup 9 Signals: {len(sell_setup_9_list)} stocks")
    print(f"  • Approaching Signals (7-8): {len(other_signals)} stocks")
    print("=" * 100)
    
    print("\n💡 USAGE NOTES:")
    print("  📌 Signals are sorted by trend strength and HA candle color")
    print("  📌 HIGHLIGHTS section shows the most reliable signals")
    print("  📌 Always confirm with other technical indicators (RSI, MACD, volume)")
    print("  📌 Don't forget fundamental analysis and risk management!")
    print("=" * 100)
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{index_name.lower()}_scan_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"{index_name} STOCK SCAN RESULTS\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Stocks Scanned: {total}\n\n")
        
        f.write("BUY SETUP 9:\n")
        for s in buy_setup_9_list:
            f.write(f"{s['symbol']},{s['last_price']},{s['ha_color']},{s['trend_strength']}\n")
        
        f.write("\nSELL SETUP 9:\n")
        for s in sell_setup_9_list:
            f.write(f"{s['symbol']},{s['last_price']},{s['ha_color']},{s['trend_strength']}\n")
    
    print(f"\n✓ Results saved to '{filename}'")
    print("=" * 100)

def main():
    """
    Main function - select index to scan
    """
    print("\n" + "=" * 100)
    print("US STOCK MARKET SCANNER - TD SEQUENTIAL + HEIKEN ASHI")
    print("=" * 100)
    print("\nSelect index to scan:")
    print("  1) NASDAQ 100")
    print("  2) S&P 500 (Major Stocks)")
    print("  3) Russell 2000 (Small-Cap)")
    print("  4) All Indices (Combined)")
    print("=" * 100)
    
    choice = input("\nYour choice (1/2/3/4): ").strip()
    
    if choice == "1":
        scan_all_stocks("NASDAQ")
    elif choice == "2":
        scan_all_stocks("SP500")
    elif choice == "3":
        scan_all_stocks("RUSSELL2000")
    elif choice == "4":
        scan_all_stocks("ALL")
    else:
        print("Invalid choice. Running NASDAQ scan by default...")
        scan_all_stocks("NASDAQ")

if __name__ == "__main__":
    try:
        import yfinance
        import pandas
    except ImportError:
        print("Installing required libraries...")
        print("Please run: pip install yfinance pandas")
        exit(1)
    
    main()