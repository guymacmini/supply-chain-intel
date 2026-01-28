"""Tavily API client for enhanced web search."""

import os
from typing import Optional
import logging

try:
    from tavily import TavilyClient as TavilySDK
except ImportError:
    TavilySDK = None

logger = logging.getLogger(__name__)


class TavilyClient:
    """Client for enhanced web search using Tavily API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client.

        Args:
            api_key: Tavily API key. If not provided, reads from TAVILY_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.client = None

        if self.api_key and TavilySDK:
            try:
                self.client = TavilySDK(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Tavily client: {e}")
                self.client = None
        elif not TavilySDK:
            logger.debug("tavily-python library not installed")

    def is_available(self) -> bool:
        """Check if Tavily client is available and configured."""
        return self.client is not None

    def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 10,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None
    ) -> Optional[dict]:
        """
        Perform a web search using Tavily.

        Args:
            query: Search query
            search_depth: "basic" or "advanced" (default: "advanced")
            max_results: Maximum number of results to return (default: 10)
            include_domains: List of domains to include in results
            exclude_domains: List of domains to exclude from results

        Returns:
            dict with search results or None if unavailable:
            {
                'query': str,
                'results': [
                    {
                        'title': str,
                        'url': str,
                        'content': str,
                        'score': float
                    },
                    ...
                ]
            }
        """
        if not self.is_available():
            return None

        try:
            kwargs = {
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results
            }

            if include_domains:
                kwargs["include_domains"] = include_domains
            if exclude_domains:
                kwargs["exclude_domains"] = exclude_domains

            response = self.client.search(**kwargs)
            return response

        except Exception as e:
            logger.warning(f"Failed to perform Tavily search for '{query}': {e}")
            return None

    def search_financial_news(
        self,
        query: str,
        max_results: int = 10
    ) -> Optional[dict]:
        """
        Search for financial news and analysis.

        Args:
            query: Search query
            max_results: Maximum number of results (default: 10)

        Returns:
            dict with search results or None if unavailable
        """
        # Focus on financial news sources
        financial_domains = [
            "bloomberg.com",
            "reuters.com",
            "wsj.com",
            "ft.com",
            "cnbc.com",
            "marketwatch.com",
            "seekingalpha.com",
            "fool.com",
            "investopedia.com",
            "yahoo.com/finance"
        ]

        return self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=financial_domains
        )

    def search_company_info(
        self,
        company_name: str,
        max_results: int = 5
    ) -> Optional[dict]:
        """
        Search for company information.

        Args:
            company_name: Name or ticker of the company
            max_results: Maximum number of results (default: 5)

        Returns:
            dict with search results or None if unavailable
        """
        query = f"{company_name} company profile investor relations"
        return self.search(
            query=query,
            search_depth="advanced",
            max_results=max_results
        )

    def format_results_as_text(self, results: Optional[dict]) -> str:
        """
        Format Tavily search results as readable text.

        Args:
            results: Results dict from Tavily search

        Returns:
            Formatted string with search results
        """
        if not results or 'results' not in results:
            return ""

        formatted = []
        for i, result in enumerate(results['results'], 1):
            formatted.append(f"\n{i}. {result.get('title', 'No title')}")
            formatted.append(f"   URL: {result.get('url', '')}")
            content = result.get('content', '')
            if content:
                # Truncate long content
                if len(content) > 300:
                    content = content[:300] + "..."
                formatted.append(f"   {content}")

        return "\n".join(formatted)
