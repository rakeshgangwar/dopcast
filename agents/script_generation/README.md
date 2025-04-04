# Enhanced Script Generation Agent

This module provides an enhanced script generation agent implementation using LangGraph for workflow orchestration. The agent is designed to convert content outlines into natural, engaging podcast scripts with dialogue and production notes.

## Features

- **Modular Architecture**: The agent is organized into separate modules for tools, memory, and workflow components.
- **Enhanced Dialogue Generation**: Improved dialogue generation with natural conversation flow and host personalities.
- **Sound Effect Management**: Intelligent placement of sound effects and transitions.
- **Multiple Output Formats**: Scripts are generated in JSON, Markdown, and PDF formats.
- **Memory Components**: Persistent memory for storing and retrieving scripts and host personalities.
- **LangGraph Workflow**: Robust workflow orchestration using LangGraph with error handling.

## Directory Structure

```
agents/script_generation/
├── __init__.py
├── enhanced_script_generation_agent.py
├── tools/
│   ├── __init__.py
│   ├── dialogue_generator.py
│   ├── script_formatter.py
│   └── sound_effect_manager.py
├── memory/
│   ├── __init__.py
│   ├── script_memory.py
│   └── host_memory.py
└── workflow/
    ├── __init__.py
    ├── state.py
    ├── script_graph.py
    └── nodes.py
```

## Usage

```python
from agents.script_generation import EnhancedScriptGenerationAgent

# Create the agent
agent = EnhancedScriptGenerationAgent()

# Process a script generation request
input_data = {
    "content_outline": content_plan,  # Content plan from the content planning agent
    "custom_parameters": {            # Custom parameters for this script
        "script_style": "conversational",
        "humor_level": "moderate",
        "include_sound_effects": True,
        "include_transitions": True
    }
}

# Process the request (async)
script = await agent.process(input_data)
```

## Workflow

The script generation workflow consists of the following steps:

1. **Initialize Script Generation**: Set up tools, memory components, and configuration.
2. **Prepare Content Outline**: Validate and prepare the content outline.
3. **Prepare Host Personalities**: Select appropriate host personalities for the script.
4. **Generate Script Sections**: Create detailed script sections with dialogue and sound effects.
5. **Assemble Script**: Combine sections into a complete script with metadata.
6. **Format Script**: Save the script in multiple formats (JSON, Markdown, PDF).

## Memory Components

### Script Memory

Stores and retrieves generated scripts, providing access to historical scripts.

### Host Memory

Manages host personalities with different styles, roles, and catchphrases.

## Tools

### Dialogue Generator

Creates natural dialogue for hosts based on their personalities and talking points.

### Script Formatter

Formats scripts in multiple output formats (JSON, Markdown, PDF).

### Sound Effect Manager

Manages sound effects and transitions throughout the script.

## Testing

Run the test script to verify the agent's functionality:

```bash
python tests/test_enhanced_script_generation_agent.py
```
