from typing import List, Literal
from pydantic import BaseModel, Field

class DialogueItem(BaseModel):
    text: str
    speaker: Literal["ホスト", "ゲスト"]

class Dialogue(BaseModel):
    scratchpad: str
    dialogue: List[DialogueItem]

class AudioConfig(BaseModel):
    model: str = Field(..., description="使用する音声モデル")
    voice: str = Field(..., description="使用する音声")
    text: str = Field(..., description="生成するテキスト")
