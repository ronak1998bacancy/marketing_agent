from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from typing import Dict, Any
from serpapi import SerpApiClient as SerpApiSearch
import httpx
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/serpapi_mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
logger.debug("Loading SerpApi environment variables")
API_KEY = os.getenv("SERPAPI_API_KEY")

# Ensure API key is present
if not API_KEY:
    logger.error("SERPAPI_API_KEY not found in environment variables")
    raise ValueError("SERPAPI_API_KEY not found in environment variables. Please set it in the .env file.")

# Initialize the MCP server
logger.info("Creating SerpApi MCP server")
mcp = FastMCP("SerpApi MCP Server")

# Tool to perform searches via SerpApi
@mcp.tool()
async def search(params: Dict[str, Any] = {}) -> str:
    """Perform a search on the specified engine using SerpApi.

    Args:
        params: Dictionary of engine-specific parameters (e.g., {"q": "Coffee", "engine": "google_light", "location": "Austin, TX"}).

    Returns:
        A formatted string of search results or an error message.
    """
    logger.info(f"Performing SerpAPI search with params: {params}")
    params = {
        "api_key": API_KEY,
        "engine": "google_light",  # Fastest engine by default
        **params  # Include any additional parameters
    }

    try:
        search = SerpApiSearch(params)
        logger.debug("Executing SerpApi search")
        data = search.get_dict()
        logger.debug(f"Search results: {data}")

        # Process organic search results if available
        if "organic_results" in data:
            formatted_results = []
            for result in data.get("organic_results", []):
                title = result.get("title", "No title")
                link = result.get("link", "No link")
                snippet = result.get("snippet", "No snippet")
                formatted_results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
            logger.info(f"Successfully fetched {len(formatted_results)} SerpApi results")
            return "\n".join(formatted_results) if formatted_results else "No organic results found"
        else:
            logger.warning("No organic results found")
            return "No organic results found"

    # Handle HTTP-specific errors
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error during SerpAPI search: {e}", exc_info=True)
        if e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
        elif e.response.status_code == 401:
            return "Error: Invalid API key. Please check your API key."
        else:
            return f"Error: {e.response.status_code} - {e.response.text}"
    # Handle other exceptions (e.g., network issues)
    except Exception as e:
        logger.error(f"Error during SerpAPI search: {e}", exc_info=True)
        return f"Error: {str(e)}"

# Run the server
if __name__ == "__main__":
    logger.info("Starting serpapi MCP server")
    try:
        mcp.run()
        logger.info("serpapi MCP server stopped")
    except Exception as e:
        logger.error(f"Error running serpapi MCP server: {e}", exc_info=True)
        raise