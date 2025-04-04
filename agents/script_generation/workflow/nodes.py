"""
Node functions for the Script Generation Agent LangGraph workflow.
Each function represents a node in the script generation workflow graph.
"""

import logging
import os
from typing import Dict, Any, List
from datetime import datetime

from ..tools.dialogue_generator import DialogueGeneratorTool
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
        
        # Set up data directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        content_dir = os.path.join(base_dir, "content")
        
        # Ensure directories exist
        os.makedirs(content_dir, exist_ok=True)
        
        # Initialize tools
        dialogue_generator = DialogueGeneratorTool()
        script_formatter = ScriptFormatterTool(content_dir)
        sound_effect_manager = SoundEffectManagerTool()
        
        # Initialize memory components
        script_memory = ScriptMemory(content_dir)
        host_memory = HostMemory(content_dir)
        
        # Extract configuration parameters
        custom_parameters = input_data.get("custom_parameters", {})
        
        # Set up configuration for the workflow
        config = {
            "script_style": custom_parameters.get("script_style", "conversational"),
            "include_sound_effects": custom_parameters.get("include_sound_effects", True),
            "include_transitions": custom_parameters.get("include_transitions", True),
            "humor_level": custom_parameters.get("humor_level", "moderate")
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

def prepare_host_personalities(state: ScriptState) -> Dict[str, Any]:
    """
    Prepare host personalities for script generation.
    
    Args:
        state: Current state
        
    Returns:
        Updated state with host personalities
    """
    logger.info("Preparing host personalities")
    
    try:
        content_outline = state.get("content_outline", {})
        host_count = content_outline.get("host_count", 2)
        
        # Get all hosts
        all_hosts = host_memory.get_all_hosts()
        
        # Ensure we have enough host personalities
        host_personalities = []
        
        # First, try to find a lead host
        lead_hosts = host_memory.get_hosts_by_role("lead_host")
        if lead_hosts:
            host_personalities.append(lead_hosts[0])
        
        # Then, try to find technical experts
        if len(host_personalities) < host_count:
            technical_hosts = host_memory.get_hosts_by_role("technical_expert")
            for host in technical_hosts:
                if host["name"] not in [h["name"] for h in host_personalities]:
                    host_personalities.append(host)
                    if len(host_personalities) >= host_count:
                        break
        
        # Finally, add any remaining hosts needed
        if len(host_personalities) < host_count:
            for host_name, host_info in all_hosts.items():
                host = host_memory.get_host(host_name)
                if host and host["name"] not in [h["name"] for h in host_personalities]:
                    host_personalities.append(host)
                    if len(host_personalities) >= host_count:
                        break
        
        # If we still don't have enough hosts, create generic ones
        if len(host_personalities) < host_count:
            for i in range(len(host_personalities), host_count):
                generic_host = {
                    "name": f"Host {i+1}",
                    "role": "co_host",
                    "style": "neutral",
                    "expertise": "general",
                    "catchphrases": []
                }
                host_personalities.append(generic_host)
        
        logger.info(f"Prepared {len(host_personalities)} host personalities")
        
        return {"host_personalities": host_personalities}
    
    except Exception as e:
        logger.error(f"Error preparing host personalities: {e}", exc_info=True)
        return {"error_info": f"Host personality preparation failed: {str(e)}"}

def generate_script_sections(state: ScriptState) -> Dict[str, Any]:
    """
    Generate script sections from the content outline.
    
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
        
        # Extract parameters
        script_style = config.get("script_style", "conversational")
        humor_level = config.get("humor_level", "moderate")
        include_sound_effects = config.get("include_sound_effects", True)
        include_transitions = config.get("include_transitions", True)
        
        # Get sections from content outline
        sections = content_outline.get("sections", [])
        
        # Generate script for each section
        script_sections = []
        
        for section in sections:
            script_section = generate_section_script(
                section, host_personalities, script_style, humor_level,
                include_sound_effects, include_transitions
            )
            script_sections.append(script_section)
        
        # Add intro and outro if not already included
        if not any(s.get("name") == "intro" for s in script_sections):
            title = content_outline.get("title", "Untitled Episode")
            description = content_outline.get("description", "")
            intro = generate_intro_script(title, description, host_personalities, include_sound_effects)
            script_sections.insert(0, intro)
        
        if not any(s.get("name") == "outro" for s in script_sections):
            outro = generate_outro_script(host_personalities, include_sound_effects)
            script_sections.append(outro)
        
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
        Updated state with complete script
    """
    logger.info("Assembling complete script")
    
    try:
        content_outline = state.get("content_outline", {})
        host_personalities = state.get("host_personalities", [])
        script_sections = state.get("script_sections", [])
        config = state.get("config", {})
        
        # Calculate script metrics
        metrics = script_formatter.calculate_script_metrics(script_sections)
        
        # Assemble the complete script
        script = {
            "title": content_outline.get("title", "Untitled Episode"),
            "description": content_outline.get("description", ""),
            "hosts": [host["name"] for host in host_personalities],
            "created_at": datetime.now().isoformat(),
            "script_style": config.get("script_style", "conversational"),
            "humor_level": config.get("humor_level", "moderate"),
            "sections": script_sections,
            "total_duration": metrics["total_duration"],
            "word_count": metrics["word_count"],
            "sport": content_outline.get("sport", "unknown"),
            "episode_type": content_outline.get("episode_type", "unknown")
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
        
        # Save the script in multiple formats
        file_paths = script_formatter.save_script(script)
        
        # Add to script memory
        script_id = script_memory.add_script(script, file_paths)
        
        # Add file paths to the script
        script["file_paths"] = file_paths
        script["script_id"] = script_id
        
        logger.info(f"Formatted and saved script with ID: {script_id}")
        
        return {"script": script}
    
    except Exception as e:
        logger.error(f"Error formatting script: {e}", exc_info=True)
        return {"error_info": f"Script formatting failed: {str(e)}"}

# Helper functions

def generate_section_script(section: Dict[str, Any], host_personalities: List[Dict[str, Any]],
                          script_style: str, humor_level: str,
                          include_sound_effects: bool, include_transitions: bool) -> Dict[str, Any]:
    """
    Generate script for a single section.
    
    Args:
        section: Section from content outline
        host_personalities: List of host personality definitions
        script_style: Style of the script
        humor_level: Level of humor to include
        include_sound_effects: Whether to include sound effects
        include_transitions: Whether to include transitions
        
    Returns:
        Script for the section
    """
    section_name = section.get("name", "unnamed_section")
    talking_points = section.get("talking_points", [])
    duration = section.get("duration", 60)  # Default 60 seconds
    
    # Enhanced implementation to generate more detailed dialogue
    dialogue_lines = []
    
    # Add section transition if enabled
    if include_transitions and section_name != "intro":
        dialogue_lines.append(sound_effect_manager.add_transition_effect(section_name))
    
    # Add section introduction by the primary host
    if len(host_personalities) > 0 and section_name not in ["intro", "outro"]:
        primary_host = host_personalities[0]
        section_intro = f"Let's move on to {section_name.replace('_', ' ').title()}. "
        
        if section_name == "headlines":
            section_intro += "Here are the top stories making news in the motorsport world this week."
        elif section_name == "detailed_stories":
            section_intro += "Now let's dive deeper into some of these stories and explore their implications."
        elif section_name == "analysis":
            section_intro += "I think it's time we analyze what these developments mean for the sport going forward."
        elif section_name == "key_moments":
            section_intro += "There were several defining moments that shaped the outcome of this event."
        elif section_name == "driver_performances":
            section_intro += "Let's take a closer look at how some of the drivers performed under pressure."
        elif section_name == "team_strategies":
            section_intro += "The strategic decisions made by the teams played a crucial role in the final results."
        
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": section_intro
        })
    
    # Generate dialogue for each talking point with expanded content
    for i, point in enumerate(talking_points):
        point_content = point.get("content", "")
        host_index = point.get("host", i % len(host_personalities))
        host = host_personalities[host_index]
        
        # Convert talking point to natural dialogue
        dialogue = dialogue_generator.talking_point_to_dialogue(
            point_content, host, script_style, humor_level
        )
        
        dialogue_lines.append({
            "speaker": host["name"],
            "text": dialogue
        })
        
        # Add interaction between hosts
        if i < len(talking_points) - 1 and script_style == "conversational":
            next_host_index = talking_points[i+1].get("host", (i+1) % len(host_personalities))
            if next_host_index != host_index:
                # Add a detailed response or handoff
                next_host = host_personalities[next_host_index]
                handoff = dialogue_generator.generate_handoff(host, next_host, point_content)
                
                dialogue_lines.append({
                    "speaker": next_host["name"],
                    "text": handoff
                })
            else:
                # Even if the same host continues, add a transitional line
                dialogue_lines.append({
                    "speaker": host["name"],
                    "text": f"Building on that point, I'd also like to discuss another important aspect of this topic..."
                })
        
        # Add follow-up questions and responses to create more depth
        # This significantly increases the dialogue content
        if i < len(talking_points) - 1 and len(host_personalities) > 1 and random.random() < 0.7:  # 70% chance for follow-up
            # Determine who asks the follow-up question
            question_host_index = (host_index + 1) % len(host_personalities)
            question_host = host_personalities[question_host_index]
            
            # Generate a follow-up question
            follow_up_question = dialogue_generator.generate_follow_up_question(question_host, point_content)
            
            dialogue_lines.append({
                "speaker": question_host["name"],
                "text": follow_up_question
            })
            
            # Generate a detailed response from the original host
            question_type = random.choice(["championship", "strategy", "technical", "fan", "decision"])
            detailed_response = dialogue_generator.generate_detailed_response(host, question_type)
            
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

def generate_intro_script(title: str, description: str,
                        host_personalities: List[Dict[str, Any]],
                        include_sound_effects: bool) -> Dict[str, Any]:
    """
    Generate script for the episode introduction.
    
    Args:
        title: Episode title
        description: Episode description
        host_personalities: List of host personality definitions
        include_sound_effects: Whether to include sound effects
        
    Returns:
        Script for the intro section
    """
    # Generate dialogue lines
    dialogue_lines = dialogue_generator.generate_intro_dialogue(title, description, host_personalities)
    
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

def generate_outro_script(host_personalities: List[Dict[str, Any]],
                        include_sound_effects: bool) -> Dict[str, Any]:
    """
    Generate script for the episode conclusion.
    
    Args:
        host_personalities: List of host personality definitions
        include_sound_effects: Whether to include sound effects
        
    Returns:
        Script for the outro section
    """
    # Generate dialogue lines
    dialogue_lines = dialogue_generator.generate_outro_dialogue(host_personalities)
    
    # Add sound effects
    sound_effects = []
    if include_sound_effects:
        sound_effects.append({
            "type": "outro",
            "description": sound_effect_manager.get_effect_description("outro"),
            "position": len(dialogue_lines) - 1
        })
    
    # Calculate word count
    word_count = sum(len(line["text"].split()) for line in dialogue_lines)
    
    return {
        "name": "outro",
        "duration": 30,  # Default outro duration
        "dialogue": dialogue_lines,
        "sound_effects": sound_effects,
        "word_count": word_count
    }

# Import random at the module level to ensure it's available
import random
