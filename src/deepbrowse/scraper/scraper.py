from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class BaseScraper:
    """Base scraper class for extracting content from HTML."""

    def __init__(self):
        pass

    def parse_html(self, html_content: str) -> BeautifulSoup:
        pass

    def extract_text(self, element) -> str:
        pass

    def extract_links(self) -> List[Dict[str, str]]:
        pass


class ContentScraper(BaseScraper):
    """Specialized scraper for extracting main content from pages."""

    def __init__(self):
        super().__init__()

    def extract_main_content(self, html_content: str) -> str:
        pass

    def extract_title(self, html_content: str) -> str:
        pass

    def extract_metadata(self, html_content: str) -> Dict[str, str]:
        pass


class NavigationScraper(BaseScraper):
    """Specialized scraper for site navigation elements."""

    def __init__(self):
        super().__init__()

    def extract_navigation_links(self, html_content: str) -> List[Dict[str, str]]:
        pass

    def find_next_page(self, html_content: str) -> Optional[str]:
        pass
