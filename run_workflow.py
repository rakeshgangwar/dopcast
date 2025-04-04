#!/usr/bin/env python
"""
Script to test the LangGraph-based DopCast workflow.
Usage:
    python run_workflow.py --sport f1 --event-id monaco_2023 --episode-type race_review
"""

import argparse
import asyncio
import logging
import json
from pipeline.workflow import PodcastWorkflow

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("dopcast.runner")

async def main():
    """Run the DopCast workflow with the provided arguments."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the DopCast workflow")
    parser.add_argument("--sport", default="f1", help="Sport type (f1 or motogp)")
    parser.add_argument("--trigger", default="manual", help="Trigger type (manual, race, etc.)")
    parser.add_argument("--event-id", help="Event identifier (e.g. monaco_2023)")
    parser.add_argument("--episode-type", default="race_review",
                       help="Episode type (race_review, qualifying_analysis, etc.)")
    parser.add_argument("--technical-level", default="mixed",
                       help="Technical detail level (basic, mixed, advanced)")
    args = parser.parse_args()
    
    # Create custom parameters from command line arguments
    custom_parameters = {
        "episode_type": args.episode_type,
        "technical_level": args.technical_level
    }
    
    logger.info(f"Initializing workflow for {args.sport} - {args.event_id}")
    
    # Initialize the workflow
    workflow = PodcastWorkflow()
    
    # Generate podcast
    logger.info("Starting podcast generation...")
    result = await workflow.generate_podcast(
        sport=args.sport,
        trigger=args.trigger,
        event_id=args.event_id,
        custom_parameters=custom_parameters
    )
    
    # Display results
    logger.info("Podcast generation completed!")
    print("\n" + "="*50)
    print("WORKFLOW RESULT")
    print("="*50)
    print(json.dumps(result, indent=2))
    print("="*50)
    
    # Indicate if podcast was successfully generated
    if "error" not in result:
        logger.info(f"Success! Generated podcast with run_id: {result.get('run_id')}")
        
        # Display podcast details if available
        podcast_info = result.get("podcast", {})
        if podcast_info:
            print("\n--- PODCAST DETAILS ---")
            print(f"Title: {podcast_info.get('title', 'Untitled')}")
            print(f"Duration: {podcast_info.get('duration', 0)} seconds")
            
            # Display audio file paths if available
            audio_files = podcast_info.get("audio_files", [])
            if audio_files:
                print("\nAudio Files:")
                for audio_file in audio_files:
                    print(f" - Format: {audio_file.get('format')} | Path: {audio_file.get('path')}")
    else:
        logger.error(f"Failed to generate podcast: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())