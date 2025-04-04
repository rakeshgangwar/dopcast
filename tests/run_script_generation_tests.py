"""
Run all script generation tests.
This script runs all the tests for the script generation components.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import test functions
from test_gemini_dialogue_generator import test_gemini_dialogue_generator, test_full_script_generation
from test_enhanced_script_generation_agent import test_enhanced_script_generation_agent

async def run_all_tests():
    """Run all script generation tests."""
    logger.info("Running all script generation tests")
    
    # Check if Google API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.warning("GOOGLE_API_KEY environment variable not set")
        logger.info("For LLM-based tests to work properly, set your Google API key with: export GOOGLE_API_KEY='your-api-key'")
        logger.info("Tests will fall back to template-based generation")
    
    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "test_results", timestamp)
    os.makedirs(results_dir, exist_ok=True)
    
    # Run tests
    try:
        logger.info("Running test_gemini_dialogue_generator")
        dialogue_result = await test_gemini_dialogue_generator()
        logger.info("Completed test_gemini_dialogue_generator")
    except Exception as e:
        logger.error(f"Error in test_gemini_dialogue_generator: {e}", exc_info=True)
    
    try:
        logger.info("Running test_full_script_generation")
        script_result = await test_full_script_generation()
        logger.info("Completed test_full_script_generation")
    except Exception as e:
        logger.error(f"Error in test_full_script_generation: {e}", exc_info=True)
    
    try:
        logger.info("Running test_enhanced_script_generation_agent")
        agent_result = await test_enhanced_script_generation_agent()
        logger.info("Completed test_enhanced_script_generation_agent")
    except Exception as e:
        logger.error(f"Error in test_enhanced_script_generation_agent: {e}", exc_info=True)
    
    logger.info("All tests completed")
    logger.info(f"Results saved to {results_dir}")

if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
