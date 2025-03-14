import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pipeline.workflow import PodcastWorkflow

app = FastAPI(
    title="DopCast API",
    description="API for generating AI-powered motorsport podcasts",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize workflow manager
workflow = PodcastWorkflow()

# Define request/response models
class PodcastRequest(BaseModel):
    sport: str = Field(..., description="Sport type (f1 or motogp)")
    trigger: str = Field("manual", description="Trigger event type")
    event_id: Optional[str] = Field(None, description="Specific event identifier")
    custom_parameters: Optional[Dict[str, Any]] = Field(None, description="Custom parameters for the pipeline")

class ScheduleRequest(BaseModel):
    sport: str = Field(..., description="Sport type (f1 or motogp)")
    trigger: str = Field(..., description="Trigger event type")
    schedule_time: datetime = Field(..., description="When to generate the podcast")
    event_id: Optional[str] = Field(None, description="Specific event identifier")
    custom_parameters: Optional[Dict[str, Any]] = Field(None, description="Custom parameters for the pipeline")

class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None

# API endpoints
@app.post("/podcasts/generate", response_model=Dict[str, Any])
async def generate_podcast(request: PodcastRequest, background_tasks: BackgroundTasks):
    """Generate a podcast for a specific sport and event."""
    # Start podcast generation in the background
    task = asyncio.create_task(workflow.generate_podcast(
        sport=request.sport,
        trigger=request.trigger,
        event_id=request.event_id,
        custom_parameters=request.custom_parameters
    ))
    
    # Return initial response
    run_id = f"{request.sport}_{request.trigger}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return {
        "run_id": run_id,
        "status": "started",
        "message": "Podcast generation started"
    }

@app.post("/podcasts/schedule", response_model=Dict[str, str])
async def schedule_podcast(request: ScheduleRequest):
    """Schedule a podcast for future generation."""
    return await workflow.schedule_podcast(
        sport=request.sport,
        trigger=request.trigger,
        schedule_time=request.schedule_time,
        event_id=request.event_id,
        custom_parameters=request.custom_parameters
    )

@app.get("/podcasts/runs/{run_id}", response_model=Dict[str, Any])
async def get_run_status(run_id: str):
    """Get the status of a specific podcast generation run."""
    status = await workflow.get_run_status(run_id)
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    return status

@app.get("/podcasts/runs", response_model=List[Dict[str, Any]])
async def list_runs(limit: int = 10, sport: Optional[str] = None):
    """List recent podcast generation runs."""
    return await workflow.list_runs(limit, sport)

@app.get("/podcasts/scheduled", response_model=List[Dict[str, Any]])
async def list_scheduled_runs(sport: Optional[str] = None):
    """List scheduled podcast generation runs."""
    return await workflow.list_scheduled_runs(sport)

@app.delete("/podcasts/scheduled/{schedule_id}", response_model=Dict[str, Any])
async def cancel_scheduled_run(schedule_id: str):
    """Cancel a scheduled podcast generation run."""
    result = await workflow.cancel_scheduled_run(schedule_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}

# Scheduler task to check for due scheduled runs
async def scheduler_task():
    while True:
        try:
            await workflow.check_scheduled_runs()
        except Exception as e:
            print(f"Error in scheduler task: {str(e)}")
        await asyncio.sleep(60)  # Check every minute

@app.on_event("startup")
async def startup_event():
    # Start the scheduler task
    asyncio.create_task(scheduler_task())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
