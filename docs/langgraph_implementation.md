# DopCast LangGraph Implementation

This document explains how the LangGraph-based workflow orchestration is implemented in DopCast.

## Overview

DopCast has been refactored to use LangGraph for agent orchestration. LangGraph provides:

- A robust graph-based workflow execution system
- Clear state management between agents
- Potential for visualization and debugging of agent interactions
- Support for persistence and tracing

## Architecture

The implementation follows these key components:

1. **State Definition (`DopCastState`)**: A TypedDict class defining the data structure that flows through the graph.
2. **Agent Nodes**: Functions wrapping the existing agents (`ResearchAgent`, `ContentPlanningAgent`, etc.).
3. **Graph Structure**: A linear flow from research to audio production.
4. **Workflow Manager**: The existing `PodcastWorkflow` class, updated to use the LangGraph.

## Running the Workflow

### Command Line

You can use the provided `run_workflow.py` script:

```bash
python run_workflow.py --sport f1 --event-id monaco_2023 --episode-type race_review
```

Or use the existing CLI:

```bash
python cli.py generate --sport f1 --event-id monaco_2023 --episode-type race_review
```

### API/Web Interface

The existing API and Web interface will work the same as before:

```bash
# Start the full server (API + Web UI)
python main.py full
```

Then navigate to:
- Web UI: http://localhost:8501
- API Docs: http://localhost:8000/docs

## Code Structure

- `pipeline/graph.py`: Defines the LangGraph state, nodes, and flow.
- `pipeline/workflow.py`: Updated to use the LangGraph for orchestration.

## Advanced Configuration

### Persistence

For production, consider updating the graph compilation to use persistence:

```python
# In pipeline/graph.py
from langgraph.checkpoint.redis import RedisSaver
import os

# Configure Redis connection (adjust based on your Redis setup)
redis_config = {
    "url": os.environ.get("REDIS_URL", "redis://localhost:6379"),
    "ttl": 3600 * 24 * 7,  # 1 week TTL
}

redis_saver = RedisSaver(redis_config=redis_config)
graph = graph_builder.compile(checkpointer=redis_saver)
```

### Run Status and History

The current implementation relies on in-memory tracking for run status. For a more robust solution, implement `get_run_status` and `list_runs` methods to query the checkpointer:

```python
# Example for retrieving state from checkpointer
async def get_run_status(self, run_id: str):
    config = {"configurable": {"thread_id": run_id}}
    try:
        state = await self.graph.aget_state(config=config)
        # Extract status from state
        return {
            "run_id": run_id,
            "status": "completed" if not state.get("error_info") else "failed",
            # Additional state details as needed
        }
    except Exception as e:
        return {"error": f"Failed to retrieve status: {str(e)}"}
```

### Graph Visualization

LangGraph supports visualization of the workflow graph. To generate a visual representation:

```python
# Visualize the graph (requires graphviz)
from IPython.display import display
from langgraph.graph.visualize import visualize

# Generate a PNG
visualize(graph).save("dopcast_workflow.png")