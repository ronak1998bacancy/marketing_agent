# server.py

from fastmcp import FastMCP
import asyncio
import httpx
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("Creating MCP server")
mcp = FastMCP("mcp-server")

# Proxy endpoints for each server
REDDIT_SERVER_URL = "http://localhost:8001"
TWITTER_SERVER_URL = "http://localhost:8002"
SERPAPI_SERVER_URL = "http://localhost:8003"

@mcp.tool()
async def fetch_posts_by_title(
    title_keyword: str,
    sort: str = "hot",
    limit: int = 3
) -> str:
    logger.info(f"Proxying Reddit request for title_keyword: {title_keyword}, sort: {sort}, limit: {limit}")
    async with httpx.AsyncClient() as client:
        logger.debug(f"Sending request to {REDDIT_SERVER_URL}/fetch_posts_by_title")
        response = await client.post(
            f"{REDDIT_SERVER_URL}/fetch_posts_by_title",
            json={"title_keyword": title_keyword, "sort": sort, "limit": limit}
        )
        logger.debug(f"Received response from Reddit server: {response.text}")
        response.raise_for_status()
        logger.info(f"Successfully proxied Reddit request for title_keyword: {title_keyword}")
        return response.text

@mcp.tool()
async def fetch_tweets_by_keyword(
    keyword: str,
    limit: int = 3
) -> str:
    logger.info(f"Proxying Twitter request for keyword: {keyword}, limit: {limit}")
    async with httpx.AsyncClient() as client:
        logger.debug(f"Sending request to {TWITTER_SERVER_URL}/fetch_tweets_by_keyword")
        response = await client.post(
            f"{TWITTER_SERVER_URL}/fetch_tweets_by_keyword",
            json={"keyword": keyword, "limit": limit}
        )
        logger.debug(f"Received response from Twitter server: {response.text}")
        response.raise_for_status()
        logger.info(f"Successfully proxied Twitter request for keyword: {keyword}")
        return response.text

@mcp.tool()
async def search(params: dict, limit: int = 3) -> str:
    logger.info(f"Proxying SerpAPI search request with params: {params}")
    async with httpx.AsyncClient() as client:
        logger.debug(f"Sending request to {SERPAPI_SERVER_URL}/search")
        response = await client.post(
            f"{SERPAPI_SERVER_URL}/search",
            json=params
        )
        logger.debug(f"Received response from SerpAPI server: {response.text}")
        response.raise_for_status()
        logger.info("Successfully proxied SerpAPI search request")
        return response.text

if __name__ == "__main__":
    logger.info("Starting MCP proxy server")
    mcp.run()
    logger.info("MCP server stopped")
