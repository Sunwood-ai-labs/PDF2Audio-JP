import subprocess
from typing import List
from loguru import logger
from tempfile import NamedTemporaryFile
from .audio_utils import TEMP_DIR, normalize_path

def create_ffmpeg_input_file(temp_files: List[str]) -> str:
    """FFmpeg用の入力ファイルリストを作成する

    Args:
        temp_files (List[str]): 結合する音声ファイルのリスト

    Returns:
        str: 作成された入力ファイルのパス
    """
    try:
        with NamedTemporaryFile(mode='w', delete=False, suffix='.txt', dir=TEMP_DIR) as f:
            for temp_file in temp_files:
                normalized_path = normalize_path(temp_file)
                logger.debug(f"一時ファイルリストに追加: {normalized_path}")
                f.write(f"file '{normalized_path}'\n")
            f.flush()
            file_list = f.name
            
        # 一時ファイルリストの内容を確認
        logger.debug(f"一時ファイルリストの内容を確認: {file_list}")
        with open(file_list, 'r') as f:
            file_content = f.read()
            logger.debug(f"ファイルリストの内容:\n{file_content}")
            
        return file_list
    except Exception as e:
        logger.error(f"FFmpeg入力ファイルの作成に失敗しました: {str(e)}")
        raise

def concat_audio_files(input_list: str, output_file: str) -> bool:
    """FFmpegを使用して音声ファイルを結合する

    Args:
        input_list (str): 入力ファイルリストのパス
        output_file (str): 出力ファイルのパス

    Returns:
        bool: 成功した場合はTrue
    """
    try:
        # FFmpegコマンドの構築
        # -y: 既存ファイルを上書き
        # -f concat: 結合モード
        # -safe 0: 安全でないファイル名を許可
        # -acodec libmp3lame: MP3エンコーダーを使用
        # -q:a 2: VBRエンコード品質（0=最高品質、9=最低品質）
        ffmpeg_command = [
            'ffmpeg',
            '-y', '-f', 'concat', '-safe', '0',
            '-i', normalize_path(input_list),
 
            '-acodec', 'libmp3lame', '-q:a', '2',
            output_file
        ]
        logger.info(f"FFmpegコマンド: {' '.join(ffmpeg_command)}")

        # FFmpegの実行
        result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpegコマンドが失敗: {result.stderr}")
            return False
            
        if result.stderr:
            logger.debug(f"FFmpeg出力: {result.stderr}")
            
        logger.info(f"FFmpegによる音声ファイルの結合が完了: {output_file}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg実行エラー: {str(e)}")
        logger.error(f"FFmpeg出力: {e.stdout if e.stdout else ''}\n{e.stderr if e.stderr else ''}")
        logger.error(f"FFmpegコマンド: {' '.join(ffmpeg_command)}")
        raise
    except Exception as e:
        logger.error(f"音声ファイルの結合中にエラーが発生しました: {str(e)}")
        raise
