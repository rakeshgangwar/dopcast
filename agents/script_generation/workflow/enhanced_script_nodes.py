"""
Enhanced node functions for the Script Generation Agent LangGraph workflow.
Each function represents a node in the script generation workflow graph.
"""

import logging
import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from ..tools.enhanced_dialogue_generator import EnhancedDialogueGeneratorTool
from ..tools.script_formatter import ScriptFormatterTool
from ..tools.sound_effect_manager import SoundEffectManagerTool
from ..memory.script_memory import ScriptMemory
from ..memory.host_memory import HostMemory

from .state import ScriptState

# Configure logging
logger = logging.getLogger(__name__)

# Initialize tools and memory components
# These will be properly initialized in the initialize_script_generation node
dialogue_generator = None
script_formatter = None
sound_effect_manager = None
script_memory = None
host_memory = None

def initialize_script_generation(state: ScriptState) -> Dict[str, Any]:
    """
    Initialize the script generation workflow.

    Args:
        state: Current state

    Returns:
        Updated state
    """
    global dialogue_generator, script_formatter, sound_effect_manager, script_memory, host_memory

    logger.info("Initializing script generation workflow")

    try:
        input_data = state["input_data"]
        custom_parameters = input_data.get("custom_parameters", {})

        # Set up data directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        output_dir = os.path.join(base_dir, "output")
        content_dir = os.path.join(output_dir, "script_generation")

        # Ensure directories exist
        os.makedirs(content_dir, exist_ok=True)

        # Initialize tools with custom LLM client configuration
        try:
            # Create a simple LLM client config
            llm_config = {
                "temperature": 0.7,
                "max_tokens": 1024
            }

            # Initialize the dialogue generator with a custom config
            dialogue_generator_config = {
                "use_cache": True,
                "llm_client": None  # We'll let the tool create its own client
            }
            dialogue_generator = EnhancedDialogueGeneratorTool(content_dir, dialogue_generator_config)

            # Initialize other tools
            script_formatter = ScriptFormatterTool(content_dir)
            sound_effect_manager = SoundEffectManagerTool()

            # Initialize memory components
            script_memory = ScriptMemory(content_dir)
            host_memory = HostMemory(content_dir)

            logger.info("Successfully initialized all script generation tools and components")
        except Exception as tool_error:
            logger.error(f"Error initializing tools: {str(tool_error)}")
            # Create fallback implementations to avoid NoneType errors
            if dialogue_generator is None:
                from ..tools.dialogue_generator import DialogueGeneratorTool
                dialogue_generator = DialogueGeneratorTool(content_dir)
            if script_formatter is None:
                script_formatter = ScriptFormatterTool(content_dir)
            if sound_effect_manager is None:
                sound_effect_manager = SoundEffectManagerTool()
            if script_memory is None:
                script_memory = ScriptMemory(content_dir)
            if host_memory is None:
                host_memory = HostMemory(content_dir)

        # Set up configuration for the workflow
        config = {
            "script_style": custom_parameters.get("script_style", "conversational"),
            "include_sound_effects": custom_parameters.get("include_sound_effects", True),
            "include_transitions": custom_parameters.get("include_transitions", True),
            "humor_level": custom_parameters.get("humor_level", "moderate"),
            "use_llm": custom_parameters.get("use_llm", True)
        }

        return {"config": config}

    except Exception as e:
        logger.error(f"Error initializing script generation: {e}", exc_info=True)
        return {"error_info": f"Script generation initialization failed: {str(e)}"}

def prepare_content_outline(state: ScriptState) -> Dict[str, Any]:
    """
    Prepare the content outline for script generation.

    Args:
        state: Current state

    Returns:
        Updated state with prepared content outline
    """
    logger.info("Preparing content outline")

    try:
        input_data = state["input_data"]
        content_outline = input_data.get("content_outline", {})

        # Validate content outline
        if not content_outline:
            logger.error("No content outline provided")
            return {"error_info": "No content outline provided"}

        logger.info(f"Prepared content outline for {content_outline.get('title', 'Untitled Episode')}")

        return {"content_outline": content_outline}

    except Exception as e:
        logger.error(f"Error preparing content outline: {e}", exc_info=True)
        return {"error_info": f"Content outline preparation failed: {str(e)}"}

def prepare_research_data(state: ScriptState) -> Dict[str, Any]:
    """
    Prepare research data for script generation.

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
            logger.warning("No research data provided, script may be generic")
            research_data = {}

        logger.info(f"Prepared research data for script generation")

        return {"research_data": research_data}

    except Exception as e:
        logger.error(f"Error preparing research data: {e}", exc_info=True)
        return {"error_info": f"Research data preparation failed: {str(e)}"}

def prepare_host_personalities(state: ScriptState) -> Dict[str, Any]:
    """
    Prepare host personalities for the script.

    Args:
        state: Current state

    Returns:
        Updated state with host personalities
    """
    logger.info("Preparing host personalities")

    try:
        content_outline = state.get("content_outline", {})
        host_count = content_outline.get("host_count", 2)

        # Get host personalities from memory or create default ones
        if host_memory is not None:
            try:
                host_personalities = host_memory.get_host_personalities(host_count)
            except Exception as mem_error:
                logger.warning(f"Error getting host personalities from memory: {str(mem_error)}")
                host_personalities = _create_default_host_personalities(host_count)
        else:
            logger.warning("Host memory is not initialized, using default host personalities")
            host_personalities = _create_default_host_personalities(host_count)

        logger.info(f"Prepared {len(host_personalities)} host personalities")

        return {"host_personalities": host_personalities}

    except Exception as e:
        logger.error(f"Error preparing host personalities: {e}", exc_info=True)
        return {"error_info": f"Host personality preparation failed: {str(e)}"}

def generate_script_sections(state: ScriptState) -> Dict[str, Any]:
    """
    Generate script sections with dialogue and sound effects.

    Args:
        state: Current state

    Returns:
        Updated state with script sections
    """
    logger.info("Generating script sections")

    try:
        content_outline = state.get("content_outline", {})
        host_personalities = state.get("host_personalities", [])
        config = state.get("config", {})
        research_data = state.get("research_data", {})

        # Ensure we have at least one host personality
        if not host_personalities:
            logger.warning("No host personalities provided, creating default hosts")
            host_personalities = _create_default_host_personalities(2)  # Default to 2 hosts

        # Extract parameters
        script_style = config.get("script_style", "conversational")
        humor_level = config.get("humor_level", "moderate")
        include_sound_effects = config.get("include_sound_effects", True)
        include_transitions = config.get("include_transitions", True)

        # Get sections from content outline
        sections = content_outline.get("sections", [])
        title = content_outline.get("title", "Untitled Episode")
        description = content_outline.get("description", "")

        # Create an event loop to run async functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Generate script for each section
        script_sections = []

        # Process sections asynchronously
        async def process_sections():
            nonlocal script_sections

            # Process all sections
            section_tasks = []
            for section in sections:
                # Ensure the section has talking points
                if "talking_points" not in section or not section["talking_points"]:
                    logger.warning(f"Section {section.get('name', 'unknown')} has no talking points, skipping")
                    continue

                task = generate_section_script(
                    section, host_personalities, script_style, humor_level,
                    include_sound_effects, include_transitions, research_data
                )
                section_tasks.append(task)

            # Wait for all section scripts to be generated
            if section_tasks:  # Only gather if there are tasks
                section_results = await asyncio.gather(*section_tasks)
                script_sections.extend(section_results)
            else:
                logger.warning("No valid sections to process")

            # Add intro if not already included
            if not any(s.get("name") == "intro" for s in script_sections):
                intro = await generate_intro_script(title, description, host_personalities, include_sound_effects, research_data)
                script_sections.insert(0, intro)

            # Add outro if not already included
            if not any(s.get("name") == "outro" for s in script_sections):
                outro = await generate_outro_script(host_personalities, include_sound_effects, title, research_data)
                script_sections.append(outro)

        # Run the async function in the event loop
        loop.run_until_complete(process_sections())
        loop.close()

        logger.info(f"Generated {len(script_sections)} script sections")

        return {"script_sections": script_sections}

    except Exception as e:
        logger.error(f"Error generating script sections: {e}", exc_info=True)
        return {"error_info": f"Script section generation failed: {str(e)}"}

def assemble_script(state: ScriptState) -> Dict[str, Any]:
    """
    Assemble the complete script from sections.

    Args:
        state: Current state

    Returns:
        Updated state with assembled script
    """
    logger.info("Assembling script")

    try:
        content_outline = state.get("content_outline", {})
        host_personalities = state.get("host_personalities", [])
        script_sections = state.get("script_sections", [])
        config = state.get("config", {})
        research_data = state.get("research_data", {})

        # Calculate script metrics
        if script_formatter is not None:
            try:
                metrics = script_formatter.calculate_script_metrics(script_sections)
            except Exception as metrics_error:
                logger.warning(f"Error calculating script metrics: {str(metrics_error)}")
                metrics = {"total_duration": 0, "word_count": 0}
        else:
            logger.warning("Script formatter is not initialized, using default metrics")
            # Calculate basic metrics manually
            word_count = sum(section.get("word_count", 0) for section in script_sections)
            total_duration = sum(section.get("duration", 0) for section in script_sections)
            metrics = {"total_duration": total_duration, "word_count": word_count}

        # Assemble the complete script
        script = {
            "title": content_outline.get("title", "Untitled Episode"),
            "description": content_outline.get("description", ""),
            "hosts": [host.get("name", "Host") for host in host_personalities] if host_personalities else ["Host"],
            "created_at": datetime.now().isoformat(),
            "script_style": config.get("script_style", "conversational"),
            "humor_level": config.get("humor_level", "moderate"),
            "sections": script_sections,
            "total_duration": metrics["total_duration"],
            "word_count": metrics["word_count"],
            "sport": content_outline.get("sport", research_data.get("sport", "unknown")),
            "episode_type": content_outline.get("episode_type", "unknown"),
            "event_id": research_data.get("event_id", "")
        }

        logger.info(f"Assembled complete script with {len(script_sections)} sections")

        return {"script": script}

    except Exception as e:
        logger.error(f"Error assembling script: {e}", exc_info=True)
        return {"error_info": f"Script assembly failed: {str(e)}"}

def format_script(state: ScriptState) -> Dict[str, Any]:
    """
    Format and save the script in multiple formats.

    Args:
        state: Current state

    Returns:
        Updated state with formatted script
    """
    logger.info("Formatting and saving script")

    try:
        script = state.get("script", {})
        file_paths = {}
        script_id = "unknown"

        # Save the script in multiple formats if formatter is available
        if script_formatter is not None:
            try:
                file_paths = script_formatter.save_script(script)
            except Exception as format_error:
                logger.warning(f"Error saving script with formatter: {str(format_error)}")
                # Create a basic JSON file as fallback
                output_dir = os.path.join("output", "script_generation", "json")
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_path = os.path.join(output_dir, f"script_{timestamp}.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    import json
                    json.dump(script, f, indent=2)
                file_paths = {"json": json_path}
        else:
            logger.warning("Script formatter is not initialized, saving basic JSON")
            # Create a basic JSON file as fallback
            output_dir = os.path.join("output", "script_generation", "json")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = os.path.join(output_dir, f"script_{timestamp}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                import json
                json.dump(script, f, indent=2)
            file_paths = {"json": json_path}

        # Add to script memory if available
        if script_memory is not None:
            try:
                script_id = script_memory.add_script(script, file_paths)
            except Exception as memory_error:
                logger.warning(f"Error adding script to memory: {str(memory_error)}")
                script_id = f"script_{timestamp}"
        else:
            logger.warning("Script memory is not initialized, using timestamp as ID")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_id = f"script_{timestamp}"

        # Add file paths to the script
        script["file_paths"] = file_paths
        script["script_id"] = script_id

        logger.info(f"Formatted and saved script with ID: {script_id}")

        return {"script": script}

    except Exception as e:
        logger.error(f"Error formatting script: {e}", exc_info=True)
        return {"error_info": f"Script formatting failed: {str(e)}"}

# Helper functions

def _create_default_host_personalities(host_count: int) -> List[Dict[str, Any]]:
    """
    Create default host personalities when memory is not available.

    Args:
        host_count: Number of hosts to create

    Returns:
        List of host personality definitions
    """
    default_hosts = [
        {
            "name": "Alex",
            "style": "enthusiastic",
            "role": "main_host",
            "expertise": "general",
            "catchphrases": ["Absolutely incredible!", "What a moment in motorsport!"],
            "voice_id": "default"
        },
        {
            "name": "Sam",
            "style": "analytical",
            "role": "co_host",
            "expertise": "technical",
            "catchphrases": ["Looking at the data...", "From a technical perspective..."],
            "voice_id": "default"
        },
        {
            "name": "Jamie",
            "style": "neutral",
            "role": "expert",
            "expertise": "historical",
            "catchphrases": ["Throughout the history of the sport...", "We've seen this before..."],
            "voice_id": "default"
        }
    ]

    # Return the requested number of hosts (minimum 1)
    return default_hosts[:max(1, min(host_count, len(default_hosts)))]

async def generate_section_script(section: Dict[str, Any], host_personalities: List[Dict[str, Any]],
                          script_style: str, humor_level: str,
                          include_sound_effects: bool, include_transitions: bool,
                          research_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate script for a single section.

    Args:
        section: Section from content outline
        host_personalities: List of host personality definitions
        script_style: Style of the script
        humor_level: Level of humor to include
        include_sound_effects: Whether to include sound effects
        include_transitions: Whether to include transitions
        research_data: Research data to incorporate

    Returns:
        Script for the section
    """
    section_name = section["name"]
    duration = section["duration"]
    talking_points = section.get("talking_points", [])

    # Generate dialogue lines
    dialogue_lines = []

    # Add transition if needed
    if include_transitions and section_name not in ["intro", "outro"]:
        dialogue_lines.append({
            "speaker": "TRANSITION",
            "text": f"Moving on to our {section_name.replace('_', ' ')} section."
        })

    # Process each talking point
    for point in talking_points:
        point_content = point["content"]
        host_index = point["host"]
        host = host_personalities[host_index % len(host_personalities)]

        # Generate dialogue for the talking point
        dialogue = await dialogue_generator.talking_point_to_dialogue(
            point_content, host, script_style, humor_level, research_data
        )

        dialogue_lines.append({
            "speaker": host["name"],
            "text": dialogue
        })

        # Generate a follow-up question from another host
        next_host_index = (host_index + 1) % len(host_personalities)
        next_host = host_personalities[next_host_index]

        follow_up_question = await dialogue_generator.generate_follow_up_question(
            point_content, next_host, research_data
        )

        dialogue_lines.append({
            "speaker": next_host["name"],
            "text": follow_up_question
        })

        # Generate a detailed response from the original host
        detailed_response = await dialogue_generator.generate_detailed_response(
            host, follow_up_question, point_content, research_data
        )

        dialogue_lines.append({
            "speaker": host["name"],
            "text": detailed_response
        })

    # Add sound effects
    sound_effects = sound_effect_manager.add_section_sound_effects(
        {"name": section_name, "dialogue": dialogue_lines},
        include_sound_effects
    )

    # Estimate word count (for timing purposes)
    word_count = sum(len(line["text"].split()) for line in dialogue_lines)

    # Create section script
    script_section = {
        "name": section_name,
        "duration": duration,
        "dialogue": dialogue_lines,
        "sound_effects": sound_effects,
        "word_count": word_count
    }

    return script_section

async def generate_intro_script(title: str, description: str,
                        host_personalities: List[Dict[str, Any]],
                        include_sound_effects: bool,
                        research_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate script for the episode introduction.

    Args:
        title: Episode title
        description: Episode description
        host_personalities: List of host personality definitions
        include_sound_effects: Whether to include sound effects
        research_data: Research data to incorporate

    Returns:
        Script for the intro section
    """
    # Generate dialogue lines
    dialogue_lines = await dialogue_generator.generate_intro_dialogue(
        title, description, host_personalities, research_data
    )

    # Add sound effects
    sound_effects = []
    if include_sound_effects:
        sound_effects.append({
            "type": "intro",
            "description": sound_effect_manager.get_effect_description("intro"),
            "position": 0
        })

    # Calculate word count
    word_count = sum(len(line["text"].split()) for line in dialogue_lines)

    return {
        "name": "intro",
        "duration": 60,  # Default intro duration
        "dialogue": dialogue_lines,
        "sound_effects": sound_effects,
        "word_count": word_count
    }

async def generate_outro_script(host_personalities: List[Dict[str, Any]],
                        include_sound_effects: bool, title: str,
                        research_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate script for the episode outro.

    Args:
        host_personalities: List of host personality definitions
        include_sound_effects: Whether to include sound effects
        title: Episode title
        research_data: Research data to incorporate

    Returns:
        Script for the outro section
    """
    # Generate dialogue lines
    dialogue_lines = await dialogue_generator.generate_outro_dialogue(
        host_personalities, title, research_data
    )

    # Add sound effects
    sound_effects = []
    if include_sound_effects:
        sound_effects.append({
            "type": "outro",
            "description": sound_effect_manager.get_effect_description("outro"),
            "position": 0
        })

    # Calculate word count
    word_count = sum(len(line["text"].split()) for line in dialogue_lines)

    return {
        "name": "outro",
        "duration": 45,  # Default outro duration
        "dialogue": dialogue_lines,
        "sound_effects": sound_effects,
        "word_count": word_count
    }
