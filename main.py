import os
import asyncio
import logging
import argparse
from datetime import datetime

from agents.coordination_agent import CoordinationAgent
from pipeline.workflow import PodcastWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', f'dopcast_{datetime.now().strftime("%Y%m%d")}.log'))
    ]
)

logger = logging.getLogger("dopcast.main")

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

async def run_api():
    """Run the FastAPI server for the DopCast API."""
    import uvicorn
    from api.main import app
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

async def run_web():
    """Run the Streamlit web interface."""
    import subprocess
    
    web_process = subprocess.Popen(
        ["streamlit", "run", "web/app.py", "--server.port=8501"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Log the process output
    while True:
        output = web_process.stdout.readline()
        if output == b'' and web_process.poll() is not None:
            break
        if output:
            logger.info(output.decode().strip())
    
    # Check for errors
    if web_process.returncode != 0:
        error = web_process.stderr.read().decode()
        logger.error(f"Streamlit process error: {error}")

async def generate_podcast(args):
    """Generate a podcast using the command line arguments."""
    workflow = PodcastWorkflow()
    
    # Prepare custom parameters
    custom_parameters = {}
    if args.episode_type:
        custom_parameters["episode_type"] = args.episode_type
    
    if args.duration:
        custom_parameters["content_planning"] = {
            "duration": args.duration * 60  # Convert to seconds
        }
    
    if args.technical_level:
        custom_parameters["technical_level"] = args.technical_level
    
    # Generate the podcast
    logger.info(f"Starting podcast generation for {args.sport}")
    result = await workflow.generate_podcast(
        sport=args.sport,
        trigger=args.trigger,
        event_id=args.event_id,
        custom_parameters=custom_parameters
    )
    
    logger.info(f"Podcast generation completed: {result}")
    return result

async def main():
    """Main entry point for the DopCast application."""
    parser = argparse.ArgumentParser(description="DopCast - AI-Powered Motorsport Podcasts")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # API command
    api_parser = subparsers.add_parser("api", help="Run the DopCast API server")
    
    # Web command
    web_parser = subparsers.add_parser("web", help="Run the DopCast web interface")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a podcast")
    generate_parser.add_argument("--sport", choices=["f1", "motogp"], required=True, help="Sport type")
    generate_parser.add_argument("--trigger", default="manual", help="Trigger event type")
    generate_parser.add_argument("--event-id", help="Specific event identifier")
    generate_parser.add_argument("--episode-type", choices=[
        "race_review", "qualifying_analysis", "news_update", "technical_deep_dive"
    ], help="Type of episode to create")
    generate_parser.add_argument("--duration", type=int, help="Target duration in minutes")
    generate_parser.add_argument("--technical-level", choices=["basic", "mixed", "advanced"], 
                                help="Level of technical detail")
    
    # Full command (API + Web)
    full_parser = subparsers.add_parser("full", help="Run both API and web interface")
    
    args = parser.parse_args()
    
    if args.command == "api":
        await run_api()
    elif args.command == "web":
        await run_web()
    elif args.command == "generate":
        await generate_podcast(args)
    elif args.command == "full":
        # Run both API and web interface
        await asyncio.gather(run_api(), run_web())
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
