"""
Root conftest.py for DeepBrowse testing.

This file provides pytest fixtures available to all test modules.
"""

import os
import pytest
import asyncio
import httpx
from unittest.mock import MagicMock, patch

# Set environment variables for testing
os.environ["OPENAI_API_KEY"] = "test-openai-key"


@pytest.fixture
def api_key():
    """Return a test API key."""
    return "test-openai-key"


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    response = MagicMock()
    response.status_code = 200
    response.text = (
        "<html><body><h1>Test Page</h1><p>This is a test page.</p></body></html>"
    )
    response.headers = {"content-type": "text/html", "content-encoding": "gzip"}
    response.raise_for_status = MagicMock(return_value=None)
    return response


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    client = MagicMock()

    # Mock response for get requests
    response = MagicMock()
    response.status_code = 200
    response.text = (
        "<html><body><h1>Test Page</h1><p>This is a test page.</p></body></html>"
    )
    response.headers = {"content-type": "text/html", "content-encoding": "gzip"}
    response.raise_for_status = MagicMock(return_value=None)

    # Setup the mock client
    async def mock_get(*args, **kwargs):
        return response

    async def mock_aclose(*args, **kwargs):
        pass

    # Apply the mocks
    client.get = mock_get
    client.aclose = mock_aclose

    return client


@pytest.fixture
def google_search_html():
    """Return a sample Google search results HTML."""
    return """
    <html>
        <body>
            <div class="g">
                <h3>First Result</h3>
                <a href="https://example.com/result1" data-ved="123">First Result</a>
            </div>
            <div class="g">
                <h3>Second Result</h3>
                <a href="https://example.com/result2" data-ved="456">Second Result</a>
            </div>
            <div class="g">
                <h3>Third Result</h3>
                <a href="https://example.com/result3" data-ved="789">Third Result</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def product_page_html():
    """Return a sample product page HTML with battery information."""
    return """
    <html>
        <head>
            <title>iPhone 15 Pro - Apple</title>
        </head>
        <body>
            <div class="product-specs">
                <h2>Battery and Power</h2>
                <ul>
                    <li>Up to 23 hours of video playback</li>
                    <li>Up to 75 hours of audio playback</li>
                    <li>Fast-charge capable: Up to 50% charge in around 30 minutes</li>
                </ul>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def event_loop():
    """Create an event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
