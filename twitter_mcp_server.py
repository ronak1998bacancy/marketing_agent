#!/usr/bin/env python

import os
import json
from fastmcp import FastMCP
import httpx
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/twitter_mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Twitter client
logger.debug("Loading Twitter environment variables")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Check if environment variable is set
if not TWITTER_BEARER_TOKEN:
    logger.error("TWITTER_BEARER_TOKEN environment variable not set")
    raise ValueError("TWITTER_BEARER_TOKEN environment variable not set")

# Create MCP server
logger.info("Creating Twitter MCP server")
mcp = FastMCP("twitter-server")

@mcp.tool()
async def fetch_tweets_by_keyword(keyword: str, limit: int = 3) -> str:
    """
    Fetch tweets based on a keyword search.

    Args:
        keyword: Keyword to search in tweets
        limit: Number of tweets to fetch (max 10)
    """
    logger.info(f"Fetching tweets for keyword: {keyword}, limit: {limit}")
    try:
        max_results = min(max(1, limit), 10)
        params = {
            "query": keyword,
            "max_results": max_results,
            "tweet.fields": "created_at,author_id,public_metrics",
            "expansions": "author_id",
            "user.fields": "username,name,profile_image_url"
        }
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
            logger.debug(f"Sending request to Twitter API with params: {params}")
            response = await client.get("https://api.twitter.com/2/tweets/search/recent", headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Received response from Twitter API: {result}")

        tweets = []
        users = {user["id"]: user for user in result.get("includes", {}).get("users", [])}
        for tweet in result.get("data", [])[:max_results]:
            user = users.get(tweet.get("author_id", ""), {})
            tweet_data = {
                "id": tweet.get("id", ""),
                "text": tweet.get("text", ""),
                "created_at": tweet.get("created_at", ""),
                "metrics": tweet.get("public_metrics", {}),
                "author": {
                    "username": f"@{user.get('username', 'unknown')}",
                    "name": user.get("name", "Unknown"),
                    "profile_image": user.get("profile_image_url", "")
                }
            }
            tweets.append(tweet_data)

        result = {
            "keyword": keyword,
            "tweets": tweets,
            "count": len(tweets)
        }
        logger.info(f"Successfully fetched {len(tweets)} tweets for keyword: {keyword}")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to fetch tweets: {e}", exc_info=True)
        return json.dumps({"error": f"Failed to fetch tweets: {str(e)}"}, indent=2)

if __name__ == "__main__":
    logger.info("Starting Twitter MCP server")
    try:
        mcp.run()
        logger.info("Twitter MCP server stopped")
    except Exception as e:
        logger.error(f"Error running Twitter MCP server: {e}", exc_info=True)
        raise