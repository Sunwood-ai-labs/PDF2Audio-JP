"""
Audio Generation Package
-----------------------

音声生成に関する機能を提供するパッケージ。

主な機能:
- 音声の生成と保存
- 複数の音声ファイルの結合
- 一時ファイルの管理
"""

from .audio_generation import generate_audio_from_transcript
from .audio_core import generate_audio
from .audio_utils import TEMP_DIR

__all__ = [
    'generate_audio_from_transcript',
    'generate_audio',
    'TEMP_DIR'
]
