import subprocess
import os
import sys
import time
import signal
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_name, processes):
    """Run a Python script in a subprocess and store the process."""
    logger.debug(f"Checking if {script_name} exists")
    if not os.path.exists(script_name):
        logger.error(f"Error: {script_name} not found")
        return
    try:
        logger.info(f"Starting {script_name}...")
        process = subprocess.Popen([sys.executable, script_name], env=os.environ)
        processes.append(process)
        logger.debug(f"Started {script_name} with PID {process.pid}")
    except Exception as e:
        logger.error(f"Error starting {script_name}: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting main.py")
    # List of scripts
    scripts = [
        "reddit_mcp_server.py",
        "twitter_mcp_server.py",
        "serpapi_mcp_server.py",
        "mcp_server.py"  # Proxy server
    ]

    # Store subprocesses for termination
    processes = []

    # Start all servers
    for script in scripts:
        run_script(script, processes)

    # Wait for servers to initialize
    logger.info("Waiting for servers to initialize...")
    time.sleep(10)  # Adjust as needed
    logger.debug("Finished waiting for server initialization")

    # Run reddit_agent.py
    try:
        logger.info("Starting reddit_agent.py...")
        agent_process = subprocess.Popen([sys.executable, "reddit_agent.py"], env=os.environ)
        logger.debug(f"Started reddit_agent.py with PID {agent_process.pid}")
        agent_process.wait()  # Wait for agent to complete
        logger.info("reddit_agent.py completed")
    except Exception as e:
        logger.error(f"Error running reddit_agent.py: {e}", exc_info=True)

    # Terminate servers on completion or interrupt
    try:
        logger.info("Shutting down servers...")
        for process in processes:
            logger.debug(f"Terminating process with PID {process.pid}")
            process.terminate()  # Send SIGTERM
            try:
                process.wait(timeout=5)  # Wait for graceful shutdown
                logger.info(f"Process with PID {process.pid} terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"Process with PID {process.pid} did not terminate, force killing")
                process.kill()  # Force kill if not terminated
                logger.info(f"Force killed process with PID {process.pid}")
        logger.info("All servers stopped.")
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt received, shutting down servers...")
        for process in processes:
            logger.debug(f"Terminating process with PID {process.pid} due to interrupt")
            process.terminate()
            try:
                process.wait(timeout=5)
                logger.info(f"Process with PID {process.pid} terminated gracefully")
            except subprocess.TimeoutExpired:
                logger.warning(f"Process with PID {process.pid} did not terminate, force killing")
                process.kill()
                logger.info(f"Force killed process with PID {process.pid}")
        logger.info("All servers stopped.")