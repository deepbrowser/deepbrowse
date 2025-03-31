#!/usr/bin/env python3
"""
Simple DeepBrowse Example - Product Comparison

This is a minimal example that uses DeepBrowser to compare two products.
"""

import asyncio
import sys
import os

# Add the src directory to the path so we can import the package
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.deepbrowse.browser.browser import DeepBrowser

from dotenv import load_dotenv

load_dotenv()


async def main():
    print("Initializing DeepBrowser...")
    browser = DeepBrowser(os.getenv("OPENAI_API_KEY"))

    # Use a query that requires searching and browsing multiple sources
    query = "What's the difference between iPhone 15 Pro and iPhone 15 Pro Max battery life?"
    print(f"\nSending query: '{query}'")
    print("Starting browsing session (15-second time limit)...")

    try:
        # Execute the browsing session with a 15-second time limit
        result = await browser.ask(query, time_limit=15)

        # Print debugging information about the browsing session
        print("\n--- Browsing Session Results ---")
        if "pages_visited" in result:
            print(f"\nVisited {len(result['pages_visited'])} pages:")
            for i, page in enumerate(result["pages_visited"], 1):
                print(
                    f"  {i}. {page.get('title', 'Unknown')} - {page.get('url', 'No URL')}"
                )

        # Print the collected data
        if "data_collected" in result and result["data_collected"]:
            print(f"\nCollected data from {len(result['data_collected'])} sources")
        else:
            print("\nNo data was collected during the session")

        # Print the summary
        print("\n--- Final Summary ---")
        summary = browser.get_summary()
        if summary:
            print(summary)
        else:
            print(
                "No summary was generated. The browsing session may not have collected enough information."
            )

        if result.get("error"):
            print(f"\nError during browsing: {result['error']}")

    finally:
        # Ensure the browser client's session is properly closed
        print("\nClosing browser session...")
        await browser.browser_client.close()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
