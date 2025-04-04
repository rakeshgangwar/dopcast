# Enhanced Research Agent

This module provides an enhanced research agent implementation using LangGraph for workflow orchestration. The agent is designed to gather, process, and analyze motorsport information from various sources.

## Features

- **Modular Architecture**: The agent is organized into separate modules for tools, memory, and workflow components.
- **Enhanced Web Scraping**: Improved web scraping capabilities with async support and better error handling.
- **Structured Data Processing**: Better data processing with deduplication and structured output.
- **Entity Extraction**: Advanced entity extraction using NLP techniques.
- **Memory Components**: Persistent memory for caching, entity tracking, and research history.
- **LangGraph Workflow**: Robust workflow orchestration using LangGraph with error handling and conditional routing.

## Directory Structure

```
agents/research/
├── __init__.py
├── enhanced_research_agent.py
├── tools/
│   ├── __init__.py
│   ├── web_scraper.py
│   ├── data_processor.py
│   └── entity_extractor.py
├── memory/
│   ├── __init__.py
│   ├── cache_memory.py
│   ├── entity_memory.py
│   └── research_memory.py
└── workflow/
    ├── __init__.py
    ├── research_graph.py
    └── nodes.py
```

## Usage

```python
from agents.research import EnhancedResearchAgent

# Create the agent
agent = EnhancedResearchAgent()

# Process a research request
input_data = {
    "sport": "f1",
    "event_type": "race",
    "event_id": "monaco_2023",
    "force_refresh": True
}

# Process the request (async)
result = await agent.process(input_data)
```

## Workflow

The research workflow consists of the following steps:

1. **Initialize Research**: Set up tools, memory components, and configuration.
2. **Collect Data**: Gather data from configured sources.
3. **Process Data**: Process and structure the collected data.
4. **Extract Entities**: Extract entities (people, teams, tracks, events) from the data.
5. **Analyze Trends**: Identify trends and key stories.
6. **Generate Report**: Create the final research report.

## Memory Components

### Cache Memory

Provides caching capabilities with TTL and persistence to avoid redundant data collection.

### Entity Memory

Tracks information about entities (people, teams, tracks, events) across multiple research runs.

### Research Memory

Stores historical research information, including events, trends, and key stories.

## Tools

### Web Scraper

Enhanced web scraping with async support, error handling, and source-specific extraction logic.

### Data Processor

Processes collected data with deduplication, date range extraction, and structured output.

### Entity Extractor

Extracts entities using NLP techniques and categorizes articles by topic.

## Testing

Run the test script to verify the agent's functionality:

```bash
python tests/test_enhanced_research_agent.py
```
