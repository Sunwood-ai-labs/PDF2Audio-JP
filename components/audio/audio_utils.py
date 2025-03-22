import os
from tempfile import NamedTemporaryFile
from loguru import logger

TEMP_DIR = "/app/gradio_cached_examples/tmp/"

def save_audio_file(audio_data: bytes) -> str:
    """音声データを一時ファイルとして保存する

    Args:
        audio_data (bytes): 保存する音声データ

    Returns:
        str: 保存されたファイルのパス
    """
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        temporary_file = NamedTemporaryFile(
            dir=TEMP_DIR,
            delete=False,
            suffix=".mp3",
        )
        temporary_file.write(audio_data)
        temporary_file.close()
        
        logger.info(f"音声ファイルを保存しました: {temporary_file.name}")
        return temporary_file.name

    except Exception as e:
        logger.error(f"音声ファイルの保存中にエラーが発生しました: {str(e)}")
        return None

def normalize_path(path: str) -> str:
    """パスを正規化する

    Args:
        path (str): 正規化するパス

    Returns:
        str: 正規化されたパス
    """
    return os.path.normpath(path).replace('\\', '/')

def ensure_directory(directory: str) -> bool:
    """ディレクトリの存在を確認し、必要に応じて作成する

    Args:
        directory (str): 確認/作成するディレクトリのパス

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"ディレクトリの作成に失敗しました: {directory} - {str(e)}")
        return False
