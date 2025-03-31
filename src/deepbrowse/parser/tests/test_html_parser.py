"""
Tests for the html_parser module.

These tests verify that the ContentScraper class correctly extracts
content from different types of web pages.
"""

import pytest
from bs4 import BeautifulSoup

from src.deepbrowse.parser.parser import ContentScraper


class TestContentScraper:
    """Test suite for ContentScraper class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.parser = ContentScraper()

    def test_extract_links(self):
        """Test extraction of links from HTML content."""
        # Sample HTML with various links
        html = """
        <html>
        <head><title>Test Links</title></head>
        <body>
            <a href="https://example.com/1">First Link</a>
            <a href="https://example.com/2">Second Link</a>
            <a href="#top">Top of Page</a>
            <a href="javascript:void(0)">JavaScript Link</a>
            <a href="/relative-path">Relative Link</a>
        </body>
        </html>
        """

        # Extract links
        links = self.parser.extract_links(html)

        # Verify the extracted links (should skip JavaScript and anchor links)
        assert len(links) == 3
        assert links[0]["url"] == "https://example.com/1"
        assert links[0]["text"] == "First Link"
        assert links[1]["url"] == "https://example.com/2"
        assert links[2]["url"] == "/relative-path"
        assert links[2]["text"] == "Relative Link"

    def test_extract_main_content(self):
        """Test extraction of important content from a web page."""
        # Sample web page HTML with various content sections
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <header>This is a header</header>
            <nav>Navigation links</nav>
            <main>
                <h1>Main Heading</h1>
                <p>Important paragraph 1</p>
                <p>Important paragraph 2</p>
            </main>
            <footer>Footer content</footer>
        </body>
        </html>
        """

        # Extract content
        content = self.parser.extract_main_content(html)

        # Verify the extracted content includes main content
        assert "Main Heading" in content
        assert "Important paragraph 1" in content
        assert "Important paragraph 2" in content

    def test_extract_content_from_product_page(self):
        """Test extraction of content from a product page."""
        # Sample product page HTML
        html = """
        <html>
        <head><title>iPhone 15 Pro - Apple</title></head>
        <body>
            <div class="product-header">
                <h1>iPhone 15 Pro</h1>
                <div class="price">From $999</div>
            </div>
            <div class="product-features article">
                <section>
                    <h2>Battery and Power</h2>
                    <ul>
                        <li>Up to 23 hours video playback</li>
                        <li>Fast-charge capable</li>
                    </ul>
                </section>
                <section>
                    <h2>Camera</h2>
                    <ul>
                        <li>48MP main camera</li>
                        <li>Telephoto camera</li>
                    </ul>
                </section>
            </div>
        </body>
        </html>
        """

        # Extract content
        content = self.parser.extract_main_content(html)

        # Verify the extracted content includes product details
        assert "iPhone 15 Pro" in content
        assert "Battery and Power" in content
        assert "23 hours video playback" in content
        assert "Camera" in content
        assert "48MP main camera" in content

    def test_extract_title(self):
        """Test extraction of page title."""
        # Test with a simple title
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        title = self.parser.extract_title(html)
        assert title == "Test Title"

        # Test with no title but an H1
        html = "<html><head></head><body><h1>Main Heading</h1></body></html>"
        title = self.parser.extract_title(html)
        assert title == "Main Heading"

        # Test with Open Graph meta title
        html = '<html><head><meta property="og:title" content="OG Title"></head><body></body></html>'
        title = self.parser.extract_title(html)
        assert title == "OG Title"

        # Test with no title elements
        html = "<html><head></head><body></body></html>"
        title = self.parser.extract_title(html)
        assert title == "Untitled Page"

    def test_extract_metadata(self):
        """Test extraction of metadata from a page."""
        # HTML with various metadata
        html = """
        <html>
        <head>
            <title>Test Metadata</title>
            <meta name="description" content="This is a description">
            <meta name="keywords" content="test, metadata, extraction">
            <meta property="og:title" content="OG Title">
            <meta property="og:description" content="OG Description">
            <meta name="author" content="Test Author">
        </head>
        <body></body>
        </html>
        """

        # Extract metadata
        metadata = self.parser.extract_metadata(html)

        # Verify extracted metadata
        assert metadata["title"] == "Test Metadata"
        assert "This is a description" in metadata["description"]
        assert "test, metadata, extraction" in metadata["keywords"]
        assert "OG Title" in str(metadata)  # OG data should be included somewhere
