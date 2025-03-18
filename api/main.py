import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pipeline.workflow import PodcastWorkflow
from utils.supabase_client import SupabaseClient
from config import Config

# Configure logging
logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=logging_format)

# Create logger for this module
logger = logging.getLogger("dopcast.api")

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
supabase = SupabaseClient()

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
    podcast_id: Optional[str] = None
    status: str
    started_at: str
    completed_at: Optional[str] = None

class PodcastModel(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    sport: str
    event_id: Optional[str] = None
    episode_type: Optional[str] = None
    duration: Optional[int] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None
    audio_url: Optional[str] = None
    script_url: Optional[str] = None

# API endpoints
@app.post("/podcasts/generate", response_model=Dict[str, Any])
async def generate_podcast(request: PodcastRequest, background_tasks: BackgroundTasks):
    """Generate a podcast for a specific sport and event."""
    logger.info(f"Received podcast generation request: sport={request.sport}, trigger={request.trigger}")
    
    try:
        # Check Supabase connection first
        if not supabase.is_connected():
            logger.error("Supabase connection not available")
            raise HTTPException(status_code=503, detail="Database service unavailable")
        
        # Check if required tables exist
        if not supabase.check_tables_exist():
            logger.error("Required Supabase tables don't exist")
            raise HTTPException(status_code=503, detail="Database tables not properly configured")
        
        # Start podcast generation
        result = await workflow.generate_podcast(
            sport=request.sport,
            trigger=request.trigger,
            event_id=request.event_id,
            custom_parameters=request.custom_parameters
        )
        
        if "error" in result:
            logger.error(f"Error in podcast generation: {result['error']}")
            return {
                "podcast_id": result.get("podcast_id"),
                "status": "error",
                "message": result["error"]
            }
        
        logger.info(f"Podcast generation started: {result.get('podcast_id')}")
        return {
            "podcast_id": result.get("podcast_id"),
            "run_id": result.get("run_id"),
            "status": "processing",
            "message": "Podcast generation started"
        }
    except Exception as e:
        logger.exception(f"Unexpected error in podcast generation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/podcasts/schedule", response_model=Dict[str, Any])
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

@app.get("/podcasts", response_model=List[Dict[str, Any]])
async def list_podcasts(limit: int = 10, sport: Optional[str] = None):
    """
    List podcasts from Supabase database, optionally filtered by sport.
    """
    return await workflow.list_podcasts(limit, sport)

@app.get("/podcasts/{podcast_id}", response_model=Dict[str, Any])
async def get_podcast(podcast_id: str):
    """
    Get a specific podcast by ID from Supabase database.
    """
    podcast = await workflow.get_podcast(podcast_id)
    if not podcast:
        raise HTTPException(status_code=404, detail=f"Podcast {podcast_id} not found")
    return podcast

@app.get("/podcasts/{podcast_id}/logs", response_model=List[Dict[str, Any]])
async def get_podcast_logs(podcast_id: str):
    """
    Get generation logs for a specific podcast.
    """
    try:
        # Query logs from Supabase directly
        logs = supabase.client.table('generation_logs').select('*').eq('podcast_id', podcast_id).execute()
        
        if logs.data:
            return logs.data
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check Supabase connection
    supabase_connected = supabase.is_connected()
    
    # Check if required tables exist
    tables_exist = False
    if supabase_connected:
        tables_exist = supabase.check_tables_exist()
    
    # Determine overall health status
    status = "healthy" if supabase_connected and tables_exist else "unhealthy"
    
    response = {
        "status": status, 
        "version": "0.1.0",
        "supabase": {
            "connected": supabase_connected,
            "url": Config.SUPABASE_URL,
            "tables_exist": tables_exist
        }
    }
    
    if not supabase_connected:
        response["supabase"]["error"] = "Failed to connect to Supabase"
    
    return response

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
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
