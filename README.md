# DopCast: AI-Powered Motorsport Podcasts

![DopCast Logo](https://via.placeholder.com/800x200?text=DopCast)

DopCast is an innovative platform that uses AI agents to generate engaging podcasts about motorsport events. Each agent has a specific role in the content creation pipeline, working together to deliver timely and insightful audio content for fans.

## Features

- **Multi-agent System**: Specialized AI agents handle different aspects of podcast creation
- **Automated Research**: Gather and analyze information from various sources
- **Natural Dialogue**: Generate engaging, conversational scripts (with PDF and Markdown exports)
- **Voice Synthesis**: Convert scripts to realistic speech
- **Audio Production**: Add music, effects, and professional polish
- **Scheduling System**: Automate podcast creation based on race calendar
- **Web Dashboard**: Monitor and manage podcast generation
- **API Access**: Integrate with other systems and services

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (optional, for containerized deployment)
- OpenAI API key (for AI models)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/dopcast.git
cd dopcast
```

2. Install dependencies:

```bash
uv sync
```

3. Initialize the system:

```bash
uv run initialize.py
```

4. Configure your environment variables by editing the `.env` file:

```
# Add your OpenAI API key
OPENAI_API_KEY=your_api_key_here
```

### Running DopCast

#### Using the CLI

Generate a podcast:

```bash
uv run cli.py generate --sport f1 --event-id monaco_2023 --episode-type race_review
```

Schedule a podcast:

```bash
uv run cli.py schedule --sport motogp --event-id mugello_2023 --time 14:30
```

List recent podcasts:

```bash
uv run cli.py list
```

#### Using the Web Interface

Start the web interface and API:

```bash
uv run main.py full
```

Then open your browser and navigate to:
- Web UI: http://localhost:8501
- API Docs: http://localhost:8000/docs

#### Using Docker

Build and run with Docker Compose:

```bash
docker-compose up -d
```

## System Architecture

DopCast uses a modular architecture with the following components:

### Agents

- **BaseAgent**: Abstract base class for all agents
- **ResearchAgent**: Gathers and analyzes information
- **ContentPlanningAgent**: Structures podcast episodes
- **ScriptGenerationAgent**: Creates natural, engaging scripts
- **VoiceSynthesisAgent**: Converts scripts to audio
- **AudioProductionAgent**: Enhances audio with production elements
- **CoordinationAgent**: Orchestrates the entire workflow

### Pipeline

The podcast generation pipeline follows this sequence:

```
Research → Content Planning → Script Generation → Voice Synthesis → Audio Production
```

The Coordination Agent manages this pipeline, handling retries, error recovery, and ensuring data consistency between stages.

### API

The REST API provides endpoints for:
- Generating podcasts
- Scheduling future podcast generation
- Retrieving podcast status and results
- Managing the system

### Web Interface

The Streamlit-based web interface allows for:
- Easy podcast generation with custom parameters
- Scheduling and managing podcast creation
- Viewing and downloading generated podcasts
- Downloading scripts in Markdown and PDF formats
- System monitoring and configuration

## Extending DopCast

### Adding New Sports

To add support for a new sport:

1. Create a configuration file in `config/sports/[sport_name].json`
2. Implement any sport-specific research methods in the ResearchAgent
3. Add the sport to the CLI and API options

### Customizing Voice Profiles

Edit the voice profiles in `config/voice_profiles.json` to create custom voices for your podcast hosts.

### Adding Sound Effects

Place audio files in `content/audio/assets/` to make them available for the AudioProductionAgent.

### Script Formats

The system supports exporting podcast scripts in multiple formats:
- **JSON**: Default format containing all script data
- **Markdown**: Clean, readable format for easy sharing and editing
- **PDF**: Professional format for printing or distribution

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the AI models
- The open-source community for the various libraries used
- Formula 1 and MotoGP for the exciting sports that inspired this project
