from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import json

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reddit_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
google1_api_key = os.getenv('GOOGLE_API_KEY')
deepseek_api_key = os.getenv('DEEPSEE_API_KEY')
google2_api_key = os.getenv('LINKEDIN_GOOGLE_API_KEY')

# Automate server_params for each server
script_dir = os.path.dirname(os.path.abspath(__file__))
python_executable = sys.executable

server_params_reddit = StdioServerParameters(
    command=python_executable,
    args=[os.path.join(script_dir, "reddit_mcp_server.py")],
    env={"UV_PYTHON": "3.11", **os.environ},
)
server_params_twitter = StdioServerParameters(
    command=python_executable,
    args=[os.path.join(script_dir, "twitter_mcp_server.py")],
    env={"UV_PYTHON": "3.11", **os.environ},
)
server_params_serpapi = StdioServerParameters(
    command=python_executable,
    args=[os.path.join(script_dir, "serpapi_mcp_server.py")],
    env={"UV_PYTHON": "3.11", **os.environ},
)

try:
    logger.info("Starting reddit_agent.py")
    # Connect to MCP servers
    with MCPServerAdapter(server_params_reddit) as reddit_tools, \
         MCPServerAdapter(server_params_twitter) as twitter_tools, \
         MCPServerAdapter(server_params_serpapi) as serpapi_tools:
        logger.info(f"Loaded tools: {[tool.name for tool in reddit_tools + twitter_tools + serpapi_tools]}")

        # Define agents
        logger.debug("Defining Reddit agent")
        reddit_agent = Agent(
            role="Reddit Researcher",
            goal="Fetch posts and discussions from Reddit based on a title keyword search.",
            backstory="You use Reddit tools to search for posts and comments matching a given title keyword across all subreddits.",
            tools=reddit_tools,
            # verbose=True,
            llm=LLM(model='gemini/gemini-2.5-flash-preview-05-20', 
                    api_key=os.getenv("GOOGLE_API_KEY"))
        )

        logger.debug("Defining SerpApi agent")
        serpapi_agent = Agent(
            role="Web Search Researcher",
            goal="Fetch web search results based on a keyword search.",
            backstory="You use SerpApi tools to retrieve relevant web search results for a given keyword.",
            tools=serpapi_tools,
            # verbose=True,
            llm=LLM(model='gemini/gemini-2.5-flash-preview-05-20',
                     api_key=os.getenv("LINKEDIN_GOOGLE_API_KEY"))
        )

        logger.debug("Defining Twitter agent")
        twitter_agent = Agent(
            role="Twitter Researcher",
            goal="Fetch tweets based on a keyword search.",
            backstory="You use Twitter tools to retrieve tweets matching a given keyword.",
            tools=twitter_tools,
            # verbose=True,
            llm=LLM(model="deepseek-chat",
                    api_key=os.getenv("DEEPSEE_API_KEY"), 
                    base_url="https://api.deepseek.com")
        )

        # Define tasks
        logger.debug("Defining Reddit task")
        reddit_task = Task(
            description="Fetch recent posts and their top comments from Reddit based on a title keyword search.",
            expected_output="A JSON string containing posts and their discussions matching the title keyword.",
            agent=reddit_agent
        )

        logger.debug("Defining SerpApi task")
        serpapi_task = Task(
            description="Fetch web search results based on a keyword search.",
            expected_output  ="A JSON string containing web search results matching the keyword.",
            agent=serpapi_agent
        )

        logger.debug("Defining Twitter task")
        twitter_task = Task(
            description="Fetch recent tweets based on a keyword search.",
            expected_output="A JSON string containing tweets matching the keyword.",
            agent=twitter_agent
        )

        # Create and run crew
        logger.debug("Creating Crew")
        crew = Crew(
            agents=[reddit_agent, serpapi_agent, twitter_agent],
            tasks=[reddit_task, serpapi_task, twitter_task],
            process=Process.sequential,
            verbose=True
        )

        # Get keyword dynamically from user input
        logger.info("Prompting for keyword input")
        keyword = input("Enter the keyword to search: ").strip()
        logger.info(f"Received keyword: {keyword}")

        # Ensure inputs are properly formatted
        inputs = {"title_keyword": keyword, "keyword": keyword}
        logger.debug(f"Prepared inputs for Crew.kickoff: {json.dumps(inputs, indent=2)}")

        logger.info("Starting crew execution")
        try:
            result = crew.kickoff(inputs=inputs)
            logger.info("Crew execution completed")
            logger.info("\nFinal Result:")
            logger.info(result)
        except Exception as e:
            logger.error(f"Error during Crew.kickoff: {e}", exc_info=True)
            raise

except Exception as e:
    logger.error(f"Error in reddit_agent.py: {e}", exc_info=True)
    raise