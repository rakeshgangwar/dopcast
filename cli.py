#!/usr/bin/env python

import os
import sys
import argparse
import asyncio
import logging
from datetime import datetime, timedelta

from pipeline.workflow import PodcastWorkflow
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('logs', f'dopcast_cli_{datetime.now().strftime("%Y%m%d")}.log'))
    ]
)

logger = logging.getLogger("dopcast.cli")

async def generate_podcast(args):
    """
    Generate a podcast based on command-line arguments.
    """
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
    
    if args.hosts:
        custom_parameters["content_planning"] = custom_parameters.get("content_planning", {})
        custom_parameters["content_planning"]["host_count"] = len(args.hosts.split(","))
    
    # Generate the podcast
    logger.info(f"Starting podcast generation for {args.sport}")
    print(f"\nGenerating podcast for {args.sport.upper()}...")
    print("This may take several minutes. Please wait...\n")
    
    result = await workflow.generate_podcast(
        sport=args.sport,
        trigger=args.trigger,
        event_id=args.event_id,
        custom_parameters=custom_parameters
    )
    
    if "error" in result:
        print(f"\nError generating podcast: {result['error']}")
        return 1
    
    print("\nPodcast generated successfully!")
    print(f"Output file: {result.get('podcast_file', 'Unknown')}")
    print(f"Duration: {result.get('duration', 0)/60:.1f} minutes")
    
    return 0

async def schedule_podcast(args):
    """
    Schedule a podcast for future generation.
    """
    workflow = PodcastWorkflow()
    
    # Parse schedule time
    if args.time:
        hours, minutes = map(int, args.time.split(':'))
        schedule_time = datetime.now().replace(hour=hours, minute=minutes)
        
        # If the time is in the past, schedule for tomorrow
        if schedule_time < datetime.now():
            schedule_time += timedelta(days=1)
    else:
        # Default to 1 hour from now
        schedule_time = datetime.now() + timedelta(hours=1)
    
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
    
    # Schedule the podcast
    logger.info(f"Scheduling podcast generation for {args.sport} at {schedule_time}")
    print(f"\nScheduling podcast for {args.sport.upper()} at {schedule_time}...")
    
    result = await workflow.schedule_podcast(
        sport=args.sport,
        trigger=args.trigger,
        schedule_time=schedule_time,
        event_id=args.event_id,
        custom_parameters=custom_parameters
    )
    
    print("\nPodcast scheduled successfully!")
    print(f"Schedule ID: {result.get('schedule_id', 'Unknown')}")
    print(f"Scheduled for: {schedule_time}")
    
    return 0

async def list_podcasts(args):
    """
    List recent and scheduled podcasts.
    """
    workflow = PodcastWorkflow()
    
    if args.scheduled:
        # List scheduled podcasts
        scheduled = await workflow.list_scheduled_runs(args.sport if args.sport != "all" else None)
        
        print("\nScheduled Podcasts:")
        if not scheduled:
            print("No scheduled podcasts found.")
        else:
            print(f"{'ID':<20} {'Sport':<10} {'Trigger':<15} {'Schedule Time':<25}")
            print("-" * 70)
            for run in scheduled:
                print(f"{run['id']:<20} {run['sport']:<10} {run['trigger']:<15} {run['schedule_time']:<25}")
    else:
        # List recent podcasts
        recent = await workflow.list_runs(args.limit, args.sport if args.sport != "all" else None)
        
        print("\nRecent Podcasts:")
        if not recent:
            print("No recent podcasts found.")
        else:
            print(f"{'Run ID':<20} {'Sport':<10} {'Status':<10} {'Started At':<25} {'Duration':<10}")
            print("-" * 75)
            for run in recent:
                duration = run.get("result", {}).get("duration", 0)
                duration_str = f"{duration/60:.1f} min" if duration else "N/A"
                print(f"{run['run_id']:<20} {run.get('sport', 'N/A'):<10} {run['status']:<10} {run['started_at']:<25} {duration_str:<10}")
    
    return 0

async def cancel_scheduled(args):
    """
    Cancel a scheduled podcast.
    """
    workflow = PodcastWorkflow()
    
    logger.info(f"Cancelling scheduled podcast: {args.schedule_id}")
    print(f"\nCancelling scheduled podcast: {args.schedule_id}...")
    
    result = await workflow.cancel_scheduled_run(args.schedule_id)
    
    if "error" in result:
        print(f"\nError: {result['error']}")
        return 1
    
    print("\nScheduled podcast cancelled successfully!")
    return 0

async def main():
    parser = argparse.ArgumentParser(description="DopCast - AI-Powered Motorsport Podcasts CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a podcast")
    generate_parser.add_argument("--sport", choices=["f1", "motogp"], required=True, help="Sport type")
    generate_parser.add_argument("--trigger", default="manual", help="Trigger event type")
    generate_parser.add_argument("--event-id", help="Specific event identifier")
    generate_parser.add_argument("--episode-type", choices=[
        "race_review", "qualifying_analysis", "news_update", "technical_deep_dive"
    ], help="Type of episode to create")
    generate_parser.add_argument("--duration", type=int, default=30, help="Target duration in minutes")
    generate_parser.add_argument("--technical-level", choices=["basic", "mixed", "advanced"], 
                                default="mixed", help="Level of technical detail")
    generate_parser.add_argument("--hosts", help="Comma-separated list of host names")
    
    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Schedule a podcast for future generation")
    schedule_parser.add_argument("--sport", choices=["f1", "motogp"], required=True, help="Sport type")
    schedule_parser.add_argument("--trigger", default="manual", help="Trigger event type")
    schedule_parser.add_argument("--event-id", help="Specific event identifier")
    schedule_parser.add_argument("--time", help="Time to schedule (HH:MM)")
    schedule_parser.add_argument("--episode-type", choices=[
        "race_review", "qualifying_analysis", "news_update", "technical_deep_dive"
    ], help="Type of episode to create")
    schedule_parser.add_argument("--duration", type=int, default=30, help="Target duration in minutes")
    schedule_parser.add_argument("--technical-level", choices=["basic", "mixed", "advanced"], 
                                default="mixed", help="Level of technical detail")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List podcasts")
    list_parser.add_argument("--scheduled", action="store_true", help="List scheduled podcasts")
    list_parser.add_argument("--sport", default="all", choices=["all", "f1", "motogp"], help="Filter by sport")
    list_parser.add_argument("--limit", type=int, default=10, help="Maximum number of podcasts to list")
    
    # Cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a scheduled podcast")
    cancel_parser.add_argument("schedule_id", help="Schedule ID to cancel")
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize the DopCast system")
    init_parser.add_argument("--force", action="store_true", help="Force reinitialization")
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == "generate":
        return await generate_podcast(args)
    elif args.command == "schedule":
        return await schedule_podcast(args)
    elif args.command == "list":
        return await list_podcasts(args)
    elif args.command == "cancel":
        return await cancel_scheduled(args)
    elif args.command == "init":
        # Import here to avoid circular imports
        from initialize import initialize_system
        initialize_system(args.force)
        return 0
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        sys.exit(1)
