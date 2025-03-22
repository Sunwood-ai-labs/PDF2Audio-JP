import io
import os
from openai import OpenAI
from loguru import logger
from ..data_models import AudioConfig

def get_mp3(text: str, voice: str, audio_model: str, api_key: str = None) -> bytes:
    """音声を生成する基本関数

    Args:
        text (str): 生成するテキスト
        voice (str): 使用する音声
        audio_model (str): 使用する音声モデル
        api_key (str, optional): APIキー. Defaults to None.

    Returns:
        bytes: 生成された音声データ
    """
    logger.info(f"音声生成開始: 文字数: {len(text)} | 声: {voice} | モデル: {audio_model}")
    logger.info(f"生成するテキスト: {text}")
    client = OpenAI(
        api_key=api_key or os.getenv("TTS_API_KEY"),
        base_url=os.getenv("TTS_API_BASE")
    )

    with client.audio.speech.with_streaming_response.create(
        model=audio_model,
        voice=voice,
        input=text,
    ) as response:
        with io.BytesIO() as file:
            for chunk in response.iter_bytes():
                file.write(chunk)
            logger.info("音声生成完了: 全チャンク受信完了")
            return file.getvalue()

def generate_audio(text: str, model: str, voice: str) -> str:
    """単一のテキストから音声を生成する関数

    Args:
        text (str): 生成するテキスト
        model (str): 使用する音声モデル
        voice (str): 使用する音声

    Returns:
        str: 生成された音声ファイルのパス
    """
    from .audio_utils import save_audio_file

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

        # 音声ファイルの保存
        return save_audio_file(audio)

    except Exception as e:
        logger.error(f"音声生成中にエラーが発生しました: {str(e)}")
        return None
