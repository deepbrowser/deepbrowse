"""
Test fixtures for the DeepBrowse agent tests.

This file contains fixtures that provide mock HTML content
for testing the browse and search functionality.
"""

import pytest


@pytest.fixture
def product_page_html():
    """Return a sample product page HTML with iPhone battery information."""
    return """
    <html>
    <head>
        <title>iPhone 15 Pro - Technical Specifications - Apple</title>
    </head>
    <body>
        <h1>iPhone 15 Pro</h1>
        <div class="specs-container">
            <section class="battery">
                <h2>Battery and Power</h2>
                <ul>
                    <li>Up to 23 hours video playback</li>
                    <li>Up to 20 hours video streaming</li>
                    <li>Up to 75 hours audio playback</li>
                    <li>Fast-charge capable: Up to 50% charge in around 30 minutes with 20W adapter or higher</li>
                </ul>
            </section>
            <section class="design">
                <h2>Design and Display</h2>
                <ul>
                    <li>6.1‑inch Super Retina XDR display</li>
                    <li>ProMotion technology with adaptive refresh rates up to 120Hz</li>
                    <li>Ceramic Shield front</li>
                    <li>Titanium design, tougher than any smartphone glass</li>
                </ul>
            </section>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def google_search_html():
    """Return a sample Google search results page HTML."""
    return """
    <html>
    <head>
        <title>iPhone 15 Pro battery life - Google Search</title>
    </head>
    <body>
        <div class="search-results">
            <h1>Google Search Results</h1>
            <div class="g">
                <div class="rc">
                    <h3 class="r"><a href="https://example.com/article1">First Result: iPhone 15 Pro battery life review</a></h3>
                    <div class="s">
                        <div class="st">The iPhone 15 Pro offers up to 23 hours of video playback, a significant improvement over previous models.</div>
                    </div>
                </div>
            </div>
            <div class="g">
                <div class="rc">
                    <h3 class="r"><a href="https://example.com/article2">Second Result: Comparing iPhone battery performance</a></h3>
                    <div class="s">
                        <div class="st">Our tests show that the iPhone 15 Pro lasts approximately 20% longer than the iPhone 14 Pro under similar conditions.</div>
                    </div>
                </div>
            </div>
            <div class="g">
                <div class="rc">
                    <h3 class="r"><a href="https://example.com/article3">Third Result: Apple's official iPhone 15 Pro specs</a></h3>
                    <div class="s">
                        <div class="st">According to Apple, the iPhone 15 Pro features up to 23 hours of video playback, 20 hours of streamed video, and 75 hours of audio.</div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def shopping_page_html():
    """Return a sample shopping page HTML with product information."""
    return """
    <html>
    <head>
        <title>Shop iPhone 15 Pro - Best Deals</title>
    </head>
    <body>
        <h1>iPhone 15 Pro Deals</h1>
        <div class="product-container">
            <div class="product">
                <h2>iPhone 15 Pro - 128GB</h2>
                <div class="price">$999.00</div>
                <div class="description">
                    <p>The iPhone 15 Pro features the A17 Pro chip, a titanium design, and a pro camera system.</p>
                    <ul>
                        <li>6.1-inch Super Retina XDR display</li>
                        <li>A17 Pro chip</li>
                        <li>Pro camera system</li>
                        <li>Up to 23 hours of battery life</li>
                    </ul>
                </div>
            </div>
            <div class="product">
                <h2>iPhone 15 Pro - 256GB</h2>
                <div class="price">$1,099.00</div>
                <div class="description">
                    <p>More storage for all your photos, videos, and apps.</p>
                </div>
            </div>
            <div class="product">
                <h2>iPhone 15 Pro - 512GB</h2>
                <div class="price">$1,299.00</div>
                <div class="description">
                    <p>Ideal for professionals who need more space.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
