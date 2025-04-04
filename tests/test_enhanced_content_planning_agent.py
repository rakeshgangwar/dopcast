"""
Test script for the Enhanced Content Planning Agent.
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.content_planning import EnhancedContentPlanningAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_content_planning_agent():
    """Test the enhanced content planning agent."""
    logger.info("Testing Enhanced Content Planning Agent")
    
    # Create the agent
    agent = EnhancedContentPlanningAgent()
    
    # Create mock research data
    research_data = {
        "sport": "f1",
        "event_type": "race",
        "status": "complete",
        "article_count": 10,
        "articles": [
            {
                "title": "Hamilton wins thrilling Monaco Grand Prix",
                "summary": "Lewis Hamilton secured a dramatic victory at the Monaco Grand Prix, holding off Max Verstappen in a tense finish.",
                "url": "https://example.com/f1/monaco-gp-results",
                "source": "F1 News"
            },
            {
                "title": "Ferrari struggles continue with double DNF",
                "summary": "Ferrari's difficult season continued with both cars retiring from the Monaco Grand Prix due to technical issues.",
                "url": "https://example.com/f1/ferrari-monaco-dnf",
                "source": "Motorsport News"
            },
            {
                "title": "Controversial penalty decides podium positions",
                "summary": "A late penalty for Max Verstappen changed the podium positions, with many questioning the stewards' decision.",
                "url": "https://example.com/f1/monaco-gp-penalty",
                "source": "Racing Updates"
            }
        ],
        "key_entities": {
            "drivers": ["Hamilton", "Verstappen", "Leclerc"],
            "teams": ["Mercedes", "Red Bull", "Ferrari"],
            "tracks": ["Monaco"]
        },
        "topics": {
            "race_results": [0],
            "controversy": [2],
            "technical": [1]
        }
    }
    
    # Test input data
    input_data = {
        "research_data": research_data,
        "episode_type": "race_review",
        "custom_parameters": {
            "duration": 1800,  # 30 minutes
            "technical_level": "mixed",
            "host_count": 2
        }
    }
    
    # Process the request
    logger.info(f"Processing content planning request: {input_data['episode_type']}")
    result = await agent.process(input_data)
    
    # Save the result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"content_plan_test_result_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Test result saved to {output_file}")
    
    # Print a summary of the result
    logger.info("Result summary:")
    logger.info(f"Title: {result.get('title')}")
    logger.info(f"Sport: {result.get('sport')}")
    logger.info(f"Episode type: {result.get('episode_type')}")
    logger.info(f"Duration: {result.get('duration')} seconds")
    logger.info(f"Number of sections: {len(result.get('sections', []))}")
    
    return result

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_enhanced_content_planning_agent())
