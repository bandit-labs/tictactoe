from typing import Optional
from pydantic import BaseModel

class MoveCreate(BaseModel):
    row: Optional[int] = None
    col: Optional[int] = None
    ai_difficulty: Optional[str] = None  # "easy" | "medium" | "hard"
