from typing import Optional, List, Dict, Any
import json
from pathlib import Path
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from loguru import logger
import sys
from openai import OpenAI
import os
import io
import os
from pathlib import Path
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from loguru import logger
import sys
import json
from datetime import datetime

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

def save_debug_info(data: dict, prefix: str = "debug"):
    """デバッグ情報をJSONファイルに保存する関数

    Args:
        data (dict): 保存するデータ
        prefix (str, optional): ファイル名のプレフィックス. Defaults to "debug".
    """
    try:
        # デバッグ用ディレクトリの作成
        debug_dir = Path("debug_logs")
        debug_dir.mkdir(exist_ok=True)

        # タイムスタンプを含むファイル名の生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = debug_dir / f"{prefix}_{timestamp}.json"

        # JSONファイルとして保存
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"デバッグ情報を保存しました: {filename}")

    except Exception as e:
        logger.error(f"デバッグ情報の保存に失敗しました: {str(e)}")

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

        # OpenAIのAPIを使用して対話を生成
        client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=config.api_base if config.api_base else os.getenv("LLM_API_BASE")
        )

        # システムプロンプトの構築
        system_prompt = f"""
        あなたは与えられたテキストを対話形式に変換するアシスタントです。
        以下の指示に従って対話を生成してください：

        【出力形式】
        必ず以下の形式で出力してください：
        ホスト: （テキスト）
        ゲスト: （テキスト）
        ホスト: （テキスト）
        ...

        各行は必ず「ホスト:」または「ゲスト:」で始まり、その後にコロンとスペース、そして発話内容が続きます。
        この形式以外の出力は許可されません。

        【指示内容】
        {config.intro_instructions}

        テキスト分析指示：
        {config.text_instructions}

        メモ帳指示：
        {config.scratch_pad_instructions}

        前置き対話：
        {config.prelude_dialog}

        対話指示：
        ブレインストーミングセッションで考えた重要なポイントと創造的なアイデアに基づいて、とても長く、魅力的で有益なポッドキャスト対話をここに書いてください。会話的なトーンを使用し、一般的な聴衆にコンテンツを理解しやすくするために必要な文脈や説明を含めてください。

        対話の参加者に作り物の名前を使用せず、リスナーにとって魅力的で没入感のある体験を作り出してください。括弧付きのプレースホルダーを含めないでください。出力は音声に直接変換されることを想定して設計してください。

        対話をできるだけ長く詳細にしながら、トピックに焦点を当て、魅力的な流れを維持してください。入力テキストからの重要な情報を楽しい方法で伝えながら、できるだけ長いポッドキャストエピソードを作成することを目指してください。

        対話の最後に、参加者に、彼らの議論から得られた主要な洞察とポイントを自然にまとめてもらってください。これは会話から自然に流れ出るべきで、重要なポイントをカジュアルな会話的な方法で繰り返すものです。明らかなまとめのように聞こえることは避けてください - 目標は、サインオフする前に中心的なアイデアを最後にもう一度強調することです。

        ポッドキャストは約20,000語程度にしてください。
        """

        # ユーザープロンプトの構築
        user_prompt = f"""
        以下のテキストを対話形式に変換してください：

        {text}

        {edited_transcript_processed if edited_transcript else ""}
        {user_feedback_processed if user_feedback else ""}
        """

        try:
            # OpenAI APIを呼び出して対話を生成
            response = client.chat.completions.create(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            # 応答から対話を抽出
            dialogue_text = response.choices[0].message.content
            
            # デバッグ情報をファイルに保存
            debug_data = {
                "timestamp": datetime.now().isoformat(),
                "model": config.model_name,
                "template_type": config.template_type,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": dialogue_text,
                "edited_transcript": edited_transcript,
                "user_feedback": user_feedback
            }
            save_debug_info(debug_data, "dialogue_generation")
            
            # デバッグ用にレスポンスを保存
            logger.info("OpenAI APIからのレスポンス:")
            logger.info(dialogue_text)
            
            dialogue_lines = []

            # 対話テキストを解析して話者と内容を分離
            for line in dialogue_text.strip().split('\n'):
                if not line.strip():
                    continue
                
                # デバッグ用に各行の内容を出力
                logger.debug(f"処理中の行: {line}")
                
                # 「ホスト:」または「ゲスト:」で始まる行を処理
                if 'ホスト:' in line or 'ゲスト:' in line:
                    try:
                        speaker, text = [part.strip() for part in line.split(':', 1)]
                        logger.debug(f"分割結果 - 話者: {speaker}, テキスト: {text}")
                        dialogue_lines.append(
                            DialogueLine(
                                speaker=speaker,
                                text=text
                            )
                        )
                    except Exception as e:
                        logger.warning(f"行の解析に失敗: {line} - エラー: {str(e)}")
                        continue

            if not dialogue_lines:
                # デバッグ情報を記録
                logger.error("対話生成に失敗しました：有効な対話行が見つかりません")
                logger.error("システムプロンプト:")
                logger.error(system_prompt)
                logger.error("ユーザープロンプト:")
                logger.error(user_prompt)
                logger.error("生成された対話テキスト:")
                logger.error(dialogue_text)
                raise ValueError("対話生成に失敗しました")

            # 生成された対話行の数を記録
            logger.info(f"生成された対話行数: {len(dialogue_lines)}")
            return dialogue_lines

        except Exception as e:
            logger.error(f"OpenAI APIの呼び出し中にエラーが発生しました: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"対話生成中にエラーが発生しました: {str(e)}")
        raise
