"""
Fixed universe: 30 large-cap US equities across sectors.

This is a deliberate scope choice, not a placeholder — the project targets
a fixed, curated list of liquid US equities with clean, freely available
daily history, rather than an open-ended ticker search across asset classes.
"""

UNIVERSE = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "sector": "Technology"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financials"},
    {"symbol": "V", "name": "Visa Inc.", "sector": "Financials"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Staples"},
    {"symbol": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Staples"},
    {"symbol": "MA", "name": "Mastercard Inc.", "sector": "Financials"},
    {"symbol": "HD", "name": "Home Depot Inc.", "sector": "Consumer Discretionary"},
    {"symbol": "DIS", "name": "Walt Disney Co.", "sector": "Communication Services"},
    {"symbol": "BAC", "name": "Bank of America Corp.", "sector": "Financials"},
    {"symbol": "XOM", "name": "Exxon Mobil Corp.", "sector": "Energy"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
    {"symbol": "KO", "name": "Coca-Cola Co.", "sector": "Consumer Staples"},
    {"symbol": "PEP", "name": "PepsiCo Inc.", "sector": "Consumer Staples"},
    {"symbol": "CSCO", "name": "Cisco Systems Inc.", "sector": "Technology"},
    {"symbol": "INTC", "name": "Intel Corp.", "sector": "Technology"},
    {"symbol": "VZ", "name": "Verizon Communications Inc.", "sector": "Communication Services"},
    {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services"},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology"},
    {"symbol": "ABT", "name": "Abbott Laboratories", "sector": "Healthcare"},
    {"symbol": "MRK", "name": "Merck & Co. Inc.", "sector": "Healthcare"},
    {"symbol": "T", "name": "AT&T Inc.", "sector": "Communication Services"},
    {"symbol": "NKE", "name": "Nike Inc.", "sector": "Consumer Discretionary"},
]

UNIVERSE_SYMBOLS = {t["symbol"] for t in UNIVERSE}
