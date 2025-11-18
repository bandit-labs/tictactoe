from pydantic import BaseModel

class MoveCreate(BaseModel):
    row: int
    col: int
    use_ai: bool = False
