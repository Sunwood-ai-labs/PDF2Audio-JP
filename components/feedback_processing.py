from typing import Optional, Tuple, Any
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from loguru import logger
from .dialogue_generation import DialogueConfig, DialogueLine, generate_dialogue
from .audio_generation import generate_audio_from_transcript
from pathlib import Path
from pypdf import PdfReader
import os
import gradio as gr
import sys

class FeedbackConfig(BaseModel):
    """フィードバック処理の設定を定義するモデル"""
    files: Any
    text_model: str
    audio_model: str
    speaker_1_voice: str
    speaker_2_voice: str
    template_dropdown: str
    llm_api_key: Optional[str] = os.getenv("LLM_API_KEY")
    api_base: Optional[str] = os.getenv("LLM_API_BASE")
    llm_api_base: Optional[str] = os.getenv("LLM_API_BASE")
    tts_api_key: Optional[str] = os.getenv("TTS_API_KEY")
    tts_api_base: Optional[str] = os.getenv("TTS_API_BASE")
    intro_instructions: str
    text_instructions: str
    scratch_pad_instructions: str
    prelude_dialog: str
    podcast_dialog_instructions: str

@retry(
    retry=retry_if_exception_type((ValidationError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def process_feedback_and_regenerate(
    files, text_model, audio_model, speaker_1_voice, speaker_2_voice,
    template_dropdown, llm_api_key, api_base, llm_api_base, tts_api_key, tts_api_base,
    intro_instructions, text_instructions, scratch_pad_instructions, prelude_dialog,
    podcast_dialog_instructions, edited_transcript, user_feedback
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """フィードバックを処理し、オーディオを再生成する関数

    Args:
        files: アップロードされたファイル
        text_model: テキスト生成モデル
        audio_model: 音声生成モデル
        speaker_1_voice: ホストの声
        speaker_2_voice: ゲストの声
        template_dropdown: 指示テンプレート
        llm_api_key: LLM APIキー
        api_base: APIベースURL
        llm_api_base: LLM APIベースURL
        tts_api_key: TTS APIキー
        tts_api_base: TTS APIベースURL
        intro_instructions: 導入指示
        text_instructions: テキスト分析指示
        scratch_pad_instructions: メモ帳指示
        prelude_dialog: 前置き対話
        podcast_dialog_instructions: ポッドキャスト対話指示
        edited_transcript: 編集済みトランスクリプト
        user_feedback: ユーザーフィードバック

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]: 
            (audio_output, transcript_output, original_text_output, error_output)
    """
    try:
        # 設定のバリデーション
        config = FeedbackConfig(
            files=files,
            text_model=text_model,
            audio_model=audio_model,
            speaker_1_voice=speaker_1_voice,
            speaker_2_voice=speaker_2_voice,
            template_dropdown=template_dropdown,
            llm_api_key=llm_api_key,
            api_base=api_base,
            llm_api_base=llm_api_base,
            tts_api_key=tts_api_key,
            tts_api_base=tts_api_base,
            intro_instructions=intro_instructions,
            text_instructions=text_instructions,
            scratch_pad_instructions=scratch_pad_instructions,
            prelude_dialog=prelude_dialog,
            podcast_dialog_instructions=podcast_dialog_instructions
        )

        # ログの設定
        logger.remove()  # 既存のハンドラを削除
        logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
        logger.add("processing.log", rotation="500 MB")  # ファイルにもログを出力

        # すべての引数をログに記録
        logger.info("受け取った引数一覧:")
        for i, arg in enumerate([files, text_model, audio_model, speaker_1_voice, speaker_2_voice, template_dropdown, llm_api_key, api_base, llm_api_base, tts_api_key, tts_api_base, intro_instructions, text_instructions, scratch_pad_instructions, prelude_dialog, podcast_dialog_instructions, edited_transcript, user_feedback]):
            logger.info(f"引数 {i}: {arg}")

        # 対話生成の設定
        dialogue_config = DialogueConfig(
            model_name=config.text_model,
            template_type=config.template_dropdown,
            intro_instructions=config.intro_instructions,
            text_instructions=config.text_instructions,
            scratch_pad_instructions=config.scratch_pad_instructions,
            prelude_dialog=config.prelude_dialog,
            podcast_dialog_instructions=config.podcast_dialog_instructions,
            api_base=config.llm_api_base
        )

        # ファイルチェック
        if not files or not any(files):
            logger.warning("ファイルが提供されていません")
            return None, None, None, "ファイルをアップロードしてください。"

        # ファイルリストの正規化
        if isinstance(files, str):
            files = [files]
        
        logger.info(f"処理するファイル数: {len(files)}")
        
        # Combine text from uploaded files
        combined_text = ""
        processed_files = 0
        
        for file_path in files:
            try:
                if not file_path or not file_path.strip():
                    continue
                
                logger.info(f"処理するファイルパス: {file_path}")
                
                try:
                    file_path = Path(file_path)
                except Exception as e:
                    logger.error(f"ファイルパスの変換に失敗: {e}")
                    continue
                
                file_path = Path(file_path).resolve()

                if not file_path.exists():
                    logger.error(f"ファイルが存在しません: {file_path}")
                    continue

                if not file_path.is_file():
                    logger.error(f"通常のファイルではありません: {file_path}")
                    continue
                
                file_extension = file_path.suffix.lower()
                logger.info(f"ファイル拡張子: {file_extension}")
                
                if file_extension == '.pdf':
                    logger.info(f"PDFファイルを処理中: {file_path}")
                    try:
                        with open(file_path, "rb") as f:
                            reader = PdfReader(f)
                            logger.info(f"PDFページ数: {len(reader.pages)}")
                            text = ""
                            for i, page in enumerate(reader.pages):
                                page_text = page.extract_text()
                                if page_text:
                                    text += page_text + "\n\n"
                                    logger.info(f"ページ {i+1} からテキストを抽出: {len(page_text)} 文字")
                                else:
                                    logger.warning(f"ページ {i+1} からテキストを抽出できませんでした")
                            
                            if text.strip():
                                combined_text += text
                                logger.info(f"PDFから抽出された合計テキスト: {len(text)} 文字")
                            else:
                                logger.warning("PDFからテキストを抽出できませんでした")
                    except Exception as e:
                        logger.error(f"PDFファイルの処理中にエラー: {e}")
                        continue
                
                elif file_extension in ['.md', '.txt']:
                    logger.info(f"{file_extension}ファイルを処理中: {file_path}")
                    success = False
                    encodings = ['utf-8', 'shift-jis', 'euc-jp', 'iso-2022-jp']
                    
                    for encoding in encodings:
                        try:
                            with open(file_path, "r", encoding=encoding) as f:
                                text = f.read()
                                if text.strip():
                                    combined_text += text + "\n\n"
                                    logger.info(f"ファイルから読み込まれたテキスト ({encoding}): {len(text)} 文字")
                                    success = True
                                    break
                                else:
                                    logger.warning(f"{encoding}でファイルを読み込みましたが、内容が空です")
                        except UnicodeDecodeError:
                            logger.warning(f"{encoding}でのデコードに失敗しました")
                            continue
                        except Exception as e:
                            logger.error(f"ファイル読み込み中にエラー ({encoding}): {e}")
                            break
                    
                    if not success:
                        logger.error(f"ファイルの読み込みに失敗: {file_path}")
                        continue
                
                else:
                    logger.warning(f"未対応のファイル形式です: {file_extension}")
                    continue
                
                processed_files += 1
                logger.info(f"ファイル処理完了: {processed_files}/{len(files)}")
                
            except Exception as e:
                logger.error(f"ファイル処理中のエラー: {str(e)}", exc_info=True)
                continue

        if processed_files == 0:
            logger.error("処理に成功したファイルがありません")
            return None, None, None, "ファイルの処理に失敗しました。ファイル形式とエンコーディングを確認してください。"

        if not combined_text.strip():
            logger.error("テキストが抽出できませんでした")
            return None, None, None, "アップロードされたファイルからテキストを抽出できませんでした。ファイルが空でないか、正しい形式であることを確認してください。"

        logger.info(f"処理完了: 合計 {processed_files} ファイル")
        logger.info(f"合計テキスト長: {len(combined_text)} 文字")

        # 対話を生成
        logger.info("LLM生成開始: generate_dialogue関数を呼び出します")
        dialogue_lines = generate_dialogue(
            text=combined_text,
            config=dialogue_config,
            edited_transcript=edited_transcript,
            user_feedback=user_feedback
        )
        if not dialogue_lines:
            return None, None, None, "対話生成に失敗しました"
        logger.info("LLM生成完了: generate_dialogueが正常に返りました")

        # 音声を生成
        logger.info("音声生成を開始します")
        audio = generate_audio_from_transcript(
            transcript=dialogue_lines,
            speaker_1_voice=config.speaker_1_voice,
            speaker_2_voice=config.speaker_2_voice,
            audio_model=config.audio_model,
            openai_api_key=config.llm_api_key
        )
        if not audio:
            return None, None, None, "音声生成に失敗しました"
        logger.info("音声生成が完了しました")

        # トランスクリプトの準備
        transcript_output = "\n\n".join([f"{line.speaker}: {line.text}" for line in dialogue_lines])

        return audio, transcript_output, combined_text, None  # エラーがない場合はNoneを返す

    except Exception as e:
        # If an error occurs during generation, return None for the outputs and the error message
        import traceback
        error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return None, None, None, error_msg

def edit_and_regenerate(edited_transcript, user_feedback, *args):
    """編集されたトランスクリプトとフィードバックを使用して再生成を行う関数"""
    return process_feedback_and_regenerate(*args[:-2], edited_transcript, user_feedback)
