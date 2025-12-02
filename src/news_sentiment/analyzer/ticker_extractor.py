"""
Ticker Symbol Extraction from Text.

This module extracts stock tickers, crypto symbols, and forex pairs
from Reddit posts and other text content.
"""

import re
from typing import Dict, List, Set

# Common stock tickers that are also English words (avoid false positives)
COMMON_WORDS = {
    "A", "I", "AM", "PM", "AN", "AS", "AT", "BE", "BY", "DO", "GO", "HE",
    "IF", "IN", "IS", "IT", "ME", "MY", "NO", "OF", "OK", "ON", "OR", "SO",
    "TO", "UP", "US", "WE", "ALL", "AND", "ARE", "BIG", "BUT", "CAN", "CEO",
    "DAY", "DD", "DIP", "ETF", "FOR", "GET", "GOT", "HAS", "HIM", "HIS",
    "HOW", "IRA", "IPO", "ITS", "LET", "LOT", "LOW", "MAN", "MAY", "NEW",
    "NOT", "NOW", "OLD", "ONE", "OUR", "OUT", "OWN", "PUT", "RUN", "SAY",
    "SEE", "SHE", "THE", "TOP", "TRY", "TWO", "WAY", "WHO", "WHY", "WIN",
    "WON", "YET", "YOU", "ATH", "ATL", "AVG", "BUY", "EPS", "FED", "GDP",
    "IMO", "LOL", "P&L", "P/E", "QE", "ROI", "SEC", "USA", "USD", "YTD",
    "YOLO", "HODL", "FOMO", "FUD", "TLDR", "EDIT", "LINK", "FREE", "JUST",
    "LIKE", "LONG", "MUCH", "NEXT", "ONLY", "OVER", "SOME", "STOP", "THAN",
    "THAT", "THEM", "THEN", "THIS", "VERY", "WANT", "WHAT", "WHEN", "WITH",
    "WORK", "YEAR", "YOUR", "BEEN", "CALL", "CASH", "DOWN", "EVEN", "EVER",
    "GOOD", "HAVE", "HERE", "HIGH", "HOLD", "LAST", "LESS", "LOOK", "LOSS",
    "MADE", "MAKE", "MORE", "MOST", "MOVE", "MUST", "NEED", "SELL", "TAKE",
    "TIME", "WILL", "WERE", "BEST", "GAIN", "PUTS", "CALLS", "SHORT",
}

# Popular stock tickers to always recognize (even without $)
POPULAR_TICKERS = {
    # Mega caps
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "BRK",
    "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC",
    # Tech
    "AMD", "INTC", "CRM", "ADBE", "NFLX", "PYPL", "SQ", "SHOP", "UBER",
    "LYFT", "SNAP", "TWTR", "PINS", "ZM", "DOCU", "CRWD", "NET", "PLTR",
    "SNOW", "COIN", "HOOD", "SOFI", "RIVN", "LCID", "NIO", "XPEV",
    # Meme stocks
    "GME", "AMC", "BB", "BBBY", "WISH", "CLOV", "SPCE", "PLTR",
    # ETFs
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VXX", "ARKK", "SQQQ", "TQQQ",
    # Crypto-related
    "MSTR", "MARA", "RIOT", "HUT", "BITF", "GBTC", "ETHE",
}

# Cryptocurrency symbols
CRYPTO_SYMBOLS = {
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "SHIB", "DOT", "AVAX",
    "MATIC", "LINK", "UNI", "ATOM", "LTC", "BCH", "XLM", "ALGO", "VET",
    "FIL", "AAVE", "EOS", "XTZ", "THETA", "AXS", "SAND", "MANA", "ENJ",
    "NEAR", "FTM", "ONE", "HBAR", "EGLD", "FLOW", "KSM", "CAKE", "RUNE",
    "ZEC", "DASH", "COMP", "MKR", "SNX", "YFI", "SUSHI", "CRV", "BAT",
    "PEPE", "BONK", "WIF", "FLOKI",
}

# Forex pairs (major and minor)
FOREX_PAIRS = {
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURAUD", "EURCHF", "GBPCHF",
    "AUDCAD", "CADJPY", "NZDJPY", "AUDNZD", "EURNZD", "GBPAUD", "GBPCAD",
}


def extract_tickers(text: str) -> List[str]:
    """Extract ticker symbols from text.

    Identifies:
    - Cashtag format: $AAPL, $NVDA
    - Popular tickers without cashtag: NVDA, TSLA
    - Crypto symbols: BTC, ETH
    - Forex pairs: EURUSD, GBPUSD

    Args:
        text: Text content to analyze

    Returns:
        List of unique ticker symbols found, sorted alphabetically
    """
    if not text:
        return []

    found_tickers: Set[str] = set()

    # Pattern 1: Cashtag format ($AAPL, $nvda)
    cashtag_pattern = r"\$([A-Za-z]{1,5})\b"
    for match in re.finditer(cashtag_pattern, text):
        ticker = match.group(1).upper()
        if ticker not in COMMON_WORDS and len(ticker) >= 1:
            found_tickers.add(ticker)

    # Pattern 2: Standalone uppercase tickers (NVDA, AAPL)
    # Must be 2-5 chars, all caps, word boundary
    standalone_pattern = r"\b([A-Z]{2,5})\b"
    for match in re.finditer(standalone_pattern, text):
        ticker = match.group(1)
        # Only add if it's a known ticker or crypto
        if ticker in POPULAR_TICKERS or ticker in CRYPTO_SYMBOLS:
            found_tickers.add(ticker)

    # Pattern 3: Forex pairs (EUR/USD, EURUSD)
    forex_pattern = r"\b([A-Z]{3})[/]?([A-Z]{3})\b"
    for match in re.finditer(forex_pattern, text):
        pair = match.group(1) + match.group(2)
        if pair in FOREX_PAIRS:
            found_tickers.add(pair)

    # Pattern 4: Crypto with common suffixes (BTC-USD, ETH/USDT)
    crypto_pattern = r"\b(BTC|ETH|SOL|XRP|DOGE|ADA)[-/]?(USD|USDT|USDC)?\b"
    for match in re.finditer(crypto_pattern, text, re.IGNORECASE):
        ticker = match.group(1).upper()
        found_tickers.add(ticker)

    return sorted(list(found_tickers))


def extract_tickers_with_context(text: str) -> Dict[str, str]:
    """Extract tickers with surrounding context.

    Useful for determining sentiment per symbol.

    Args:
        text: Text content to analyze

    Returns:
        Dictionary mapping ticker to surrounding context (50 chars each side)
    """
    if not text:
        return {}

    results: Dict[str, str] = {}
    tickers = extract_tickers(text)

    for ticker in tickers:
        # Find all occurrences and get context
        patterns = [
            rf"\${ticker}\b",  # Cashtag
            rf"\b{ticker}\b",  # Standalone
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                # Store first context found for each ticker
                if ticker not in results:
                    results[ticker] = context
                break

    return results


def categorize_symbol(symbol: str) -> str:
    """Categorize a symbol as stock, crypto, or forex.

    Args:
        symbol: The ticker symbol

    Returns:
        Category string: 'stock', 'crypto', or 'forex'
    """
    if symbol in CRYPTO_SYMBOLS:
        return "crypto"
    elif symbol in FOREX_PAIRS or len(symbol) == 6:
        return "forex"
    else:
        return "stock"
