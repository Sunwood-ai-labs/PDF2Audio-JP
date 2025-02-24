from typing import List, Literal
from pydantic import BaseModel

class DialogueItem(BaseModel):
    text: str
    speaker: Literal["ホスト", "ゲスト"]

class Dialogue(BaseModel):
    scratchpad: str
    dialogue: List[DialogueItem]
