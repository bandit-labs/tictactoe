from typing import Optional
from pydantic import BaseModel

class MoveCreate(BaseModel):
    row: Optional[int] = None
    col: Optional[int] = None
    use_ai: bool = False          # False = PvP | True = PvAI
    ai_difficulty: Optional[str] = None  # "easy" | "medium" | "hard"
