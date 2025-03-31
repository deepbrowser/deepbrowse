"""
Tests for the BrowserClient in the navigation module.

These tests verify that the BrowserClient correctly handles HTTP requests.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import aiohttp

from src.deepbrowse.navigation.navigate import BrowserClient


class TestBrowserClient:
    """Test suite for BrowserClient."""

    @pytest.mark.asyncio
    async def test_init(self):
        """Test BrowserClient initialization."""
        client = BrowserClient()
        assert client.default_headers is not None
        assert "User-Agent" in client.default_headers
        assert client.timeout == 30
        assert client.session is None
        assert isinstance(client.history, list)

        # No need to close the session since it's None, but this shouldn't raise an error
        await client.close()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test BrowserClient as a context manager."""
        async with BrowserClient() as client:
            assert client.session is not None
            assert not client.session.closed
        # Client should be closed after exiting the context manager

    @pytest.mark.asyncio
    async def test_get_request(self, monkeypatch):
        """Test the get method."""
        # Mock aiohttp.ClientSession
        mock_session = MagicMock()
        mock_session.closed = False
        # Make sure the close method is an AsyncMock
        mock_session.close = AsyncMock()

        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><body>Test</body></html>")
        mock_response.raise_for_status = MagicMock()

        # Context manager for session.get
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        # Set up the get method to return our mock context
        mock_session.get = MagicMock(return_value=mock_context)

        # Create a client and patch its session
        client = BrowserClient()
        client.session = mock_session

        # Call the get method and check the result
        result = await client.get("https://example.com")
        assert result == "<html><body>Test</body></html>"

        # Verify the mock was called with the expected arguments
        mock_session.get.assert_called_once()
        args, kwargs = mock_session.get.call_args
        assert args[0] == "https://example.com"
        assert "timeout" in kwargs

        # Check that the history was updated
        assert len(client.history) == 1
        assert client.history[0]["url"] == "https://example.com"
        assert client.history[0]["status"] == 200

        await client.close()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_request_error(self, monkeypatch):
        """Test error handling in the get method."""
        # Mock aiohttp.ClientSession
        mock_session = MagicMock()
        mock_session.closed = False
        # Make sure the close method is an AsyncMock
        mock_session.close = AsyncMock()

        # Make the get method raise an error
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Test error"))

        # Create a client and patch its session
        client = BrowserClient()
        client.session = mock_session

        # Call the get method and check that it raises an exception
        with pytest.raises(Exception):
            await client.get("https://example.com")

        await client.close()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_post_request(self, monkeypatch):
        """Test the post method."""
        # Mock aiohttp.ClientSession
        mock_session = MagicMock()
        mock_session.closed = False
        # Make sure the close method is an AsyncMock
        mock_session.close = AsyncMock()

        # Mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(
            return_value="<html><body>Post Result</body></html>"
        )
        mock_response.raise_for_status = MagicMock()

        # Context manager for session.post
        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        # Set up the post method to return our mock context
        mock_session.post = MagicMock(return_value=mock_context)

        # Create a client and patch its session
        client = BrowserClient()
        client.session = mock_session

        # Call the post method with data and check the result
        data = {"key": "value"}
        result = await client.post("https://example.com/submit", data=data)
        assert result == "<html><body>Post Result</body></html>"

        # Verify the mock was called with the expected arguments
        mock_session.post.assert_called_once()
        args, kwargs = mock_session.post.call_args
        assert args[0] == "https://example.com/submit"
        assert kwargs["data"] == data

        # Check that the history was updated with the method
        assert len(client.history) == 1
        assert client.history[0]["url"] == "https://example.com/submit"
        assert client.history[0]["method"] == "POST"

        await client.close()
        mock_session.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_history_management(self):
        """Test history recording and retrieval."""
        client = BrowserClient()

        # Create mock session and responses
        mock_session = MagicMock()
        mock_session.closed = False
        # Make sure the close method is an AsyncMock
        mock_session.close = AsyncMock()

        # Mock response 1
        mock_response1 = MagicMock()
        mock_response1.status = 200
        mock_response1.text = AsyncMock(return_value="<html>Page 1</html>")
        mock_response1.raise_for_status = MagicMock()

        # Context manager for first request
        mock_context1 = MagicMock()
        mock_context1.__aenter__ = AsyncMock(return_value=mock_response1)
        mock_context1.__aexit__ = AsyncMock(return_value=None)

        # Mock response 2
        mock_response2 = MagicMock()
        mock_response2.status = 200
        mock_response2.text = AsyncMock(return_value="<html>Page 2</html>")
        mock_response2.raise_for_status = MagicMock()

        # Context manager for second request
        mock_context2 = MagicMock()
        mock_context2.__aenter__ = AsyncMock(return_value=mock_response2)
        mock_context2.__aexit__ = AsyncMock(return_value=None)

        # Setup get to return different responses
        mock_session.get = MagicMock(side_effect=[mock_context1, mock_context2])

        # Set the client session
        client.session = mock_session

        # Make two requests
        await client.get("https://example.com/page1")
        await client.get("https://example.com/page2")

        # Check the history
        assert len(client.history) == 2
        assert client.history[0]["url"] == "https://example.com/page1"
        assert client.history[1]["url"] == "https://example.com/page2"

        # Check current URL
        assert client.get_current_url() == "https://example.com/page2"

        # Check history retrieval
        history = client.get_history()
        assert len(history) == 2
        assert history[0]["url"] == "https://example.com/page1"

        await client.close()
        mock_session.close.assert_awaited_once()

    def test_url_resolution(self):
        """Test URL resolution for relative URLs."""
        client = BrowserClient()

        # Test different URL combinations
        base_url = "https://example.com/path/page.html"
        test_cases = [
            # (relative URL, expected absolute URL)
            ("subpage.html", "https://example.com/path/subpage.html"),
            ("/newpath/page.html", "https://example.com/newpath/page.html"),
            ("../otherpage.html", "https://example.com/otherpage.html"),
            ("https://other.com/page.html", "https://other.com/page.html"),
            ("//cdn.example.com/image.jpg", "https://cdn.example.com/image.jpg"),
        ]

        for rel_url, expected in test_cases:
            resolved = client.resolve_url(base_url, rel_url)
            assert resolved == expected
