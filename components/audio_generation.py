import io
import os
from tempfile import NamedTemporaryFile
import glob
import time
from openai import OpenAI
from loguru import logger
from typing import Optional, List
from pydantic import BaseModel
import sys

# ログの設定
logger.remove()  # 既存のハンドラを削除
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("audio_generation.log", rotation="500 MB")  # ファイルにもログを出力

class AudioConfig(BaseModel):
    """音声生成の設定を定義するモデル"""
    model: str
    voice: str
    text: str

def get_mp3(text: str, voice: str, audio_model: str, api_key: str = None) -> bytes:
    
    logger.info(f"音声生成開始: 文字数: {len(text)} | 声: {voice} | モデル: {audio_model}")
    client = OpenAI(
        api_key=api_key or os.getenv("OPENAI_API_KEY"),
    )

    with client.audio.speech.with_streaming_response.create(
        model=audio_model,
        voice=voice,
        input=text,
    ) as response:
        with io.BytesIO() as file:
            for chunk in response.iter_bytes():
                logger.debug(f"受信したチャンクサイズ: {len(chunk)} バイト")
                file.write(chunk)
            logger.info("音声生成完了: 全チャンク受信完了")
            return file.getvalue()

def generate_audio_from_transcript(transcript, speaker_1_voice, speaker_2_voice, audio_model, openai_api_key):
    import concurrent.futures as cf
    from loguru import logger

    audio = b""
    characters = 0

    with cf.ThreadPoolExecutor() as executor:
        futures = []
        for line in transcript:
            transcript_line = f"{line.speaker}: {line.text}"
            voice = speaker_1_voice if line.speaker == "speaker-1" else speaker_2_voice
            future = executor.submit(get_mp3, line.text, voice, audio_model, openai_api_key)
            futures.append((future, transcript_line))
            characters += len(line.text)

        for future, transcript_line in futures:
            audio_chunk = future.result()
            audio += audio_chunk
            #transcript += transcript_line + "\n\n" # Not needed here

    logger.info(f"Generated {characters} characters of audio")

    temporary_directory = "./gradio_cached_examples/tmp/"
    os.makedirs(temporary_directory, exist_ok=True)

    # Use a temporary file -- Gradio's audio component doesn't work with raw bytes in Safari
    temporary_file = NamedTemporaryFile(
        dir=temporary_directory,
        delete=False,
        suffix=".mp3",
    )
    temporary_file.write(audio)
    temporary_file.close()

    # Delete any files in the temp directory that end with .mp3 and are over a day old
    for file in glob.glob(f"{temporary_directory}*.mp3"):
        if os.path.isfile(file) and time.time() - os.path.getmtime(file) > 24 * 60 * 60:
            os.remove(file)

    return temporary_file.name

def generate_audio(text: str, model: str, voice: str) -> Optional[str]:
    """音声を生成する関数

    Args:
        text (str): 生成するテキスト
        model (str): 使用する音声モデル
        voice (str): 使用する音声

    Returns:
        Optional[str]: 生成された音声ファイルのパス。エラー時はNone
    """
    try:
        logger.info("音声生成を開始します")
        logger.info(f"モデル: {model}")
        logger.info(f"音声: {voice}")
        logger.info(f"テキスト長: {len(text)}")

        # 設定のバリデーション
        config = AudioConfig(
            model=model,
            voice=voice,
            text=text
        )

        # 音声生成の実行
        audio = get_mp3(text=text, voice=voice, audio_model=model)
        if not audio:
            logger.error("音声生成に失敗しました: get_mp3がNoneを返しました")
            return None

        # 一時ファイルの作成
        temporary_directory = "./gradio_cached_examples/tmp/"
        os.makedirs(temporary_directory, exist_ok=True)
        temporary_file = NamedTemporaryFile(
            dir=temporary_directory,
            delete=False,
            suffix=".mp3",
        )
        temporary_file.write(audio)
        temporary_file.close()
        
        logger.info(f"音声ファイルを保存しました: {temporary_file.name}")
        return temporary_file.name

    except Exception as e:
        logger.error(f"音声生成中にエラーが発生しました: {str(e)}")
        return None
