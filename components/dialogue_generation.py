from typing import Optional, List, Dict, Any
import json
from pathlib import Path
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from loguru import logger
import sys

# ログの設定
logger.remove()  # 既存のハンドラを削除
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("dialogue_generation.log", rotation="500 MB")  # ファイルにもログを出力

class DialogueConfig(BaseModel):
    """対話生成の設定を定義するモデル"""
    model_name: str
    template_type: str
    intro_instructions: str
    text_instructions: str
    scratch_pad_instructions: str
    prelude_dialog: str
    podcast_dialog_instructions: str
    api_base: Optional[str] = None

class DialogueLine(BaseModel):
    """対話の1行を定義するモデル"""
    speaker: str
    text: str

@retry(
    retry=retry_if_exception_type((ValidationError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def generate_dialogue(
    text: str,
    config: DialogueConfig,
    edited_transcript: Optional[str] = None,
    user_feedback: Optional[str] = None
) -> List[DialogueLine]:
    """対話を生成する関数

    Args:
        text (str): 入力テキスト
        config (DialogueConfig): 対話生成の設定
        edited_transcript (Optional[str], optional): 編集済みトランスクリプト. Defaults to None.
        user_feedback (Optional[str], optional): ユーザーフィードバック. Defaults to None.

    Returns:
        List[DialogueLine]: 生成された対話テキスト
    """
    try:
        logger.info("対話生成を開始します")
        logger.info(f"モデル名: {config.model_name}")
        logger.info(f"テンプレートタイプ: {config.template_type}")
        
        # 入力テキストの処理
        instruction_improve = 'Based on the original text, please generate an improved version of the dialogue by incorporating the edits, comments and feedback.'
        edited_transcript_processed = (
            "\nPreviously generated edited transcript, with specific edits and comments that I want you to carefully address:\n"
            + "<edited_transcript>\n"
            + (edited_transcript if edited_transcript else "")
            + "</edited_transcript>"
        ) if edited_transcript else ""
        
        user_feedback_processed = (
            "\nOverall user feedback:\n\n"
            + (user_feedback if user_feedback else "")
        ) if user_feedback else ""

        if edited_transcript_processed.strip() or user_feedback_processed.strip():
            user_feedback_processed = (
                "<requested_improvements>"
                + user_feedback_processed
                + "\n\n"
                + instruction_improve
                + "</requested_improvements>"
            )

        # TODO: 実際のLLMを使用した対話生成ロジックを実装
        # 現在はダミーの応答を返す
        return [
            DialogueLine(speaker="話者1", text="こんにちは、これはテストの対話です。"),
            DialogueLine(speaker="話者2", text="はい、これはダミーの応答です。")
        ]

    except Exception as e:
        logger.error(f"対話生成中にエラーが発生しました: {str(e)}")
        raise
