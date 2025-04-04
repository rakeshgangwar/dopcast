# Enhanced Voice Synthesis Agent

This module provides an enhanced voice synthesis agent implementation using LangGraph for workflow orchestration. The agent is designed to convert podcast scripts into natural-sounding audio with appropriate emotions and sound effects.

## Features

- **Modular Architecture**: The agent is organized into separate modules for tools, memory, and workflow components.
- **Enhanced Voice Generation**: Improved voice generation with emotion detection and parameter adjustment.
- **Sound Effect Integration**: Proper integration of sound effects into the audio stream.
- **Voice Profile Management**: Support for different voice profiles with customizable parameters.
- **Memory Components**: Persistent memory for storing and retrieving voice profiles and audio metadata.
- **LangGraph Workflow**: Robust workflow orchestration using LangGraph with error handling.

## Directory Structure

```
agents/voice_synthesis/
├── __init__.py
├── enhanced_voice_synthesis_agent.py
├── tools/
│   ├── __init__.py
│   ├── voice_generator.py
│   ├── audio_processor.py
│   └── emotion_detector.py
├── memory/
│   ├── __init__.py
│   ├── voice_memory.py
│   └── audio_memory.py
└── workflow/
    ├── __init__.py
    ├── state.py
    ├── synthesis_graph.py
    └── nodes.py
```

## Usage

```python
from agents.voice_synthesis import EnhancedVoiceSynthesisAgent

# Create the agent
agent = EnhancedVoiceSynthesisAgent()

# Process a voice synthesis request
input_data = {
    "script": script,  # Script from the script generation agent
    "custom_parameters": {  # Custom parameters for this synthesis
        "audio_format": "mp3",
        "use_ssml": False
    }
}

# Process the request (async)
audio_metadata = await agent.process(input_data)
```

## Workflow

The voice synthesis workflow consists of the following steps:

1. **Initialize Synthesis**: Set up tools, memory components, and configuration.
2. **Prepare Script**: Validate and prepare the script.
3. **Map Voices**: Map script speakers to voice profiles.
4. **Generate Section Audio**: Create audio for each section with appropriate emotions.
5. **Combine Audio**: Combine section audio into a complete episode.
6. **Finalize Audio**: Save audio metadata and finalize the process.

## Memory Components

### Voice Memory

Stores and retrieves voice profiles with different characteristics.

### Audio Memory

Manages audio metadata for generated episodes.

## Tools

### Voice Generator

Creates audio for dialogue lines with appropriate voice profiles.

### Audio Processor

Processes and combines audio segments with proper transitions.

### Emotion Detector

Detects emotions in text to adjust voice parameters accordingly.

## Testing

Run the test script to verify the agent's functionality:

```bash
python tests/test_enhanced_voice_synthesis_agent.py
```
