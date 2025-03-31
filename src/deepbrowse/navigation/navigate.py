from typing import Dict, Optional, Union, List
import aiohttp
import asyncio
from urllib.parse import urlparse, urljoin


class BrowserClient:
    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = 30):
        """
        Initialize the browser client for making HTTP requests.

        Args:
            headers: Optional custom headers for requests
            timeout: Request timeout in seconds
        """
        self.session = None
        self.default_headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        self.timeout = timeout
        self.history = []

    async def __aenter__(self):
        """Initialize the aiohttp session when used as a context manager."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.default_headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the aiohttp session when exiting the context."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get(self, url: str, params: Optional[Dict] = None) -> str:
        """
        Make a GET request to the specified URL.

        Args:
            url: The URL to request
            params: Optional query parameters

        Returns:
            The response HTML as a string
        """
        # Initialize session if not exists
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.default_headers)

        try:
            async with self.session.get(
                url, params=params, timeout=self.timeout
            ) as response:
                # Record this visit in history
                self.history.append(
                    {
                        "url": url,
                        "status": response.status,
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )

                # Raise for 4xx/5xx status codes
                response.raise_for_status()

                # Return the HTML content
                return await response.text()

        except aiohttp.ClientError as e:
            # Handle and re-raise HTTP errors
            error_msg = f"Error fetching {url}: {str(e)}"
            raise Exception(error_msg)

    async def post(
        self, url: str, data: Optional[Dict] = None, json: Optional[Dict] = None
    ) -> str:
        """
        Make a POST request to the specified URL.

        Args:
            url: The URL to request
            data: Optional form data
            json: Optional JSON data

        Returns:
            The response HTML as a string
        """
        # Initialize session if not exists
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.default_headers)

        try:
            async with self.session.post(
                url, data=data, json=json, timeout=self.timeout
            ) as response:
                # Record this visit in history
                self.history.append(
                    {
                        "url": url,
                        "method": "POST",
                        "status": response.status,
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )

                # Raise for 4xx/5xx status codes
                response.raise_for_status()

                # Return the HTML content
                return await response.text()

        except aiohttp.ClientError as e:
            # Handle and re-raise HTTP errors
            error_msg = f"Error posting to {url}: {str(e)}"
            raise Exception(error_msg)

    def get_current_url(self) -> Optional[str]:
        """Get the current URL (the last one visited)."""
        if not self.history:
            return None
        return self.history[-1]["url"]

    def get_history(self) -> List[Dict]:
        """Get the browsing history."""
        return self.history

    def resolve_url(self, base_url: str, relative_url: str) -> str:
        """
        Resolve a relative URL against a base URL.

        Args:
            base_url: The base URL
            relative_url: The relative URL to resolve

        Returns:
            The resolved absolute URL
        """
        return urljoin(base_url, relative_url)

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
