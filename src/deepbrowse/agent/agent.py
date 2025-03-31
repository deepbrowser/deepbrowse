from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, Tool
from langchain_core.messages import HumanMessage, AIMessage
import asyncio
import time


class BrowsingAgent:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the browsing agent with LangChain components.

        Args:
            api_key: Optional OpenAI API key, if not provided will try to get from environment
        """
        self.llm = ChatOpenAI(
            temperature=0.2, openai_api_key=api_key, model_name="gpt-3.5-turbo-16k"
        )

        # Use a simple list to store conversation history instead of ConversationBufferMemory
        self.chat_history = []

        # Will be initialized in execute_browsing_session
        self.tools = []
        self.agent_executor = None

    async def execute_browsing_session(
        self, prompt: str, browser_client: Any, parser: Any, time_limit: float = 180
    ) -> Dict:
        """
        Execute an autonomous web browsing session based on the user's prompt.

        Args:
            prompt: The user's query or task description
            browser_client: The browser client used for HTTP requests
            parser: The HTML parser for content extraction
            time_limit: Maximum time in seconds to spend browsing

        Returns:
            A dictionary containing the collected data and browsing session information
        """
        # Initialize session data
        session_results = {"collected_data": [], "pages_visited": [], "error": None}

        try:
            # Set up the tools for the agent
            self._setup_tools(browser_client, parser)

            # Create the agent executor
            self._setup_agent()

            # Start timing the session
            start_time = time.time()

            # If agent was successfully initialized
            if self.agent_executor:
                print(f"Executing browsing agent for query: {prompt}")

                # Use the agent to execute the browsing task
                agent_result = await asyncio.to_thread(
                    self.agent_executor.run, input=prompt
                )

                print(f"Agent execution completed. Result: {agent_result}")

                # The pages_visited and collected_data would be populated by the tools
                # as they are called by the agent

                # Convert the browsing result to the expected format
                if browser_client.history:
                    for entry in browser_client.history:
                        session_results["pages_visited"].append(
                            {
                                "url": entry.get("url", "Unknown URL"),
                                "title": "Page "
                                + str(len(session_results["pages_visited"]) + 1),
                                "timestamp": entry.get("timestamp", time.time()),
                            }
                        )

                # For now, just store the full result in collected_data
                session_results["collected_data"].append(
                    {
                        "url": "agent_result",
                        "title": "Agent Results",
                        "content": agent_result,
                        "metadata": {"source": "agent"},
                    }
                )

                session_results["agent_result"] = agent_result
            else:
                # Fallback to the placeholder implementation
                print("Agent initialization failed. Using fallback browsing plan.")

                # Create a simple browsing plan
                browsing_plan = await self._create_browsing_plan(prompt)
                session_results["browsing_plan"] = browsing_plan

                # Execute the browsing plan with a time limit
                while time.time() - start_time < time_limit:
                    # Check if we've completed the browsing plan
                    if self._is_browsing_complete(session_results, browsing_plan):
                        break

                    # Determine the next action based on the current state
                    next_action = await self._determine_next_action(
                        prompt, browsing_plan, session_results
                    )

                    # Execute the action
                    if next_action["action_type"] == "browse":
                        print(f"Browsing to: {next_action['url']}")

                        # Execute a browsing action
                        url = next_action["url"]
                        response = await browser_client.get(url)

                        # Record the visit
                        session_results["pages_visited"].append(
                            {
                                "url": url,
                                "title": parser.extract_title(response),
                                "timestamp": time.time(),
                            }
                        )

                        # Parse the content
                        content = parser.extract_main_content(response)
                        metadata = parser.extract_metadata(response)

                        # Store the collected data
                        session_results["collected_data"].append(
                            {
                                "url": url,
                                "title": metadata.get("title", "Unknown Title"),
                                "content": content,
                                "metadata": metadata,
                            }
                        )

                    # Add a small delay between actions
                    await asyncio.sleep(1)

            return session_results

        except Exception as e:
            import traceback

            error_msg = (
                f"Error during browsing session: {str(e)}\n{traceback.format_exc()}"
            )
            print(error_msg)
            session_results["error"] = error_msg
            return session_results

    def _setup_tools(self, browser_client, parser):
        """Set up the tools available to the agent."""

        # Create synchronous wrapper functions for async methods
        def browse_website(url):
            try:
                # Use real web browsing but with content size limits
                print(f"Browsing to URL: {url}")

                # Create a new event loop for the current thread
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # If no event loop exists in this thread, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Run the async browser get method in the event loop
                html_content = loop.run_until_complete(browser_client.get(url))

                # Extract just the important content to avoid token limit issues
                extracted_content = _extract_important_content(html_content, url)

                return extracted_content
            except Exception as e:
                print(f"Error browsing to {url}: {str(e)}")
                return f"Error: {str(e)}"

        def search_google(query):
            """Use Google search to find relevant pages for a query."""
            try:
                print(f"Searching Google for: {query}")

                # Format the query for Google search
                search_url = (
                    f"https://www.google.com/search?q={query.replace(' ', '+')}"
                )

                # Create a new event loop for the current thread
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    # If no event loop exists in this thread, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Perform the search
                html_content = loop.run_until_complete(browser_client.get(search_url))

                # Extract search results with a focus on result links
                import re

                # Extract all result links
                search_results = []

                # Look for search result links using various patterns that match Google's structure
                link_patterns = [
                    r'<a href="(https?://[^"]+)" ping="[^"]*"[^>]*data-ved="[^"]*"[^>]*>',  # Standard Google search result
                    r'<a href="(https?://[^"]+)" data-ved="[^"]*"[^>]*>',  # Alternative pattern
                    r'<a href="(/url\?q=https?://[^&]+)[&]',  # Old style redirected links
                ]

                for pattern in link_patterns:
                    links = re.findall(pattern, html_content)
                    for link in links:
                        # Clean up /url?q= links
                        if link.startswith("/url?q="):
                            link = link[7:]

                        # Skip Google's own links and other common irrelevant results
                        if any(
                            domain in link
                            for domain in [
                                "google.com/search",
                                "accounts.google",
                                "maps.google",
                                "translate.google",
                                "webcache.googleusercontent",
                            ]
                        ):
                            continue

                        search_results.append(link)

                # Limit to unique, top 5 results
                unique_results = []
                for link in search_results:
                    if link not in unique_results and len(unique_results) < 5:
                        unique_results.append(link)

                # Extract titles when possible
                titled_results = []
                title_pattern = r'<h3[^>]*>(.*?)</h3>.*?<a href="([^"]*)"'
                title_matches = re.findall(title_pattern, html_content, re.DOTALL)

                for title, link in title_matches:
                    # Clean the title (remove HTML tags)
                    clean_title = re.sub(r"<[^>]+>", "", title)
                    if "http" in link and len(titled_results) < 5:
                        titled_results.append((clean_title, link))

                # Format results as HTML
                if titled_results:
                    results_html = "<html><body><h1>Google Search Results</h1><ul>"
                    for title, link in titled_results:
                        results_html += f"<li><a href='{link}'>{title}</a></li>"
                    results_html += "</ul></body></html>"
                elif unique_results:
                    results_html = "<html><body><h1>Google Search Results</h1><ul>"
                    for link in unique_results:
                        results_html += f"<li><a href='{link}'>{link}</a></li>"
                    results_html += "</ul></body></html>"
                else:
                    results_html = "<html><body><h1>Google Search Results</h1><p>No results found.</p></body></html>"

                return results_html

            except Exception as e:
                print(f"Error searching Google for '{query}': {str(e)}")
                return f"Error in Google search: {str(e)}"

        def extract_content(html):
            try:
                # Simple extraction to avoid token limit issues
                if len(html) > 8000:  # Limit content to avoid token issues
                    # Extract only the first 8000 characters
                    return html[:8000] + "... [Content truncated due to size]"
                return html
            except Exception as e:
                print(f"Error extracting content: {str(e)}")
                return f"Error: {str(e)}"

        def extract_links(html):
            try:
                # Use a simple regex-based extraction that won't consume too many tokens
                import re

                links = re.findall(r'<a href=[\'"]?(http[^\'" >]+)', html)
                # Limit the number of links to avoid token issues
                if len(links) > 10:
                    return links[:10] + ["... more links truncated"]
                return links if links else ["No links found"]
            except Exception as e:
                print(f"Error extracting links: {str(e)}")
                return [f"Error: {str(e)}"]

        # Helper function to extract only important content
        def _extract_important_content(html, url):
            import re

            # For search result pages or Google search
            if "google.com/search" in url:
                # Extract search results with links to product pages
                links = re.findall(
                    r'<a href=[\'"]?(https?://[^\'" >]+)["\'](.*?)</a>',
                    html,
                    re.DOTALL,
                )

                # Also try to extract the results with titles
                title_pattern = r'<h3[^>]*>(.*?)</h3>.*?<a href="([^"]*)"'
                title_matches = re.findall(title_pattern, html, re.DOTALL)

                extracted_html = "<html><body><h1>Google Search Results</h1><ul>"

                # Add links with titles
                for title, link in title_matches[:5]:  # Limit to 5
                    if "http" in link:
                        # Clean the title (remove HTML tags)
                        clean_title = re.sub(r"<[^>]+>", "", title)
                        extracted_html += f"<li><a href='{link}'>{clean_title}</a></li>"

                # Add other links found
                link_count = 0
                for link in links:
                    if link_count >= 5:  # Limit to 5 total links
                        break
                    if isinstance(link, tuple):
                        link_url = link[0]
                    else:
                        link_url = link

                    # Skip links already added from title_matches
                    if any(link_url in l for _, l in title_matches):
                        continue

                    # Skip Google's own links
                    if any(
                        domain in link_url
                        for domain in [
                            "google.com/search",
                            "accounts.google",
                            "maps.google",
                        ]
                    ):
                        continue

                    extracted_html += f"<li><a href='{link_url}'>{link_url}</a></li>"
                    link_count += 1

                extracted_html += "</ul></body></html>"
                return extracted_html

            # First, let's check if we're on a specific product page
            elif "iphone-15-pro" in url or "iphone-16-pro" in url:
                # For iPhone product pages, extract specs related to camera, battery, and performance
                specs = {}

                # Look for battery specs specifically - more targeted search
                battery_patterns = [
                    r"(?i)<[^>]*>.*?Battery.*?(?:<[^>]*>){1,5}((?:Up to|All\-day).*?(?:hour|hrs|playback|mAh).*?)(?:<[^>]*>){1,3}",
                    r"(?i)Battery life(?:[^<]*<[^>]*>){1,3}([^<]*(?:hour|hrs|Up to|playback)[^<]*)",
                    r"(?i)Battery(?:[^<]*<[^>]*>){1,3}([^<]*(?:hour|hrs|Up to|playback)[^<]*)",
                ]

                for pattern in battery_patterns:
                    battery_matches = re.findall(pattern, html, re.DOTALL)
                    if battery_matches:
                        specs["battery"] = "".join(
                            battery_matches[:5]
                        )  # Take up to 5 matches
                        break

                # Look for other specs in a similar way
                # ...

                # Create a simplified HTML with just the extracted specs
                if specs:
                    extracted_html = (
                        "<html><body><h1>Extracted Product Information</h1>"
                    )
                    for category, content in specs.items():
                        extracted_html += f"<h2>{category.title()}</h2><p>{content}</p>"
                    extracted_html += "</body></html>"
                    return extracted_html

            # For other pages, just extract title and a small amount of content
            title_match = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
            title = title_match.group(1) if title_match else "Unknown Title"

            # Extract first few paragraphs
            paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
            content = ""
            for i, p in enumerate(paragraphs[:5]):  # Take just first 5 paragraphs
                if len(content) < 3000:  # Keep total under 3000 chars
                    content += p + "\n\n"

            return f"<html><body><h1>{title}</h1>{content}</body></html>"

        # Set up tools with synchronous functions
        self.tools = [
            Tool(
                name="search_google",
                func=search_google,
                description="Search Google for information related to your query. Input should be a search query string.",
            ),
            Tool(
                name="browse_website",
                func=browse_website,
                description="Browse to a specific URL and get the HTML content. Input should be a valid URL starting with http:// or https://",
            ),
            Tool(
                name="extract_content",
                func=extract_content,
                description="Extract the main content from HTML. Input should be HTML content.",
            ),
            Tool(
                name="extract_links",
                func=extract_links,
                description="Extract all links from an HTML page. Input should be HTML content.",
            ),
        ]

    def _setup_agent(self):
        """Set up the LangChain agent."""
        try:
            # Import the right modules for agent creation
            from langchain.agents import AgentType, initialize_agent
            from langchain.memory import ConversationBufferMemory

            # Create a memory instance for the agent
            memory = ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            )

            # Initialize the agent with tools
            self.agent_executor = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,  # Set to True to see the agent's thought process
                handle_parsing_errors=True,
                memory=memory,  # Add memory for chat_history
            )

            print("Agent initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize agent: {str(e)}")
            # Fallback to simple chain if agent initialization fails
            self.agent_executor = None

    async def _create_browsing_plan(self, prompt: str) -> List[Dict]:
        """Create a browsing plan based on the user prompt."""
        # This would use the LLM to create a structured browsing plan
        # For now, we'll return a simple example plan
        return [
            {"step": 1, "action": "search", "query": prompt},
            {"step": 2, "action": "browse_results", "count": 3},
            {"step": 3, "action": "extract_information", "topics": prompt.split()},
        ]

    def _is_browsing_complete(
        self, session_results: Dict, browsing_plan: List[Dict]
    ) -> bool:
        """Check if the browsing plan has been completed."""
        # In a real implementation, this would check if all steps in the browsing plan
        # have been completed or if we've collected enough information
        # For simplicity, we'll just check if we've visited at least 3 pages
        return len(session_results["pages_visited"]) >= 3

    async def _determine_next_action(
        self, prompt: str, browsing_plan: List[Dict], session_results: Dict
    ) -> Dict:
        """Determine the next action based on the browsing plan and current state."""
        # This would use the LLM to decide what to do next
        # For simplicity, we'll return a simple action

        # If we haven't visited any pages yet, start with a search
        if not session_results["pages_visited"]:
            return {
                "action_type": "browse",
                "url": f"https://www.google.com/search?q={prompt.replace(' ', '+')}",
            }

        # Otherwise, follow a link from the current page
        return {"action_type": "follow_link", "url": "https://example.com/next-page"}

    def _choose_relevant_link(self, links: List[Dict], prompt: str) -> Dict:
        """Choose the most relevant link from a list based on the prompt."""
        # In a real implementation, this would use the LLM to select the most relevant link
        # For now, just return the first link if available, or a default
        if links:
            return links[0]
        return {"url": "https://example.com", "text": "Example"}
