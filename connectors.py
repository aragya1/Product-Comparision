from langchain_community.utilities import GoogleSerperAPIWrapper
import os
from dotenv import load_dotenv
from typing import Literal,Optional, List, Any,Dict
from autogen_core.tools import FunctionTool
from model import get_gemini_client
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
import prompts
from serpapi import GoogleSearch


def google_search(query:str, domain:str) -> Dict[str, Any]:
    """    
    Performs a Google search using the Serper API.
    
    Args:
        query (str): The search query to execute.
        domain(str) : Searches particular domain (Valid options - im: Google Images API, lcl - Google Local API ,vid: Google Videos API,nws: Google News API,shop: Google Shopping API,pts: Google Patents API)        
    Returns:
        JSON: A JSON containing the search results.
    """
    load_dotenv()
    key = os.getenv("SERPER_API_KEY")

    if not key:
        return "Error: SERPER_API_KEY not found in .env"
    
    os.environ["SERPER_API_KEY"] = key


    search_tool_wrapper = GoogleSerperAPIWrapper(tbs = domain)
    try:
        result = search_tool_wrapper.run(query)
        return result
    except Exception as e:
        return f"Search failed: {str(e)}"



def amazon_search(query: str, limit: int = 5, region: str = "in") -> List:
    """
    Search Amazon via SerpAPI and return normalized product dictionaries.
    
    Args:
        query: Product search keyword (e.g., "iPhone 15").
        limit: Number of results to fetch.
        region: Country domain (e.g., "us", "in").
    
    Returns:
        List of dicts with product details (title, url, price, etc.).
    """
    load_dotenv()
    key = os.getenv("SERPAPI_KEY")
    print(key)
    if not key:
        return "Error: SERPAPI_KEY not found in .env"
    
    params = {
        "engine": "amazon",
        "api_key": key,
        "amazon_domain": f"amazon.{region}",
        "k": query,
        "num": limit,
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    print(results)

    products = []
    for item in results.get("organic_results", [])[:limit]:
        if isinstance(item, dict):
            products.append({
                "product_id": item.get("asin"),
                "title": item.get("title"),
                "url": item.get("link"),
                "price": item.get("price", {}).get("raw"),
                "currency": item.get("price", {}).get("currency"),
                "rating": item.get("rating"),
                "reviews": item.get("reviews"),  # list or count depending on API
                "source": f"amazon.{region}",
                "description": item.get("snippet"),
                "metadata": {
                    "delivery": item.get("delivery"),
                    "availability": item.get("availability"),
                },
                "raw": item,
                "image_url": item.get("thumbnail"),
            })

    return products


def amazon_product(asin: str, region: str = "in") -> dict:
    """
    Fetch detailed information for a specific Amazon product using ASIN.

    Args:
        asin: Amazon product ID (e.g., "B0C6HZ7Q7T").
        region: Country domain (e.g., "us", "in").

    Returns:
        Dict with detailed product info (title, price, rating, images, description, etc.)
    """
    load_dotenv()
    key = os.getenv("SERPAPI_KEY")

    if not key:
        return "Error: SERPAPI_KEY not found in .env"
    
    params = {
        "engine": "amazon_product",
        "api_key": key,
        "amazon_domain": f"amazon.{region}",
        "asin": asin,
    }

    search = GoogleSearch(params)
    result = search.get_dict()

    # Normalize some fields
    product = {
        "asin": asin,
        "title": result.get("title"),
        "url": result.get("link"),
        "price": result.get("pricing", {}).get("price"),
        "currency": result.get("pricing", {}).get("currency"),
        "rating": result.get("rating"),
        "reviews": result.get("reviews"),
        "brand": result.get("brand"),
        "category": result.get("category"),
        "features": result.get("features"),
        "description": result.get("description"),
        "images": result.get("images"),
        "delivery": result.get("delivery_info"),
        "availability": result.get("availability"),
        "raw": result,
    }

    return product

google_search_tool = FunctionTool(google_search,description="Google search tool based on Seper API")
amazon_search_tool = FunctionTool(amazon_search,description="Amazon search tool based on SerpAPI")
amazon_product_tool = FunctionTool(amazon_product, description="Amazon product search tool based on SerpAPI, get detailed product deatils")
