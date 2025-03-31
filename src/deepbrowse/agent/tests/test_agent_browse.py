"""
Tests for the website browsing functionality in the agent module.

These tests verify that the browse_website function correctly extracts
and processes web page content, including handling different types of pages.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp
import re

# Import the BrowsingAgent to access the browse_website function
from src.deepbrowse.agent.agent import BrowsingAgent


class TestAgentBrowse:
    """Test suite for agent browsing functions."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.agent = BrowsingAgent()
        # Mock browser client and parser for use in tool setup
        self.mock_browser_client = MagicMock()
        self.mock_parser = MagicMock()
        # Set up tools to access browse_website function
        self.agent._setup_tools(self.mock_browser_client, self.mock_parser)
        # Find the browse_website tool
        self.browse_website_tool = next(
            tool for tool in self.agent.tools if tool.name == "browse_website"
        )
        self.browse_website_func = self.browse_website_tool.func

    def test_browse_website_existence(self):
        """Test that the browse_website tool exists and is callable."""
        assert self.browse_website_tool is not None
        assert callable(self.browse_website_func)

    @pytest.mark.asyncio
    async def test_browse_website_basic(self, monkeypatch):
        """Test basic browsing functionality with a simple HTML page."""
        test_html = (
            "<html><body><h1>Test Page</h1><p>This is a test page.</p></body></html>"
        )

        # Setup mock browser client's get method to return test_html
        self.mock_browser_client.get = AsyncMock(return_value=test_html)

        # Create a mock event loop
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=lambda x: test_html)
        monkeypatch.setattr(
            asyncio, "get_event_loop", MagicMock(return_value=mock_loop)
        )

        # Call the browse_website function
        result = self.browse_website_func("https://example.com")

        # Verify it contains the expected content
        assert "<h1>Unknown Title</h1>" in result
        assert "This is a test page" in result

    @pytest.mark.asyncio
    async def test_browse_website_product_page(self, monkeypatch, product_page_html):
        """Test browsing functionality with a product page containing battery information."""
        # Setup mock browser client's get method to return product_page_html
        self.mock_browser_client.get = AsyncMock(return_value=product_page_html)

        # Create a mock event loop
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(
            side_effect=lambda x: product_page_html
        )
        monkeypatch.setattr(
            asyncio, "get_event_loop", MagicMock(return_value=mock_loop)
        )

        # Call the browse_website function with a URL that looks like an iPhone product page
        result = self.browse_website_func("https://example.com/iphone-15-pro")

        # Verify it extracts the battery information
        assert "Extracted Product Information" in result or "iPhone 15 Pro" in result
        assert "Battery" in result.lower() or "battery" in result.lower()
        assert "23 hours" in result or "video playback" in result

    @pytest.mark.asyncio
    async def test_browse_website_search_page(self, monkeypatch, google_search_html):
        """Test browsing functionality with a Google search results page."""
        # Setup mock browser client's get method to return google_search_html
        self.mock_browser_client.get = AsyncMock(return_value=google_search_html)

        # Create a mock event loop
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(
            side_effect=lambda x: google_search_html
        )
        monkeypatch.setattr(
            asyncio, "get_event_loop", MagicMock(return_value=mock_loop)
        )

        # Call the browse_website function with a Google search URL
        result = self.browse_website_func("https://www.google.com/search?q=test")

        # Verify it extracts the search results
        assert "Google Search Results" in result
        assert "iPhone 15 Pro battery life" in result or "First Result" in result

    def test_browse_website_error_handling(self, monkeypatch):
        """Test that browse_website properly handles errors."""
        # Setup mock browser client's get method to raise an exception
        self.mock_browser_client.get = AsyncMock(
            side_effect=Exception("Connection error")
        )

        # Patch the event loop creation to avoid thread issues
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(
            side_effect=Exception("Connection error")
        )
        monkeypatch.setattr(
            asyncio, "get_event_loop", MagicMock(return_value=mock_loop)
        )

        # Call browse_website and check that it returns an error message
        result = self.browse_website_func("https://example.com/error")
        assert "Error" in result
        assert "Connection error" in result
