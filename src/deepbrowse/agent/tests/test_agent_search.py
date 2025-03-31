"""
Tests for the Google search functionality in the agent module.

These tests verify that the search_google function correctly extracts
and processes search results from Google.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Import the BrowsingAgent to access the search_google function
from src.deepbrowse.agent.agent import BrowsingAgent


class TestAgentSearch:
    """Test suite for agent search functions."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.agent = BrowsingAgent()
        # Mock browser client and parser for use in tool setup
        self.mock_browser_client = MagicMock()
        self.mock_parser = MagicMock()
        # Set up tools to access search_google function
        self.agent._setup_tools(self.mock_browser_client, self.mock_parser)
        # Find the search_google tool
        self.search_google_tool = next(
            tool for tool in self.agent.tools if tool.name == "search_google"
        )
        self.search_google_func = self.search_google_tool.func

    def test_search_google_existence(self):
        """Test that the search_google tool exists and is callable."""
        assert self.search_google_tool is not None
        assert callable(self.search_google_func)

    @pytest.mark.asyncio
    async def test_search_google_extraction(self, monkeypatch, google_search_html):
        """Test that search_google correctly extracts links from Google search results."""
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

        # Call the search_google function
        result = self.search_google_func("test query")

        # Verify the results contain the expected content
        assert "Google Search Results" in result
        assert "First Result" in result or "iPhone 15 Pro battery life" in result

    def test_search_google_error_handling(self, monkeypatch):
        """Test that search_google properly handles errors."""
        # Setup mock browser client's get method to raise an exception
        self.mock_browser_client.get = AsyncMock(side_effect=Exception("Search error"))

        # Patch the event loop creation to avoid thread issues
        mock_loop = MagicMock()
        mock_loop.run_until_complete = MagicMock(side_effect=Exception("Search error"))
        monkeypatch.setattr(
            asyncio, "get_event_loop", MagicMock(return_value=mock_loop)
        )

        # Call search_google and check that it returns an error message
        result = self.search_google_func("test query")
        assert "Error" in result
        assert "Search error" in result
