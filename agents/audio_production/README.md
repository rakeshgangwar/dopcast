# Enhanced Audio Production Agent

This module provides an enhanced audio production agent implementation using LangGraph for workflow orchestration. The agent is designed to process audio segments into a professional-quality podcast episode with proper mixing, mastering, and metadata.

## Features

- **Modular Architecture**: The agent is organized into separate modules for tools, memory, and workflow components.
- **Enhanced Audio Mixing**: Improved audio mixing with proper transitions and balancing.
- **Audio Mastering**: Professional-quality mastering with EQ, compression, and limiting.
- **Metadata Generation**: Automatic generation of ID3 tags and podcast RSS entries.
- **Memory Components**: Persistent memory for storing and retrieving production metadata.
- **LangGraph Workflow**: Robust workflow orchestration using LangGraph with error handling.

## Directory Structure

```
agents/audio_production/
├── __init__.py
├── enhanced_audio_production_agent.py
├── tools/
│   ├── __init__.py
│   ├── audio_mixer.py
│   ├── audio_enhancer.py
│   └── metadata_generator.py
├── memory/
│   ├── __init__.py
│   └── production_memory.py
└── workflow/
    ├── __init__.py
    ├── state.py
    ├── production_graph.py
    └── nodes.py
```

## Usage

```python
from agents.audio_production import EnhancedAudioProductionAgent

# Create the agent
agent = EnhancedAudioProductionAgent()

# Process an audio production request
input_data = {
    "audio_metadata": audio_metadata,  # Audio metadata from voice synthesis
    "custom_parameters": {  # Custom parameters for this production
        "output_format": "mp3",
        "target_loudness": -16.0,
        "episode_number": 42
    }
}

# Process the request (async)
production_metadata = await agent.process(input_data)
```

## Workflow

The audio production workflow consists of the following steps:

1. **Initialize Production**: Set up tools, memory components, and configuration.
2. **Prepare Audio Metadata**: Validate and prepare the audio metadata.
3. **Enhance Audio**: Apply noise reduction and other enhancements to audio segments.
4. **Mix Audio**: Mix audio segments with proper transitions and balancing.
5. **Master Audio**: Apply EQ, compression, and limiting for professional sound.
6. **Generate Metadata**: Create ID3 tags and podcast RSS entries.

## Memory Components

### Production Memory

Stores and retrieves production metadata for published episodes.

## Tools

### Audio Mixer

Mixes audio segments with proper transitions and balancing.

### Audio Enhancer

Enhances audio quality with noise reduction, EQ, compression, and limiting.

### Metadata Generator

Generates ID3 tags and podcast RSS entries for publishing.

## Testing

Run the test script to verify the agent's functionality:

```bash
python tests/test_enhanced_audio_production_agent.py
```
