import requests
import json
import logging
from typing import List, Dict, Any


def duckduckgo_search(query: str) -> List[Dict[str, Any]]:
    """
    Perform a DuckDuckGo search and return the top results.

    Args:
        query (str): The search query.

    Returns:
        List[Dict[str, Any]]: The list of search results.
    """
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = response.json()
            results = data.get("RelatedTopics", [])
            top_results = results[:5]  # Get top 5 results
            return top_results
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding error: {e}")
            return []
    else:
        logging.error(f"Failed to fetch data from DuckDuckGo. Status code: {response.status_code}")
        return []
