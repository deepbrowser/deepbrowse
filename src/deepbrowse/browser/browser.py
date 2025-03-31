from typing import Dict, Optional, Any, List
from deepbrowse.parser.parser import ContentScraper
from deepbrowse.agent.agent import BrowsingAgent
from deepbrowse.navigation.navigate import BrowserClient


class DeepBrowser:
    def __init__(self, api_key: Optional[str] = None):
        self.agent = BrowsingAgent(api_key)
        self.parser = ContentScraper()
        self.browser_client = BrowserClient()
        self.collected_data = []
        self.summary = ""

    async def ask(self, prompt: str, time_limit: float = 180) -> Dict:
        """
        Execute an autonomous web browsing session based on the user's prompt.

        Args:
            prompt: The user's query or task description
            time_limit: Maximum time in seconds to spend browsing

        Returns:
            A dictionary containing the results and session information
        """
        # Initialize session data
        session_data = {
            "prompt": prompt,
            "pages_visited": [],
            "data_collected": [],
            "completed": False,
            "error": None,
        }

        try:
            # Start the autonomous agent
            results = await self.agent.execute_browsing_session(
                prompt=prompt,
                time_limit=time_limit,
                browser_client=self.browser_client,
                parser=self.parser,
            )

            # Store the collected data for later summarization
            self.collected_data = results.get("collected_data", [])

            # Update session data with results
            session_data.update(
                {
                    "pages_visited": results.get("pages_visited", []),
                    "data_collected": self.collected_data,
                    "completed": True,
                }
            )

            # Generate summary immediately if data is available
            if self.collected_data:
                self.summary = self._generate_summary(prompt, self.collected_data)
                session_data["summary"] = self.summary

            return session_data

        except Exception as e:
            session_data["error"] = str(e)
            return session_data

    def get_summary(self) -> str:
        """
        Get the summary of the last browsing session.

        Returns:
            A string containing the summarized findings from the web browsing session
        """
        return self.summary

    def _generate_summary(self, prompt: str, collected_data: List[Dict]) -> str:
        """
        Generate a summary of the collected data based on the original prompt.

        Args:
            prompt: The original user query
            collected_data: List of data collected during browsing

        Returns:
            A concise summary of the findings
        """
        # Here we would typically use an LLM to generate a summary,
        # but for now we'll implement a simple version

        if not collected_data:
            return "No data was collected during the browsing session."

        # Build a simple summary from the collected data
        summary_parts = ["## Summary of findings\n\n"]

        # Add information about the number of sources
        summary_parts.append(f"Based on {len(collected_data)} sources:\n\n")

        # Extract key information from each source
        for i, data in enumerate(collected_data, 1):
            title = data.get("title", f"Source {i}")
            url = data.get("url", "Unknown URL")
            content = data.get("content", "No content extracted")

            # Add source information to summary
            summary_parts.append(f"### {title}\n")
            summary_parts.append(f"- URL: {url}\n")

            # Add a snippet of the content (first 200 chars)
            content_snippet = content[:200] + "..." if len(content) > 200 else content
            summary_parts.append(f"- Content preview: {content_snippet}\n\n")

        return "".join(summary_parts)
