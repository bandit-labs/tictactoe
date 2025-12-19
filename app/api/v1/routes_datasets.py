"""
Dataset Export API Routes
Endpoints for exporting ML-ready datasets
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import os
import tempfile

from sqlalchemy import func

from app.core.db import get_db
from app.application.ml_dataset_service import MLDatasetExportService
from app.application.analytics_models import GameAnalytics

router = APIRouter(prefix="/datasets", tags=["datasets"])

class DatasetExportRequest(BaseModel):
    format: str = Field(default="parquet", pattern="^(parquet|csv)$")
    max_games: Optional[int] = Field(default=None, description="Limit number of games")
    mode_filter: Optional[str] = Field(default=None, pattern="^(pvp|pvai)$")

@router.post("/export")
def export_dataset(
    request: DatasetExportRequest,
    db = Depends(get_db)
):
    """
    Export analytics data as ML-ready dataset

    Returns downloadable file (Parquet or CSV)
    """
    export_service = MLDatasetExportService(db)

    # Create temp file
    suffix = '.parquet' if request.format == 'parquet' else '.csv'
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)

    try:
        if request.format == 'parquet':
            stats = export_service.export_to_parquet(
                output_path=temp_path,
                max_games=request.max_games,
                mode_filter=request.mode_filter
            )
        else:
            df = export_service.export_to_dataframe(
                max_games=request.max_games,
                mode_filter=request.mode_filter
            )
            df.to_csv(temp_path, index=False)
            stats = {
                'total_moves': len(df),
                'total_games': df['game_id'].nunique()
            }

            # Return file with stats in headers
        return FileResponse(
            temp_path,
            media_type='application/octet-stream',
            filename=f'ml_dataset_{datetime.now().strftime("%Y%m%d_%H%M%S")}{suffix}',
            headers={
                'X-Dataset-Stats': str(stats)
            }
        )
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
def get_dataset_stats(db = Depends(get_db)):
    """Get statistics about available data for ML training"""

    total_games = db.query(GameAnalytics).filter(
        GameAnalytics.status.in_(['X_win', 'O_win', 'draw'])
    ).count()

    outcomes = db.query(
        GameAnalytics.status,
        func.count(GameAnalytics.game_id)
    ).filter(
        GameAnalytics.status.in_(['X_win', 'O_win', 'draw'])
    ).group_by(GameAnalytics.status).all()

    return {
        'total_completed_games': total_games,
        'outcomes': {status: count for status, count in outcomes},
        'ready_for_ml': total_games >= 200
    }
