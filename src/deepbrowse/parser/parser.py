from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin


class BaseScraper:
    """Base scraper class for extracting content from HTML."""

    def __init__(self):
        self.soup = None
        self.url = None

    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content into a BeautifulSoup object.

        Args:
            html_content: The HTML content as a string

        Returns:
            BeautifulSoup object
        """
        self.soup = BeautifulSoup(html_content, "html.parser")
        return self.soup

    def extract_text(self, element) -> str:
        """
        Extract clean text from a BeautifulSoup element.

        Args:
            element: BeautifulSoup element

        Returns:
            Cleaned text string
        """
        if element is None:
            return ""

        # Get the text and clean it
        text = element.get_text(separator=" ", strip=True)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        return text

    def extract_links(self, html_content: str = None) -> List[Dict[str, str]]:
        """
        Extract all links from an HTML page.

        Args:
            html_content: Optional HTML content as a string. If not provided,
                        uses previously parsed content.

        Returns:
            List of dictionaries containing link URLs and text
        """
        if html_content:
            self.parse_html(html_content)

        if not self.soup:
            return []

        links = []
        for a_tag in self.soup.find_all("a", href=True):
            href = a_tag["href"]

            # Skip empty, javascript, or anchor links
            if not href or href.startswith("javascript:") or href.startswith("#"):
                continue

            # Resolve relative URLs if base URL is set
            if self.url and not (
                href.startswith("http://") or href.startswith("https://")
            ):
                href = urljoin(self.url, href)

            links.append({"url": href, "text": self.extract_text(a_tag)})

        return links


class ContentScraper(BaseScraper):
    """Specialized scraper for extracting main content from pages."""

    def __init__(self):
        super().__init__()
        self.main_content_tags = [
            "article",
            "main",
            'div[role="main"]',
            ".content",
            "#content",
            ".post",
            ".article",
            ".entry",
            ".page-content",
            ".main-content",
            ".product-header",
        ]

    def extract_main_content(self, html_content: str) -> str:
        """
        Extract the main content from an HTML page.

        Args:
            html_content: HTML content as a string

        Returns:
            Extracted main content as text
        """
        self.parse_html(html_content)
        content_parts = []

        # Try to extract product header first if it exists
        product_header = self.soup.find(class_="product-header")
        if product_header:
            content_parts.append(self.extract_text(product_header))

        # Try common content containers
        for selector in self.main_content_tags:
            if "[" in selector and "]" in selector:
                # This is a CSS attribute selector
                tag, attr = selector.replace("]", "").split("[")
                attr_name, attr_value = attr.split("=")
                attr_value = attr_value.strip("\"'")
                element = self.soup.find(tag, {attr_name.strip(): attr_value})
            elif selector.startswith("."):
                # This is a class selector
                element = self.soup.find(class_=selector[1:])
            elif selector.startswith("#"):
                # This is an ID selector
                element = self.soup.find(id=selector[1:])
            else:
                # This is a tag selector
                element = self.soup.find(selector)

            if element and element != product_header:  # Avoid duplication
                content_parts.append(self.extract_text(element))

        # If content parts were found, join them
        if content_parts:
            return " ".join(content_parts)

        # If no main content container found, extract from body
        # but remove navigation, header, footer, etc.
        body = self.soup.find("body")
        if body:
            # Remove common non-content elements
            for selector in [
                "nav",
                "header",
                "footer",
                "aside",
                ".sidebar",
                "#sidebar",
            ]:
                for element in body.select(selector):
                    element.decompose()

            return self.extract_text(body)

        # Fallback to whole page content
        return self.extract_text(self.soup)

    def extract_title(self, html_content: str) -> str:
        """
        Extract the title from an HTML page.

        Args:
            html_content: HTML content as a string

        Returns:
            Page title as a string
        """
        self.parse_html(html_content)

        # Try <title> tag first
        title_tag = self.soup.find("title")
        if title_tag:
            return self.extract_text(title_tag)

        # Try main heading (h1)
        h1_tag = self.soup.find("h1")
        if h1_tag:
            return self.extract_text(h1_tag)

        # Try meta title
        meta_title = self.soup.find("meta", property="og:title")
        if meta_title and meta_title.get("content"):
            return meta_title["content"]

        # Fallback
        return "Untitled Page"

    def extract_metadata(self, html_content: str) -> Dict[str, str]:
        """
        Extract metadata from an HTML page, including Open Graph and other meta tags.

        Args:
            html_content: HTML content as a string

        Returns:
            Dictionary of metadata
        """
        self.parse_html(html_content)
        metadata = {
            "title": self.extract_title(html_content),
            "description": "",
            "keywords": "",
            "author": "",
            "published_date": "",
            "image": "",
            "url": "",
            "og_title": "",
            "og_description": "",
        }

        # Description
        meta_desc = self.soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            metadata["description"] = meta_desc["content"]

        # Try Open Graph description
        og_desc = self.soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            metadata["og_description"] = og_desc["content"]
            # If no regular description, use OG description
            if not metadata["description"]:
                metadata["description"] = og_desc["content"]

        # Open Graph title
        og_title = self.soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            metadata["og_title"] = og_title["content"]

        # Keywords
        meta_keywords = self.soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and meta_keywords.get("content"):
            metadata["keywords"] = meta_keywords["content"]

        # Author
        meta_author = self.soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            metadata["author"] = meta_author["content"]

        # Published date
        meta_date = self.soup.find("meta", property="article:published_time")
        if meta_date and meta_date.get("content"):
            metadata["published_date"] = meta_date["content"]

        # Image (Open Graph)
        og_image = self.soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            metadata["image"] = og_image["content"]

        # URL (Open Graph)
        og_url = self.soup.find("meta", property="og:url")
        if og_url and og_url.get("content"):
            metadata["url"] = og_url["content"]

        return metadata


class NavigationScraper(BaseScraper):
    """Specialized scraper for site navigation elements."""

    def __init__(self):
        super().__init__()
        self.url = None

    def set_base_url(self, url: str):
        """Set the base URL for resolving relative links."""
        self.url = url

    def extract_navigation_links(self, html_content: str) -> List[Dict[str, str]]:
        """
        Extract navigation links from an HTML page.

        Args:
            html_content: HTML content as a string

        Returns:
            List of navigation links as dictionaries with url and text
        """
        self.parse_html(html_content)

        nav_links = []

        # Look for navigation elements
        nav_elements = self.soup.select(
            "nav, .nav, .navigation, .menu, header ul, .navbar"
        )

        for nav in nav_elements:
            for a_tag in nav.find_all("a", href=True):
                href = a_tag["href"]

                # Skip empty, javascript, or anchor links
                if not href or href.startswith("javascript:") or href.startswith("#"):
                    continue

                # Resolve relative URLs if base URL is set
                if self.url and not (
                    href.startswith("http://") or href.startswith("https://")
                ):
                    href = urljoin(self.url, href)

                nav_links.append({"url": href, "text": self.extract_text(a_tag)})

        return nav_links

    def find_next_page(self, html_content: str) -> Optional[str]:
        """
        Find the URL of the next page in paginated content.

        Args:
            html_content: HTML content as a string

        Returns:
            URL of the next page, or None if not found
        """
        self.parse_html(html_content)

        # Common next page selectors
        next_selectors = [
            "a.next",
            ".next a",
            'a[rel="next"]',
            'a:contains("Next")',
            ".pagination a.next",
            '.pagination a[rel="next"]',
            'a[aria-label="Next"]',
            ".next-page",
            "#next-page",
        ]

        for selector in next_selectors:
            # Handle CSS pseudo-class contains
            if ":contains(" in selector:
                base_selector, text = selector.split(":contains(")
                text = text.strip(")\"'")

                for a_tag in self.soup.select(base_selector):
                    if text.lower() in self.extract_text(a_tag).lower():
                        href = a_tag.get("href")
                        if href and not href.startswith("#"):
                            # Resolve relative URL if needed
                            if self.url and not (
                                href.startswith("http://")
                                or href.startswith("https://")
                            ):
                                href = urljoin(self.url, href)
                            return href
            else:
                # Standard CSS selector
                next_link = self.soup.select_one(selector)
                if next_link and next_link.get("href"):
                    href = next_link["href"]
                    if not href.startswith("#"):
                        # Resolve relative URL if needed
                        if self.url and not (
                            href.startswith("http://") or href.startswith("https://")
                        ):
                            href = urljoin(self.url, href)
                        return href

        return None
