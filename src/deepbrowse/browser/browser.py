from typing import Dict, Optional, Any
from ..client.http_client import BaseHttpClient
from ..scraper.scraper import BaseScraper
from ..agent.action_agent import BaseAgent


class DeepBrowser:
    def __init__(self):
        pass

    async def ask(self, prompt: str, time_limit: float = 180) -> Dict:
        pass

    def get_summary(self) -> str:
        pass

    def set_http_client(self, client: BaseHttpClient) -> None:
        pass

    def set_scraper(self, scraper: BaseScraper) -> None:
        pass

    def set_agent(self, agent: BaseAgent) -> None:
        pass
