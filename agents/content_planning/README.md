# Enhanced Content Planning Agent

This module provides an enhanced content planning agent implementation using LangGraph for workflow orchestration. The agent is designed to create structured podcast episode outlines based on research data.

## Features

- **Modular Architecture**: The agent is organized into separate modules for tools, memory, and workflow components.
- **Enhanced Outline Generation**: Improved outline generation with better section planning and talking point generation.
- **Template Management**: Support for episode templates with different formats and durations.
- **Memory Components**: Persistent memory for storing and retrieving outlines and templates.
- **LangGraph Workflow**: Robust workflow orchestration using LangGraph with error handling.

## Directory Structure

```
agents/content_planning/
├── __init__.py
├── enhanced_content_planning_agent.py
├── tools/
│   ├── __init__.py
│   ├── outline_generator.py
│   ├── section_planner.py
│   └── talking_point_generator.py
├── memory/
│   ├── __init__.py
│   ├── outline_memory.py
│   └── template_memory.py
└── workflow/
    ├── __init__.py
    ├── state.py
    ├── planning_graph.py
    └── nodes.py
```

## Usage

```python
from agents.content_planning import EnhancedContentPlanningAgent

# Create the agent
agent = EnhancedContentPlanningAgent()

# Process a content planning request
input_data = {
    "research_data": research_results,  # Data from the research agent
    "episode_type": "race_review",      # Type of episode to create
    "custom_parameters": {              # Custom parameters for this episode
        "duration": 1800,               # Target duration in seconds (30 minutes)
        "technical_level": "mixed",     # Level of technical detail
        "host_count": 2                 # Number of hosts
    }
}

# Process the request (async)
content_plan = await agent.process(input_data)
```

## Workflow

The content planning workflow consists of the following steps:

1. **Initialize Planning**: Set up tools, memory components, and configuration.
2. **Prepare Research Data**: Validate and prepare the research data.
3. **Select Episode Format**: Select the appropriate episode format template.
4. **Adjust Sections**: Filter and adjust section durations to match the target episode length.
5. **Create Detailed Sections**: Generate talking points for each section.
6. **Generate Content Plan**: Create the final content plan with all details.

## Memory Components

### Outline Memory

Stores and retrieves episode outlines, providing access to historical content plans.

### Template Memory

Manages episode templates with different formats and section structures.

## Tools

### Outline Generator

Creates complete episode outlines with titles, descriptions, and references.

### Section Planner

Plans episode sections, adjusting durations and filtering based on research data.

### Talking Point Generator

Generates talking points for each section based on research data and technical level.

## Testing

Run the test script to verify the agent's functionality:

```bash
python tests/test_enhanced_content_planning_agent.py
```
