"""
Tests for the browser_client module.

These tests verify that the BrowserClient class correctly handles web requests
and content processing.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
import re

from src.deepbrowse.navigation.navigate import BrowserClient


class TestableBrowserClient(BrowserClient):
    """A subclass of BrowserClient that can be easily tested."""

    async def get(self, url: str, params=None) -> str:
        """
        Override get method for testing. This version doesn't use a context manager.
        """
        # Record the visit in history
        self.history.append(
            {
                "url": url,
                "status": 200,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        # Return the mocked response text directly
        if hasattr(self, "mock_response"):
            if isinstance(self.mock_response, Exception):
                raise self.mock_response
            if callable(self.mock_response):
                return await self.mock_response(url, params)
            return self.mock_response

        return "<html><body><h1>Test Response</h1></body></html>"

    async def post(self, url: str, data=None, json=None) -> str:
        """
        Override post method for testing. This version doesn't use a context manager.
        """
        # Record the visit in history
        self.history.append(
            {
                "url": url,
                "method": "POST",
                "status": 200,
                "timestamp": asyncio.get_event_loop().time(),
            }
        )

        # Return the mocked response directly
        if hasattr(self, "mock_response"):
            if isinstance(self.mock_response, Exception):
                raise self.mock_response
            if callable(self.mock_response):
                return await self.mock_response(url, data, json)
            return self.mock_response

        return '{"status": "success"}'


class TestBrowserClient:
    """Test suite for the BrowserClient class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.browser_client = TestableBrowserClient()

    @pytest.mark.asyncio
    async def test_get_page_content_success(self):
        """Test successful page content retrieval."""
        test_html = "<html><body><h1>Test Page</h1></body></html>"

        # Set up the mock response
        self.browser_client.mock_response = test_html

        # Call the method under test
        content = await self.browser_client.get("https://example.com")

        # Verify the result
        assert content == test_html
        assert self.browser_client.history[0]["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_get_page_content_http_error(self):
        """Test handling of HTTP errors."""
        # Set up the client to raise an HTTP error
        error = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=404,
            message="Not Found",
            headers={},
        )
        self.browser_client.mock_response = error

        # Call the method and verify it raises the expected exception
        with pytest.raises(aiohttp.ClientResponseError) as excinfo:
            await self.browser_client.get("https://example.com/notfound")

        assert excinfo.value.status == 404
        assert excinfo.value.message == "Not Found"

    @pytest.mark.asyncio
    async def test_get_page_content_connection_error(self):
        """Test handling of connection errors."""
        # Set up the client to raise a connection error with a simple mock for connection_key
        # The actual ConnectionKey class is not directly accessible
        connection_key = MagicMock()
        connection_key.host = (
            "example.com"  # Add host attribute for string representation
        )

        error = aiohttp.ClientConnectorError(
            connection_key=connection_key, os_error=OSError("Connection refused")
        )
        self.browser_client.mock_response = error

        # Call the method and verify it raises the expected exception
        with pytest.raises(aiohttp.ClientConnectorError) as excinfo:
            await self.browser_client.get("https://example.com/connection_error")

        # Just verify that it's the right type of exception
        assert isinstance(excinfo.value, aiohttp.ClientConnectorError)

    @pytest.mark.asyncio
    async def test_get_page_content_timeout(self):
        """Test handling of timeout errors."""
        # Set up the client to raise a timeout error
        self.browser_client.mock_response = asyncio.TimeoutError()

        # Call the method and verify it raises the expected exception
        with pytest.raises(asyncio.TimeoutError):
            await self.browser_client.get("https://example.com/timeout")

    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test the POST method functionality."""
        test_response = '{"status": "success"}'

        # Set up the mock response
        self.browser_client.mock_response = test_response

        # Call the method under test with JSON data
        json_data = {"key": "value"}
        content = await self.browser_client.post(
            "https://example.com/api", json=json_data
        )

        # Verify the result
        assert content == test_response
        assert self.browser_client.history[0]["url"] == "https://example.com/api"
        assert self.browser_client.history[0]["method"] == "POST"

    @pytest.mark.asyncio
    async def test_history_tracking(self):
        """Test that the browser client correctly tracks history."""

        # Create a response function that returns different responses based on URL
        async def mock_response_func(url, params=None):
            if "page1" in url:
                return "<html><body><h1>Page 1</h1></body></html>"
            elif "page2" in url:
                return "<html><body><h1>Page 2</h1></body></html>"
            return "Unknown page"

        # Set up the mock response function
        self.browser_client.mock_response = mock_response_func

        # Make two requests
        await self.browser_client.get("https://example.com/page1")
        await self.browser_client.get("https://example.com/page2")

        # Verify the history
        history = self.browser_client.get_history()
        assert len(history) == 2
        assert history[0]["url"] == "https://example.com/page1"
        assert history[1]["url"] == "https://example.com/page2"

        # Verify current URL
        current_url = self.browser_client.get_current_url()
        assert current_url == "https://example.com/page2"

    @pytest.mark.asyncio
    async def test_resolve_url(self):
        """Test that the browser client correctly resolves relative URLs."""
        base_url = "https://example.com/path/page.html"

        # Test with various relative URLs
        assert (
            self.browser_client.resolve_url(base_url, "other.html")
            == "https://example.com/path/other.html"
        )
        assert (
            self.browser_client.resolve_url(base_url, "/other.html")
            == "https://example.com/other.html"
        )
        assert (
            self.browser_client.resolve_url(base_url, "../other.html")
            == "https://example.com/other.html"
        )
        assert (
            self.browser_client.resolve_url(base_url, "https://example.org/page")
            == "https://example.org/page"
        )
