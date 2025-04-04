#!/usr/bin/env python
"""
Script to test the LangGraph-based DopCast workflow with real-world data.
This script clears the cache and forces a refresh of data.
"""

import argparse
import asyncio
import logging
import json
import os
import shutil
from pipeline.workflow import PodcastWorkflow
from agents.research.memory.cache_memory import CacheMemory

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("dopcast.real_runner")

async def clear_caches():
    """Clear all caches to ensure fresh data collection."""
    # Clear research cache
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(base_dir, "output", "data", "cache")
    
    if os.path.exists(cache_dir):
        logger.info(f"Clearing research cache in {cache_dir}")
        cache_memory = CacheMemory(cache_dir)
        cache_memory.clear()
    else:
        logger.warning(f"Cache directory not found: {cache_dir}")

async def main():
    """Run the DopCast workflow with real-world data."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the DopCast workflow with real-world data")
    parser.add_argument("--sport", default="f1", help="Sport type (f1 or motogp)")
    parser.add_argument("--trigger", default="manual", help="Trigger type (manual, race, etc.)")
    parser.add_argument("--event-id", help="Event identifier (e.g. monaco_2023)")
    parser.add_argument("--episode-type", default="race_review",
                       help="Episode type (race_review, qualifying_analysis, etc.)")
    parser.add_argument("--technical-level", default="mixed",
                       help="Technical detail level (basic, mixed, advanced)")
    args = parser.parse_args()
    
    # Clear caches to ensure fresh data
    await clear_caches()
    
    # Create custom parameters from command line arguments
    custom_parameters = {
        "episode_type": args.episode_type,
        "technical_level": args.technical_level,
        # Force refresh to ensure real-world data collection
        "force_refresh": True
    }
    
    logger.info(f"Initializing workflow for {args.sport} - {args.event_id} with REAL data")
    
    # Initialize the workflow
    workflow = PodcastWorkflow()
    
    # Generate podcast
    logger.info("Starting podcast generation with REAL data...")
    result = await workflow.generate_podcast(
        sport=args.sport,
        trigger=args.trigger,
        event_id=args.event_id,
        custom_parameters=custom_parameters
    )
    
    # Display results
    logger.info("Podcast generation completed!")
    print("\n" + "="*50)
    print("REAL WORKFLOW RESULT")
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
            audio_file = podcast_info.get("file", {})
            if audio_file:
                print("\nAudio File:")
                print(f" - Format: {audio_file.get('format')} | Path: {audio_file.get('path')}")
    else:
        logger.error(f"Failed to generate podcast: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
