# pipeline/graph.py
from typing import TypedDict, List, Dict, Any, Optional
import logging
from langgraph.graph import StateGraph, END, START

# Import agent classes
from agents.research import EnhancedResearchAgent  # Import the enhanced research agent
from agents.content_planning import EnhancedContentPlanningAgent  # Import the enhanced content planning agent
from agents.script_generation import EnhancedScriptGenerationAgent  # Import the enhanced script generation agent
from agents.voice_synthesis import EnhancedVoiceSynthesisAgent  # Import the enhanced voice synthesis agent
from agents.audio_production import EnhancedAudioProductionAgent  # Import the enhanced audio production agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DopCastState(TypedDict):
    """
    Represents the state of the DopCast podcast generation workflow.
    Keys are updated as the graph progresses.
    """
    # Input data for the workflow run
    initial_request: Dict[str, Any]

    # Outputs from each agent node
    research_results: Optional[Dict[str, Any]] = None
    content_plan: Optional[Dict[str, Any]] = None
    script_data: Optional[Dict[str, Any]] = None
    voice_synthesis_output: Optional[Dict[str, Any]] = None
    final_podcast_info: Optional[Dict[str, Any]] = None # Output from audio_production

    # Error tracking
    error_info: Optional[str] = None

# Instantiate agents (Consider dependency injection or a factory pattern for more complex scenarios)
research_agent = EnhancedResearchAgent()  # Use the enhanced research agent
content_planning_agent = EnhancedContentPlanningAgent()  # Use the enhanced content planning agent
script_generation_agent = EnhancedScriptGenerationAgent()  # Use the enhanced script generation agent
voice_synthesis_agent = EnhancedVoiceSynthesisAgent()  # Use the enhanced voice synthesis agent
audio_production_agent = EnhancedAudioProductionAgent()  # Use the enhanced audio production agent


# Initialize the StateGraph builder
graph_builder = StateGraph(DopCastState)

# --- Node Functions ---

async def run_research(state: DopCastState) -> Dict[str, Any]:
    """Node to execute the Research Agent."""
    logger.info("--- Running Research Node ---")
    try:
        initial_request = state['initial_request']
        sport = initial_request.get("sport", "f1")
        # Determine event_type from episode_type if possible, similar to CoordinationAgent
        episode_type = initial_request.get("custom_parameters", {}).get("episode_type", "race_review")
        event_type_cleaned = episode_type.replace("_review", "").replace("_analysis", "")
        event_id = initial_request.get("event_id")
        # Extract specific research params if any
        research_params = initial_request.get("custom_parameters", {}).get("research", {})

        agent_input = {
            "sport": sport,
            "event_type": event_type_cleaned,
            "event_id": event_id,
            "force_refresh": research_params.get("force_refresh", False)
        }
        logger.info(f"Research Agent Input: {agent_input}")
        result = await research_agent.run(agent_input)
        logger.info(f"Research Agent Output Keys: {result.keys()}")
        # Basic validation (can be expanded based on CoordinationAgent logic)
        if "error" in result:
             raise ValueError(f"Research step returned error: {result['error']}")
        # Add more validation if needed (e.g., min sources)

        return {"research_results": result}
    except Exception as e:
        logger.error(f"Error in Research Node: {e}", exc_info=True)
        return {"error_info": f"Research failed: {str(e)}"}

async def run_content_planning(state: DopCastState) -> Dict[str, Any]:
    """Node to execute the Content Planning Agent."""
    logger.info("--- Running Content Planning Node ---")
    if state.get("error_info"): return {} # Skip if previous step failed
    try:
        research_results = state.get("research_results")
        if not research_results:
            raise ValueError("Research results not found in state.")

        initial_request = state['initial_request']
        episode_type = initial_request.get("custom_parameters", {}).get("episode_type", "race_review")
        planning_params = initial_request.get("custom_parameters", {}).get("content_planning", {})

        agent_input = {
            "research_data": research_results,
            "episode_type": episode_type,
            "custom_parameters": planning_params
        }
        logger.info(f"Content Planning Agent Input Keys: {agent_input.keys()}")
        result = await content_planning_agent.run(agent_input)
        logger.info(f"Content Planning Agent Output Keys: {result.keys()}")
        if "error" in result:
             raise ValueError(f"Content Planning step returned error: {result['error']}")

        return {"content_plan": result}
    except Exception as e:
        logger.error(f"Error in Content Planning Node: {e}", exc_info=True)
        return {"error_info": f"Content Planning failed: {str(e)}"}

async def run_script_generation(state: DopCastState) -> Dict[str, Any]:
    """Node to execute the Script Generation Agent."""
    logger.info("--- Running Script Generation Node ---")
    if state.get("error_info"): return {}
    try:
        content_plan = state.get("content_plan")
        if not content_plan:
            raise ValueError("Content plan not found in state.")

        initial_request = state['initial_request']
        script_params = initial_request.get("custom_parameters", {}).get("script_generation", {})

        agent_input = {
            "content_outline": content_plan,
            "custom_parameters": script_params
        }
        logger.info(f"Script Generation Agent Input Keys: {agent_input.keys()}")
        result = await script_generation_agent.run(agent_input)
        logger.info(f"Script Generation Agent Output Keys: {result.keys()}")
        if "error" in result:
             raise ValueError(f"Script Generation step returned error: {result['error']}")
        # Add validation (e.g., word count)

        return {"script_data": result}
    except Exception as e:
        logger.error(f"Error in Script Generation Node: {e}", exc_info=True)
        return {"error_info": f"Script Generation failed: {str(e)}"}

async def run_voice_synthesis(state: DopCastState) -> Dict[str, Any]:
    """Node to execute the Voice Synthesis Agent."""
    logger.info("--- Running Voice Synthesis Node ---")
    if state.get("error_info"): return {}
    try:
        script_data = state.get("script_data")
        if not script_data:
            raise ValueError("Script data not found in state.")

        initial_request = state['initial_request']
        voice_params = initial_request.get("custom_parameters", {}).get("voice_synthesis", {})

        agent_input = {
            "script": script_data,
            "custom_parameters": voice_params
        }
        logger.info(f"Voice Synthesis Agent Input Keys: {agent_input.keys()}")
        result = await voice_synthesis_agent.run(agent_input)
        logger.info(f"Voice Synthesis Agent Output Keys: {result.keys()}")
        if "error" in result:
             raise ValueError(f"Voice Synthesis step returned error: {result['error']}")

        return {"voice_synthesis_output": result}
    except Exception as e:
        logger.error(f"Error in Voice Synthesis Node: {e}", exc_info=True)
        return {"error_info": f"Voice Synthesis failed: {str(e)}"}

async def run_audio_production(state: DopCastState) -> Dict[str, Any]:
    """Node to execute the Audio Production Agent."""
    logger.info("--- Running Audio Production Node ---")
    if state.get("error_info"): return {}
    try:
        voice_output = state.get("voice_synthesis_output")
        script_data = state.get("script_data") # Audio production might need script context
        if not voice_output or not script_data:
            raise ValueError("Voice synthesis output or script data not found in state.")

        initial_request = state['initial_request']
        audio_params = initial_request.get("custom_parameters", {}).get("audio_production", {})

        agent_input = {
            "audio_metadata": voice_output,
            "script": script_data,
            "custom_parameters": audio_params
        }
        logger.info(f"Audio Production Agent Input Keys: {agent_input.keys()}")
        result = await audio_production_agent.run(agent_input)
        logger.info(f"Audio Production Agent Output Keys: {result.keys()}")
        if "error" in result:
             raise ValueError(f"Audio Production step returned error: {result['error']}")

        # This is the final output of the main pipeline
        return {"final_podcast_info": result}
    except Exception as e:
        logger.error(f"Error in Audio Production Node: {e}", exc_info=True)
        return {"error_info": f"Audio Production failed: {str(e)}"}


# --- Add Nodes to Graph ---
graph_builder.add_node("research", run_research)
graph_builder.add_node("content_planning", run_content_planning)
graph_builder.add_node("script_generation", run_script_generation)
graph_builder.add_node("voice_synthesis", run_voice_synthesis)
graph_builder.add_node("audio_production", run_audio_production)

logger.info("Added agent nodes to the graph builder.")

# --- Define Edges ---

# Set the entry point
graph_builder.set_entry_point("research")

# Define the standard pipeline flow
graph_builder.add_edge("research", "content_planning")
graph_builder.add_edge("content_planning", "script_generation")
graph_builder.add_edge("script_generation", "voice_synthesis")
graph_builder.add_edge("voice_synthesis", "audio_production")

# Define a conditional edge to handle errors
# Note: The current node functions handle errors by checking state['error_info']
# and returning early, effectively stopping progression for that branch.
# A dedicated conditional edge could centralize this logic if preferred.

# Define the end point after the last main step
graph_builder.add_edge("audio_production", END)

logger.info("Defined graph edges.")

# --- Compile the Graph ---
# Add checkpointer for persistence if needed (e.g., MemorySaver, RedisSaver)
# from langgraph.checkpoint.memory import MemorySaver
# memory = MemorySaver()
# graph = graph_builder.compile(checkpointer=memory)
graph = graph_builder.compile()
logger.info("Compiled the LangGraph.")

# Example of how to invoke (will be used in workflow.py later)
# async def run_graph(input_data):
#     config = {"configurable": {"thread_id": "some_run_id"}}
#     async for event in graph.astream({"initial_request": input_data}, config=config):
#         # Process events (e.g., log node starts/ends)
#         print(event)
#     final_state = await graph.aget_state(config=config)
#     return final_state.values