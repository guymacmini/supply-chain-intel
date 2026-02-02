"""Finnhub API client for fetching market data."""

import os
from typing import Optional
import logging

try:
    import finnhub
except ImportError:
    finnhub = None

logger = logging.getLogger(__name__)


class FinnhubClient:
    """Client for fetching market data from Finnhub API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Finnhub client.

        Args:
            api_key: Finnhub API key. If not provided, reads from FINNHUB_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self.client = None

        if self.api_key and finnhub:
            try:
                self.client = finnhub.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Finnhub client: {e}")
                self.client = None
        elif not finnhub:
            logger.debug("finnhub-python library not installed")

    def is_available(self) -> bool:
        """Check if Finnhub client is available and configured."""
        return self.client is not None

    def get_quote(self, ticker: str) -> Optional[dict]:
        """
        Get current price quote for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            dict with quote data or None if unavailable:
            {
                'c': current_price,
                'h': day_high,
                'l': day_low,
                'o': day_open,
                'pc': previous_close
            }
        """
        if not self.is_available():
            return None

        try:
            return self.client.quote(ticker)
        except Exception as e:
            logger.warning(f"Failed to fetch quote for {ticker}: {e}")
            return None

    def get_company_profile(self, ticker: str) -> Optional[dict]:
        """
        Get company profile including market cap, exchange, etc.

        Args:
            ticker: Stock ticker symbol

        Returns:
            dict with company profile or None if unavailable
        """
        if not self.is_available():
            return None

        try:
            profile = self.client.company_profile2(symbol=ticker)
            return profile if profile else None
        except Exception as e:
            logger.warning(f"Failed to fetch profile for {ticker}: {e}")
            return None

    def get_basic_financials(self, ticker: str) -> Optional[dict]:
        """
        Get basic financial metrics including P/E ratio, 52-week high/low.

        Args:
            ticker: Stock ticker symbol

        Returns:
            dict with financial metrics or None if unavailable:
            {
                'metric': {
                    '52WeekHigh': value,
                    '52WeekLow': value,
                    'peBasicExclExtraTTM': pe_ratio,
                    ...
                }
            }
        """
        if not self.is_available():
            return None

        try:
            return self.client.company_basic_financials(ticker, 'all')
        except Exception as e:
            logger.warning(f"Failed to fetch financials for {ticker}: {e}")
            return None

    def get_market_data(self, ticker: str) -> Optional[dict]:
        """
        Get comprehensive market data for a ticker.

        Combines quote, profile, and financials into a single dict.

        Args:
            ticker: Stock ticker symbol

        Returns:
            dict with market data or None if unavailable:
            {
                'ticker': str,
                'current_price': float,
                '52_week_high': float,
                '52_week_low': float,
                'pe_ratio': float,
                'market_cap': float (in millions),
                'market_cap_tier': str (mega/large/mid/small/micro),
                'exchange': str,
                'sector': str (GICS sector),
                'industry': str (GICS industry),
                'country': str (HQ country),
                'revenue_ttm': float (millions),
                'revenue_growth': float (YoY %),
                'eps_ttm': float
            }
        """
        if not self.is_available():
            return None

        try:
            # Fetch all data
            quote = self.get_quote(ticker)
            profile = self.get_company_profile(ticker)
            financials = self.get_basic_financials(ticker)

            if not quote:
                return None

            # Build response
            result = {
                'ticker': ticker,
                'current_price': quote.get('c'),
                '52_week_high': None,
                '52_week_low': None,
                'pe_ratio': None,
                'market_cap': None,
                'market_cap_tier': None,
                'exchange': None,
                'sector': None,
                'industry': None,
                'country': None,
                'revenue_ttm': None,
                'revenue_growth': None,
                'eps_ttm': None
            }

            # Add profile data
            if profile:
                market_cap = profile.get('marketCapitalization')
                result['market_cap'] = market_cap
                result['exchange'] = profile.get('exchange')
                result['sector'] = profile.get('finnhubIndustry')  # GICS sector
                result['industry'] = profile.get('gind')  # GICS industry
                result['country'] = profile.get('country')
                
                # Calculate market cap tier
                if market_cap:
                    result['market_cap_tier'] = self._classify_market_cap_tier(market_cap)

            # Add financial metrics
            if financials and 'metric' in financials:
                metrics = financials['metric']
                result['52_week_high'] = metrics.get('52WeekHigh')
                result['52_week_low'] = metrics.get('52WeekLow')
                result['pe_ratio'] = metrics.get('peBasicExclExtraTTM')
                result['revenue_ttm'] = metrics.get('revenueTTM')
                result['revenue_growth'] = metrics.get('revenueGrowthTTMYoy')
                result['eps_ttm'] = metrics.get('epsBasicExclExtraTTM')

            return result

        except Exception as e:
            logger.warning(f"Failed to fetch market data for {ticker}: {e}")
            return None

    def _classify_market_cap_tier(self, market_cap_millions: float) -> str:
        """
        Classify market cap into tiers.
        
        Args:
            market_cap_millions: Market cap in millions USD
            
        Returns:
            Market cap tier classification
        """
        if market_cap_millions >= 200000:  # $200B+
            return "mega"
        elif market_cap_millions >= 10000:  # $10B-$200B
            return "large"
        elif market_cap_millions >= 2000:   # $2B-$10B
            return "mid"
        elif market_cap_millions >= 300:    # $300M-$2B
            return "small"
        else:                              # <$300M
            return "micro"

    def get_market_data_for_tickers(self, tickers: list[str]) -> dict[str, dict]:
        """
        Get market data for multiple tickers.

        Args:
            tickers: List of stock ticker symbols

        Returns:
            dict mapping ticker to market data dict
        """
        if not self.is_available():
            return {}

        results = {}
        for ticker in tickers:
            data = self.get_market_data(ticker)
            if data:
                results[ticker] = data

        return results
