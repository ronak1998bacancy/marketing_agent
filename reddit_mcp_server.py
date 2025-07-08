#!/usr/bin/env python

import os
import json
from fastmcp import FastMCP
import praw
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reddit_mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Reddit client with environment variables
logger.debug("Loading Reddit environment variables")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "AIInsightAgent/1.0")

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# Create MCP server
logger.info("Creating Reddit MCP server")
mcp = FastMCP("reddit-server")

@mcp.tool()
async def fetch_posts_by_title(title_keyword: str, sort: str = "hot", limit: int = 3) -> str:
    """
    Fetch posts and their top comments from Reddit based on a title keyword search.

    Args:
        title_keyword: Keyword to search in post titles
        sort: Sort order (hot, new, top)
        limit: Number of posts to fetch (max 10)
    """
    logger.info(f"Fetching Reddit posts for keyword: {title_keyword}, sort: {sort}, limit: {limit}")
    try:
        posts = []
        for submission in reddit.subreddit("all").search(f"{title_keyword}", sort=sort, limit=min(limit, 5)):
            logger.debug(f"Processing Reddit post: {submission.id}")
            post_data = {
                "id": submission.id,
                "title": submission.title,
                "subreddit": submission.subreddit.display_name,
                "author": str(submission.author) if submission.author else "[deleted]",
                "score": submission.score,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
                "url": submission.url,
                "selftext": submission.selftext,
                "permalink": f"https://reddit.com{submission.permalink}"
            }
            # Fetch top 3 comments
            submission.comments.replace_more(limit=0)
            comments = [
                {
                    "id": comment.id,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "body": comment.body,
                    "score": comment.score,
                    "created_utc": comment.created_utc,
                    "permalink": f"https://reddit.com{comment.permalink}"
                }
                for comment in submission.comments.list()[:3]
            ]
            post_data["comments"] = comments
            posts.append(post_data)

        result = {
            "keyword": title_keyword,
            "sort": sort,
            "posts": posts,
            "count": len(posts)
        }
        logger.info(f"Successfully fetched {len(posts)} Reddit posts for keyword: {title_keyword}")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to fetch Reddit posts: {e}", exc_info=True)
        return json.dumps({"error": f"Failed to fetch posts: {str(e)}"}, indent=2)

if __name__ == "__main__":
    logger.info("Starting reddit MCP server")
    try:
        mcp.run()
        logger.info("reddit MCP server stopped")
    except Exception as e:
        logger.error(f"Error running reddit MCP server: {e}", exc_info=True)
        raise