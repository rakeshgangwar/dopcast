"""
Node functions for the Content Planning Agent LangGraph workflow.
Each function represents a node in the content planning workflow graph.
"""

import logging
import os
from typing import Dict, Any, List
from datetime import datetime

from ..tools.outline_generator import OutlineGeneratorTool
from ..tools.section_planner import SectionPlannerTool
from ..tools.talking_point_generator import TalkingPointGeneratorTool
from ..memory.outline_memory import OutlineMemory
from ..memory.template_memory import TemplateMemory

from .state import PlanningState

# Configure logging
logger = logging.getLogger(__name__)

# Initialize tools and memory components
# These will be properly initialized in the initialize_planning node
outline_generator = None
section_planner = None
talking_point_generator = None
outline_memory = None
template_memory = None

def initialize_planning(state: PlanningState) -> Dict[str, Any]:
    """
    Initialize the content planning workflow.

    Args:
        state: Current state

    Returns:
        Updated state
    """
    global outline_generator, section_planner, talking_point_generator, outline_memory, template_memory

    logger.info("Initializing content planning workflow")

    try:
        input_data = state["input_data"]

        # Set up data directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        output_dir = os.path.join(base_dir, "output")
        content_dir = os.path.join(output_dir, "content")

        # Ensure directories exist
        os.makedirs(content_dir, exist_ok=True)

        # Initialize tools
        outline_generator = OutlineGeneratorTool(content_dir)
        section_planner = SectionPlannerTool()
        talking_point_generator = TalkingPointGeneratorTool()

        # Initialize memory components
        outline_memory = OutlineMemory(content_dir)
        template_memory = TemplateMemory(content_dir)

        # Extract configuration parameters
        episode_type = input_data.get("episode_type", "race_review")
        custom_parameters = input_data.get("custom_parameters", {})

        # Set up configuration for the workflow
        config = {
            "episode_type": episode_type,
            "host_count": custom_parameters.get("host_count", 2),
            "content_tone": custom_parameters.get("content_tone", "conversational"),
            "technical_level": custom_parameters.get("technical_level", "mixed"),
            "target_audience": custom_parameters.get("target_audience", "general_fans"),
            "episode_duration": custom_parameters.get("duration", None)  # Will be set based on template
        }

        return {"config": config}

    except Exception as e:
        logger.error(f"Error initializing planning: {e}", exc_info=True)
        return {"error_info": f"Planning initialization failed: {str(e)}"}

def prepare_research_data(state: PlanningState) -> Dict[str, Any]:
    """
    Prepare research data for content planning.

    Args:
        state: Current state

    Returns:
        Updated state with prepared research data
    """
    logger.info("Preparing research data")

    try:
        input_data = state["input_data"]
        research_data = input_data.get("research_data", {})

        # Validate research data
        if not research_data:
            logger.error("No research data provided")
            return {"error_info": "No research data provided"}

        # Extract key information
        sport = research_data.get("sport", "unknown")
        event_type = research_data.get("event_type", "unknown")

        logger.info(f"Prepared research data for {sport} {event_type}")

        return {"research_data": research_data}

    except Exception as e:
        logger.error(f"Error preparing research data: {e}", exc_info=True)
        return {"error_info": f"Research data preparation failed: {str(e)}"}

def select_episode_format(state: PlanningState) -> Dict[str, Any]:
    """
    Select the episode format based on episode type.

    Args:
        state: Current state

    Returns:
        Updated state with episode format
    """
    logger.info("Selecting episode format")

    try:
        config = state.get("config", {})
        episode_type = config.get("episode_type", "race_review")

        # Get all templates
        templates = template_memory.get_all_templates()

        # Get the template for the episode type
        template = template_memory.get_template(episode_type)

        if not template:
            logger.warning(f"Template not found for episode type: {episode_type}, using race_review")
            template = template_memory.get_template("race_review")

        # Update episode duration if not specified
        if not config.get("episode_duration"):
            config["episode_duration"] = template["total_duration"]

        logger.info(f"Selected episode format: {episode_type}")

        return {
            "episode_format": template,
            "config": config
        }

    except Exception as e:
        logger.error(f"Error selecting episode format: {e}", exc_info=True)
        return {"error_info": f"Episode format selection failed: {str(e)}"}

def adjust_sections(state: PlanningState) -> Dict[str, Any]:
    """
    Adjust section durations based on target episode length.

    Args:
        state: Current state

    Returns:
        Updated state with adjusted sections
    """
    logger.info("Adjusting section durations")

    try:
        config = state.get("config", {})
        episode_format = state.get("episode_format", {})
        research_data = state.get("research_data", {})

        # Get sections from episode format
        sections = episode_format.get("sections", [])

        # Filter sections based on research data
        filtered_sections = section_planner.filter_sections(sections, research_data)

        # Adjust section durations
        target_duration = config.get("episode_duration", episode_format.get("total_duration", 1800))
        adjusted_sections = section_planner.adjust_section_durations(filtered_sections, target_duration)

        logger.info(f"Adjusted {len(adjusted_sections)} sections to target duration: {target_duration}s")

        return {"adjusted_sections": adjusted_sections}

    except Exception as e:
        logger.error(f"Error adjusting sections: {e}", exc_info=True)
        return {"error_info": f"Section adjustment failed: {str(e)}"}

def create_detailed_sections(state: PlanningState) -> Dict[str, Any]:
    """
    Create detailed sections with talking points.

    Args:
        state: Current state

    Returns:
        Updated state with detailed sections
    """
    logger.info("Creating detailed sections")

    try:
        config = state.get("config", {})
        adjusted_sections = state.get("adjusted_sections", [])
        research_data = state.get("research_data", {})

        # Extract parameters
        technical_level = config.get("technical_level", "mixed")
        host_count = config.get("host_count", 2)

        # Create detailed sections
        detailed_sections = []
        for section in adjusted_sections:
            detailed_section = talking_point_generator.create_detailed_section(
                section, research_data, technical_level, host_count
            )
            detailed_sections.append(detailed_section)

        logger.info(f"Created {len(detailed_sections)} detailed sections")

        return {"detailed_sections": detailed_sections}

    except Exception as e:
        logger.error(f"Error creating detailed sections: {e}", exc_info=True)
        return {"error_info": f"Detailed section creation failed: {str(e)}"}

def generate_content_plan(state: PlanningState) -> Dict[str, Any]:
    """
    Generate the final content plan.

    Args:
        state: Current state

    Returns:
        Updated state with content plan
    """
    logger.info("Generating content plan")

    try:
        config = state.get("config", {})
        research_data = state.get("research_data", {})
        episode_format = state.get("episode_format", {})
        detailed_sections = state.get("detailed_sections", [])

        # Extract parameters
        episode_type = config.get("episode_type", "race_review")
        technical_level = config.get("technical_level", "mixed")
        host_count = config.get("host_count", 2)

        # Create the content plan
        content_plan = outline_generator.create_outline(
            research_data, episode_type, episode_format, detailed_sections, technical_level, host_count
        )

        # Save the content plan
        filepath = outline_generator.save_outline(content_plan)

        # Add to outline memory
        outline_id = outline_memory.add_outline(content_plan, filepath)

        logger.info(f"Generated content plan with ID: {outline_id}")

        return {"content_plan": content_plan}

    except Exception as e:
        logger.error(f"Error generating content plan: {e}", exc_info=True)
        return {"error_info": f"Content plan generation failed: {str(e)}"}
