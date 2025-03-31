"""
Tests for the DeepBrowser class.

These tests verify that the DeepBrowser correctly integrates the agent,
navigation, and parser components.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import os

from src.deepbrowse.browser.browser import DeepBrowser


class TestDeepBrowser:
    """Test suite for DeepBrowser."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Set test API key for testing
        os.environ["OPENAI_API_KEY"] = "test-api-key"
        self.api_key = "test-api-key"

    @pytest.mark.asyncio
    async def test_init(self):
        """Test DeepBrowser initialization."""
        browser = DeepBrowser(api_key=self.api_key)
        # The api_key is passed to the agent but not stored directly
        assert browser.agent is not None
        assert browser.browser_client is not None
        assert browser.parser is not None
        # Clean up resources
        await browser.browser_client.close()

    @pytest.mark.asyncio
    @patch("deepbrowse.agent.agent.BrowsingAgent.execute_browsing_session")
    async def test_ask_method(self, mock_execute_session):
        """Test the ask method with a mocked execute_browsing_session."""
        # Set up the mock return value
        mock_execute_session.return_value = {
            "collected_data": [
                {
                    "url": "https://example.com",
                    "title": "Test Page",
                    "content": "Test content",
                    "metadata": {"source": "test"},
                }
            ],
            "pages_visited": [
                {
                    "url": "https://example.com",
                    "title": "Test Page",
                    "timestamp": 1234567890,
                }
            ],
        }

        # Initialize the browser
        browser = DeepBrowser(api_key=self.api_key)

        # Test the ask method
        result = await browser.ask("test query", time_limit=10)

        # Verify the agent's execute_browsing_session was called with the correct parameters
        mock_execute_session.assert_called_once()
        call_args = mock_execute_session.call_args[1]  # Get the keyword arguments
        assert call_args["prompt"] == "test query"
        assert call_args["time_limit"] == 10
        assert call_args["browser_client"] is browser.browser_client
        assert call_args["parser"] is browser.parser

        # Verify the result contains the expected fields
        assert "data_collected" in result
        assert "pages_visited" in result
        assert len(result["data_collected"]) == 1
        assert len(result["pages_visited"]) == 1
        assert result["data_collected"][0]["url"] == "https://example.com"
        assert result["completed"] is True

        # Verify the summary was stored
        summary = browser.get_summary()
        assert summary is not None

        await browser.browser_client.close()

    @pytest.mark.asyncio
    @patch("deepbrowse.agent.agent.BrowsingAgent.execute_browsing_session")
    async def test_search_integration(self, mock_execute_session):
        """Test that the DeepBrowser integrates with Google search functionality."""
        # Create a search result with the expected format
        mock_execute_session.return_value = {
            "collected_data": [
                {
                    "url": "google_search",
                    "title": "Search Results",
                    "content": "<html><body><h1>Google Search Results</h1><ul><li><a href='https://example.com/result1'>Result 1</a></li></ul></body></html>",
                    "metadata": {"source": "google"},
                }
            ],
            "pages_visited": [
                {
                    "url": "https://www.google.com/search?q=test",
                    "title": "Google Search: test",
                    "timestamp": 1234567890,
                }
            ],
        }

        # Initialize the browser
        browser = DeepBrowser(api_key=self.api_key)

        # Test the ask method with a search query
        result = await browser.ask("search for test information", time_limit=10)

        # Verify the execute_browsing_session was called
        mock_execute_session.assert_called_once()

        # Verify the result contains the expected data
        assert "data_collected" in result
        assert "pages_visited" in result
        assert len(result["pages_visited"]) == 1
        assert "google.com/search" in result["pages_visited"][0]["url"]
        assert "Google Search Results" in result["data_collected"][0]["content"]

        await browser.browser_client.close()

    @pytest.mark.asyncio
    @patch("deepbrowse.agent.agent.BrowsingAgent.execute_browsing_session")
    async def test_browser_error_handling(self, mock_execute_session):
        """Test that DeepBrowser properly handles errors in the agent."""
        # Set the mock to raise an exception
        mock_execute_session.side_effect = Exception("Test error")

        # Create a browser
        browser = DeepBrowser(api_key=self.api_key)

        # Test the ask method with an error
        result = await browser.ask("error query", time_limit=5)

        # Verify the result contains an error field
        assert "error" in result
        assert "Test error" in result["error"]

        await browser.browser_client.close()
