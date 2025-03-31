from typing import Dict, Optional, Any
from deepbrowse.scraper.scraper import BaseScraper
from deepbrowse.agent.agent import BaseAgent


class DeepBrowser:
    def __init__(self):
        pass

    async def ask(self, prompt: str, time_limit: float = 180) -> Dict:
        pass

    def get_summary(self) -> str:
        pass
