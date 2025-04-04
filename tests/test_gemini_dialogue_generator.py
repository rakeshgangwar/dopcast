"""
Test script for Gemini-powered dialogue generation.
This tests the DialogueGeneratorTool with Google Gemini LLM integration.
"""

import os
import sys
import json
import logging
from datetime import datetime
import asyncio

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our components
from agents.script_generation.tools.dialogue_generator import DialogueGeneratorTool
from agents.common.llm_client import GeminiLLMClient

async def test_gemini_dialogue_generator():
    """Test the Gemini-powered dialogue generator."""
    logger.info("Testing Gemini-powered dialogue generator")
    
    # Check if Google API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY environment variable not set")
        logger.info("Please set your Google API key with: export GOOGLE_API_KEY='your-api-key'")
        return
    
    # Initialize the dialogue generator with Gemini LLM
    llm_config = {
        "model_name": "gemini-2.0-flash",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    dialogue_generator = DialogueGeneratorTool({
        "llm_config": llm_config,
        "use_cache": True
    })
    
    # Create a talking point
    talking_point = "The controversial penalty given to Max Verstappen in the final laps of the Monaco Grand Prix"
    
    # Create host personalities
    host_personalities = [
        {
            "name": "Mukesh",
            "role": "lead_host",
            "style": "enthusiastic",
            "expertise": "general",
            "catchphrases": ["Absolutely incredible!", "Let's dive into this.", "What a moment that was!"]
        },
        {
            "name": "Rakesh",
            "role": "technical_expert",
            "style": "analytical",
            "expertise": "technical",
            "catchphrases": ["If we look at the data...", "Technically speaking...", "The numbers tell us..."]
        }
    ]
    
    # Test talking_point_to_dialogue
    logger.info("Testing talking_point_to_dialogue")
    host1 = host_personalities[0]
    host1_dialogue = await dialogue_generator.talking_point_to_dialogue(
        talking_point, host1, "conversational", "moderate"
    )
    logger.info(f"{host1['name']}'s dialogue: {host1_dialogue}")
    
    # Test generate_handoff
    logger.info("Testing generate_handoff")
    host2 = host_personalities[1]
    handoff = await dialogue_generator.generate_handoff(
        host1, host2, talking_point
    )
    logger.info(f"Handoff from {host1['name']} to {host2['name']}: {handoff}")
    
    # Test generate_follow_up_question
    logger.info("Testing generate_follow_up_question")
    follow_up_question = await dialogue_generator.generate_follow_up_question(
        host2, talking_point
    )
    logger.info(f"Follow-up question from {host2['name']}: {follow_up_question}")
    
    # Test generate_detailed_response
    logger.info("Testing generate_detailed_response")
    detailed_response = await dialogue_generator.generate_detailed_response(
        host1, follow_up_question, talking_point
    )
    logger.info(f"Detailed response from {host1['name']}: {detailed_response}")
    
    # Test generate_intro_dialogue
    logger.info("Testing generate_intro_dialogue")
    title = "Monaco Grand Prix Controversy"
    description = "Discussing the controversial penalty given to Max Verstappen and its implications for the championship."
    intro_dialogue = await dialogue_generator.generate_intro_dialogue(
        title, description, host_personalities
    )
    logger.info(f"Intro dialogue: {json.dumps(intro_dialogue, indent=2)}")
    
    # Test generate_outro_dialogue
    logger.info("Testing generate_outro_dialogue")
    outro_dialogue = await dialogue_generator.generate_outro_dialogue(
        host_personalities, title
    )
    logger.info(f"Outro dialogue: {json.dumps(outro_dialogue, indent=2)}")
    
    # Create a complete dialogue exchange
    dialogue_exchange = [
        {
            "speaker": host1["name"],
            "text": host1_dialogue.strip()
        },
        {
            "speaker": host2["name"],
            "text": handoff.strip()
        },
        {
            "speaker": host2["name"],
            "text": follow_up_question.strip()
        },
        {
            "speaker": host1["name"],
            "text": detailed_response.strip()
        }
    ]
    
    # Save the result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "tests")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"gemini_dialogue_test_{timestamp}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "dialogue_exchange": dialogue_exchange,
            "intro_dialogue": intro_dialogue,
            "outro_dialogue": outro_dialogue
        }, f, indent=2)
    
    logger.info(f"Test result saved to {output_file}")
    
    return {
        "dialogue_exchange": dialogue_exchange,
        "intro_dialogue": intro_dialogue,
        "outro_dialogue": outro_dialogue
    }

async def test_full_script_generation():
    """Test generating a complete script with multiple sections."""
    logger.info("Testing full script generation with Gemini")
    
    # Check if Google API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY environment variable not set")
        logger.info("Please set your Google API key with: export GOOGLE_API_KEY='your-api-key'")
        return
    
    # Initialize the dialogue generator with Gemini LLM
    llm_config = {
        "model_name": "gemini-2.0-flash",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    dialogue_generator = DialogueGeneratorTool({
        "llm_config": llm_config,
        "use_cache": True
    })
    
    # Create host personalities
    host_personalities = [
        {
            "name": "Mukesh",
            "role": "lead_host",
            "style": "enthusiastic",
            "expertise": "general",
            "catchphrases": ["Absolutely incredible!", "Let's dive into this.", "What a moment that was!"]
        },
        {
            "name": "Rakesh",
            "role": "technical_expert",
            "style": "analytical",
            "expertise": "technical",
            "catchphrases": ["If we look at the data...", "Technically speaking...", "The numbers tell us..."]
        }
    ]
    
    # Create a simple content outline
    content_outline = {
        "title": "Monaco Grand Prix Analysis",
        "description": "A deep dive into the controversial Monaco Grand Prix and its implications for the championship.",
        "sections": [
            {
                "name": "headlines",
                "duration": 120,
                "talking_points": [
                    {
                        "content": "Max Verstappen received a controversial penalty in the final laps",
                        "host": 0
                    },
                    {
                        "content": "Lewis Hamilton secured an unexpected podium finish",
                        "host": 1
                    }
                ]
            },
            {
                "name": "analysis",
                "duration": 180,
                "talking_points": [
                    {
                        "content": "The impact of the penalty on the championship standings",
                        "host": 1
                    },
                    {
                        "content": "Ferrari's strategy decisions during the race",
                        "host": 0
                    }
                ]
            }
        ]
    }
    
    # Generate script sections
    script_sections = []
    
    # Generate intro
    logger.info("Generating intro section")
    intro = await generate_test_section(
        "intro", content_outline["title"], content_outline["description"], 
        host_personalities, dialogue_generator
    )
    script_sections.append(intro)
    
    # Generate content sections
    for section in content_outline["sections"]:
        logger.info(f"Generating section: {section['name']}")
        section_script = await generate_test_section(
            section["name"], section["talking_points"], None,
            host_personalities, dialogue_generator
        )
        script_sections.append(section_script)
    
    # Generate outro
    logger.info("Generating outro section")
    outro = await generate_test_section(
        "outro", content_outline["title"], None,
        host_personalities, dialogue_generator
    )
    script_sections.append(outro)
    
    # Assemble the complete script
    script = {
        "title": content_outline["title"],
        "description": content_outline["description"],
        "hosts": [host["name"] for host in host_personalities],
        "created_at": datetime.now().isoformat(),
        "script_style": "conversational",
        "humor_level": "moderate",
        "sections": script_sections
    }
    
    # Save the result to a file for inspection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "tests")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"gemini_full_script_{timestamp}.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2)
    
    logger.info(f"Full script saved to {output_file}")
    
    return script

async def generate_test_section(section_name, content, description, host_personalities, dialogue_generator):
    """Generate a test script section."""
    if section_name == "intro":
        # Generate intro dialogue
        dialogue_lines = await dialogue_generator.generate_intro_dialogue(
            content, description, host_personalities
        )
        
        return {
            "name": "intro",
            "duration": 60,
            "dialogue": dialogue_lines,
            "sound_effects": [],
            "word_count": sum(len(line["text"].split()) for line in dialogue_lines)
        }
    
    elif section_name == "outro":
        # Generate outro dialogue
        dialogue_lines = await dialogue_generator.generate_outro_dialogue(
            host_personalities, content
        )
        
        return {
            "name": "outro",
            "duration": 30,
            "dialogue": dialogue_lines,
            "sound_effects": [],
            "word_count": sum(len(line["text"].split()) for line in dialogue_lines)
        }
    
    else:
        # Generate dialogue for content section
        dialogue_lines = []
        
        # Add section introduction
        primary_host = host_personalities[0]
        section_intro = f"Let's move on to {section_name.replace('_', ' ').title()}. "
        
        dialogue_lines.append({
            "speaker": primary_host["name"],
            "text": section_intro
        })
        
        # Generate dialogue for each talking point
        for i, point in enumerate(content):
            point_content = point["content"]
            host_index = point.get("host", i % len(host_personalities))
            host = host_personalities[host_index]
            
            # Generate dialogue for this talking point
            dialogue = await dialogue_generator.talking_point_to_dialogue(
                point_content, host, "conversational", "moderate"
            )
            
            dialogue_lines.append({
                "speaker": host["name"],
                "text": dialogue
            })
            
            # Add interaction between hosts if not the last point
            if i < len(content) - 1:
                next_host_index = content[i+1].get("host", (i+1) % len(host_personalities))
                if next_host_index != host_index:
                    next_host = host_personalities[next_host_index]
                    handoff = await dialogue_generator.generate_handoff(
                        host, next_host, point_content
                    )
                    
                    dialogue_lines.append({
                        "speaker": next_host["name"],
                        "text": handoff
                    })
        
        return {
            "name": section_name,
            "duration": 120,
            "dialogue": dialogue_lines,
            "sound_effects": [],
            "word_count": sum(len(line["text"].split()) for line in dialogue_lines)
        }

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_gemini_dialogue_generator())
    asyncio.run(test_full_script_generation())
