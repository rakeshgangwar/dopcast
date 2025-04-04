"""
Test script for the Enhanced Research Agent.
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.research import EnhancedResearchAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_research_agent():
    """Test the enhanced research agent."""
    logger.info("Testing Enhanced Research Agent")

    # Create the agent
    agent = EnhancedResearchAgent()

    # Test input data
    input_data = {
        "sport": "f1",
        "event_type": "race",
        "event_id": "monaco_2023",
        "force_refresh": True
    }

    # Process the request
    logger.info(f"Processing research request: {input_data}")
    result = await agent.process(input_data)

    # Save the result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "test_results")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"research_test_result_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Test result saved to {output_file}")

    # Print a summary of the result
    logger.info("Result summary:")
    logger.info(f"Sport: {result.get('sport')}")
    logger.info(f"Event type: {result.get('event_type')}")
    logger.info(f"Status: {result.get('status')}")
    logger.info(f"Article count: {result.get('article_count')}")
    logger.info(f"Entity types: {', '.join(result.get('entities', {}).keys())}")
    logger.info(f"Number of trends: {len(result.get('trends', []))}")
    logger.info(f"Number of key stories: {len(result.get('key_stories', []))}")

    return result

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_research_agent())
