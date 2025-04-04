#!/usr/bin/env python
"""
Test script for enhanced script generation with research data integration.
Skips voice synthesis and audio processing.

Usage:
    python test_enhanced_script_with_research.py --sport f1 --event-type race --event-id monaco_2023
"""

import argparse
import asyncio
import logging
import json
import os
from datetime import datetime

from agents.research import EnhancedResearchAgent
from agents.content_planning import EnhancedContentPlanningAgent
from agents.script_generation import EnhancedScriptGenerationAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("dopcast.test_enhanced_script")

async def main():
    """Run the enhanced script generation with research data integration."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test enhanced script generation with research data")
    parser.add_argument("--sport", default="f1", help="Sport type (f1 or motogp)")
    parser.add_argument("--event-type", default="race", help="Event type (race, qualifying, etc.)")
    parser.add_argument("--event-id", default="monaco_2023", help="Event identifier (e.g. monaco_2023)")
    parser.add_argument("--technical-level", default="mixed",
                       help="Technical detail level (basic, mixed, advanced)")
    args = parser.parse_args()
    
    # Ensure output directories exist
    os.makedirs("output", exist_ok=True)
    
    # Create timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"{args.sport}_{args.event_type}_{timestamp}"
    
    logger.info(f"Starting enhanced script generation with research data for {args.sport} {args.event_type} {args.event_id}")
    logger.info(f"Run ID: {run_id}")
    
    # Step 1: Enhanced Research
    logger.info("Step 1: Running enhanced research")
    research_agent = EnhancedResearchAgent()
    
    research_input = {
        "sport": args.sport,
        "event_type": args.event_type,
        "event_id": args.event_id,
        "force_refresh": True
    }
    
    research_result = await research_agent.process(research_input)
    
    if "error" in research_result:
        logger.error(f"Research failed: {research_result['error']}")
        return
    
    logger.info("Research completed successfully")
    
    # Step 2: Content Planning
    logger.info("Step 2: Running content planning")
    content_planning_agent = EnhancedContentPlanningAgent()
    
    content_planning_input = {
        "research_data": research_result,
        "sport": args.sport,
        "event_type": args.event_type,
        "event_id": args.event_id,
        "technical_level": args.technical_level
    }
    
    content_plan = await content_planning_agent.process(content_planning_input)
    
    if "error" in content_plan:
        logger.error(f"Content planning failed: {content_plan['error']}")
        return
    
    logger.info("Content planning completed successfully")
    
    # Step 3: Enhanced Script Generation with Research Data
    logger.info("Step 3: Running enhanced script generation with research data")
    script_generation_agent = EnhancedScriptGenerationAgent()
    
    script_input = {
        "content_outline": content_plan,
        "research_data": research_result,  # Pass the research data to the script generation agent
        "custom_parameters": {
            "script_style": "conversational",
            "humor_level": "moderate",
            "include_sound_effects": True,
            "include_transitions": True
        }
    }
    
    script = await script_generation_agent.process(script_input)
    
    if "error" in script:
        logger.error(f"Script generation failed: {script['error']}")
        return
    
    logger.info("Script generation completed successfully")
    
    # Save the final results
    results = {
        "run_id": run_id,
        "timestamp": timestamp,
        "sport": args.sport,
        "event_type": args.event_type,
        "event_id": args.event_id,
        "technical_level": args.technical_level,
        "research_report": research_result,
        "content_plan": content_plan,
        "script": script
    }
    
    results_dir = os.path.join("output", "test_results")
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = os.path.join(results_dir, f"test_results_{run_id}.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Test results saved to {results_file}")
    logger.info("Enhanced script generation with research data test completed successfully")
    
    # Print a summary of the script
    print("\n=== Script Summary ===")
    print(f"Title: {script.get('title', 'Untitled')}")
    print(f"Sport: {script.get('sport', 'Unknown')} - Event: {script.get('event_id', 'Unknown')}")
    print(f"Word Count: {script.get('word_count', 0)} words")
    print(f"Duration: {script.get('total_duration', 0)/60:.1f} minutes")
    print(f"Sections: {len(script.get('sections', []))}")
    print(f"File Paths: {script.get('file_paths', {})}")
    print("=====================\n")

if __name__ == "__main__":
    asyncio.run(main())
