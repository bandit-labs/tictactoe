"""
Self-Play API Routes
Endpoints for triggering AI vs AI games for dataset generation
"""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uuid

from app.core.db import get_db
from app.core.dependencies import get_ai_service, get_game_state_serializer
from app.domain import IAIService, IGameStateSerializer
from app.application.use_cases import RunSelfPlayGameUseCase, RunBatchSelfPlayUseCase

router = APIRouter(prefix="/self-play", tags=["self-play"])

# In-memory job tracking (for MVP - use Redis in production)
self_play_jobs = {}


class SelfPlayRequest(BaseModel):
    num_games: int = Field(
        default=100, ge=1, le=10000, description="Number of games to play"
    )
    difficulty_x: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    difficulty_o: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    add_noise: bool = Field(default=True, description="Add randomness for move variety")
    alternate_starting_player: bool = Field(
        default=True, description="Alternate X/O each game"
    )


class SelfPlayJobResponse(BaseModel):
    job_id: str
    status: str
    num_games: int
    games_completed: int
    games_requested: int


@router.post("/start", response_model=SelfPlayJobResponse)
def start_self_play(
    request: SelfPlayRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),  # Change to db session
    ai_service: IAIService = Depends(get_ai_service),
    state_serializer: IGameStateSerializer = Depends(get_game_state_serializer),
):
    """Start a batch of self-play games"""
    job_id = str(uuid.uuid4())

    self_play_jobs[job_id] = {
        "status": "running",
        "num_games": request.num_games,
        "games_completed": 0,
        "games_requested": request.num_games,
        "game_ids": [],
    }

    # Create use cases with new signature
    single_game_use_case = RunSelfPlayGameUseCase(
        db=db,  # Pass db session instead of repository
        ai_service=ai_service,
        state_serializer=state_serializer,
    )

    batch_use_case = RunBatchSelfPlayUseCase(single_game_use_case)

    # Progress callback
    def update_progress(current, total):
        self_play_jobs[job_id]["games_completed"] = current

    # Run in background
    def run_batch():
        try:
            game_ids = batch_use_case.execute(
                num_games=request.num_games,
                difficulty_x=request.difficulty_x,
                difficulty_o=request.difficulty_o,
                add_noise=request.add_noise,
                alternate_starting_player=request.alternate_starting_player,
                progress_callback=update_progress,
            )
            self_play_jobs[job_id]["status"] = "completed"
            self_play_jobs[job_id]["game_ids"] = game_ids
        except Exception as e:
            self_play_jobs[job_id]["status"] = "failed"
            self_play_jobs[job_id]["error"] = str(e)

    background_tasks.add_task(run_batch)

    return SelfPlayJobResponse(
        job_id=job_id,
        status="running",
        num_games=request.num_games,
        games_completed=0,
        games_requested=request.num_games,
    )


@router.get("/status/{job_id}", response_model=SelfPlayJobResponse)
def get_self_play_status(job_id: str):
    """Get status of a self-play job"""
    if job_id not in self_play_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = self_play_jobs[job_id]
    return SelfPlayJobResponse(
        job_id=job_id,
        status=job["status"],
        num_games=job["num_games"],
        games_completed=job["games_completed"],
        games_requested=job["games_requested"],
    )


@router.get("/jobs")
def list_self_play_jobs():
    """List all self-play jobs"""
    return [
        {"job_id": job_id, **job_data} for job_id, job_data in self_play_jobs.items()
    ]
