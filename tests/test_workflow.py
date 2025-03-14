import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from pipeline.workflow import PodcastWorkflow

@pytest.fixture
def mock_coordination_agent():
    agent = MagicMock()
    process_result = {"podcast_file": "test_podcast.mp3", "duration": 1500}
    
    future = asyncio.Future()
    future.set_result(process_result)
    agent.process.return_value = future
    
    status_future = asyncio.Future()
    status_future.set_result({"run_id": "test_run", "status": "completed"})
    agent.get_run_status.return_value = status_future
    
    runs_future = asyncio.Future()
    runs_future.set_result([{"run_id": "test_run", "status": "completed"}])
    agent.list_runs.return_value = runs_future
    
    return agent

@patch('pipeline.workflow.CoordinationAgent')
def test_workflow_initialization(mock_agent_class, mock_coordination_agent):
    # Setup
    mock_agent_class.return_value = mock_coordination_agent
    
    # Execute
    workflow = PodcastWorkflow()
    
    # Verify
    assert workflow.coordination_agent is not None
    assert len(workflow.active_runs) == 0
    assert len(workflow.scheduled_runs) == 0
    mock_coordination_agent.initialize_agents.assert_called_once()

@patch('pipeline.workflow.CoordinationAgent')
def test_generate_podcast(mock_agent_class, mock_coordination_agent):
    # Setup
    mock_agent_class.return_value = mock_coordination_agent
    workflow = PodcastWorkflow()
    
    # Execute
    result = asyncio.run(workflow.generate_podcast("f1", "manual", "monaco_2023"))
    
    # Verify
    assert result["podcast_file"] == "test_podcast.mp3"
    mock_coordination_agent.process.assert_called_once()
    assert len(workflow.active_runs) == 1

@patch('pipeline.workflow.CoordinationAgent')
def test_schedule_podcast(mock_agent_class, mock_coordination_agent):
    # Setup
    mock_agent_class.return_value = mock_coordination_agent
    workflow = PodcastWorkflow()
    schedule_time = datetime.now() + timedelta(hours=1)
    
    # Execute
    result = asyncio.run(workflow.schedule_podcast("f1", "race", schedule_time, "monaco_2023"))
    
    # Verify
    assert "schedule_id" in result
    assert result["status"] == "scheduled"
    assert len(workflow.scheduled_runs) == 1
    assert workflow.scheduled_runs[0]["sport"] == "f1"
    assert workflow.scheduled_runs[0]["trigger"] == "race"
    assert workflow.scheduled_runs[0]["event_id"] == "monaco_2023"

@patch('pipeline.workflow.CoordinationAgent')
def test_get_run_status(mock_agent_class, mock_coordination_agent):
    # Setup
    mock_agent_class.return_value = mock_coordination_agent
    workflow = PodcastWorkflow()
    
    # Add an active run
    workflow.active_runs["test_run"] = {
        "task": MagicMock(),
        "started_at": datetime.now().isoformat(),
        "status": "running",
        "input": {"sport": "f1"}
    }
    
    # Execute
    result = asyncio.run(workflow.get_run_status("test_run"))
    
    # Verify
    assert result["run_id"] == "test_run"
    assert result["status"] == "running"
    
    # Test for non-active run
    result = asyncio.run(workflow.get_run_status("other_run"))
    assert result["status"] == "completed"
    mock_coordination_agent.get_run_status.assert_called_once_with("other_run")

@patch('pipeline.workflow.CoordinationAgent')
def test_list_runs(mock_agent_class, mock_coordination_agent):
    # Setup
    mock_agent_class.return_value = mock_coordination_agent
    workflow = PodcastWorkflow()
    
    # Add an active run
    workflow.active_runs["active_run"] = {
        "task": MagicMock(),
        "started_at": datetime.now().isoformat(),
        "status": "running",
        "input": {"sport": "f1", "trigger": "manual"}
    }
    
    # Execute
    result = asyncio.run(workflow.list_runs())
    
    # Verify
    assert len(result) == 2  # 1 active + 1 from coordination agent
    assert any(run["run_id"] == "active_run" for run in result)
    assert any(run["run_id"] == "test_run" for run in result)
    mock_coordination_agent.list_runs.assert_called_once()

@patch('pipeline.workflow.CoordinationAgent')
def test_cancel_scheduled_run(mock_agent_class, mock_coordination_agent):
    # Setup
    mock_agent_class.return_value = mock_coordination_agent
    workflow = PodcastWorkflow()
    
    # Add a scheduled run
    workflow.scheduled_runs.append({
        "id": "schedule_123",
        "sport": "f1",
        "trigger": "race",
        "schedule_time": datetime.now().isoformat(),
        "status": "scheduled"
    })
    
    # Execute
    result = asyncio.run(workflow.cancel_scheduled_run("schedule_123"))
    
    # Verify
    assert result["schedule_id"] == "schedule_123"
    assert result["status"] == "cancelled"
    assert len(workflow.scheduled_runs) == 0
    
    # Test cancelling non-existent run
    result = asyncio.run(workflow.cancel_scheduled_run("nonexistent"))
    assert "error" in result

@patch('pipeline.workflow.CoordinationAgent')
@patch('asyncio.create_task')
def test_check_scheduled_runs(mock_create_task, mock_agent_class, mock_coordination_agent):
    # Setup
    mock_agent_class.return_value = mock_coordination_agent
    workflow = PodcastWorkflow()
    
    # Add a scheduled run that is due
    past_time = datetime.now() - timedelta(minutes=5)
    workflow.scheduled_runs.append({
        "id": "schedule_past",
        "sport": "f1",
        "trigger": "race",
        "event_id": "monaco_2023",
        "schedule_time": past_time.isoformat(),
        "custom_parameters": {},
        "status": "scheduled"
    })
    
    # Add a scheduled run that is not yet due
    future_time = datetime.now() + timedelta(hours=1)
    workflow.scheduled_runs.append({
        "id": "schedule_future",
        "sport": "motogp",
        "trigger": "qualifying",
        "event_id": "mugello_2023",
        "schedule_time": future_time.isoformat(),
        "custom_parameters": {},
        "status": "scheduled"
    })
    
    # Execute
    asyncio.run(workflow.check_scheduled_runs())
    
    # Verify
    mock_create_task.assert_called_once()
    assert len(workflow.scheduled_runs) == 1
    assert workflow.scheduled_runs[0]["id"] == "schedule_future"
