import os
import glob
import time
from loguru import logger
from typing import List
from .audio_utils import TEMP_DIR

def cleanup_temp_files(temp_files: List[str]) -> None:
    """一時ファイルを削除する

    Args:
        temp_files (List[str]): 削除する一時ファイルのリスト
    """
    for temp_file in temp_files:
        logger.debug(f"一時ファイルの削除を試行: {temp_file}")
        try:
            os.remove(temp_file)
            logger.debug(f"一時ファイルを削除しました: {temp_file}")
        except Exception as e:
            logger.warning(f"一時ファイルの削除に失敗: {temp_file} - {str(e)}")
    logger.info("一時ファイルのクリーンアップ完了")

def cleanup_old_files(max_age_days: int = 1) -> int:
    """古い一時ファイルを削除する

    Args:
        max_age_days (int, optional): 保持する最大日数. Defaults to 1.

    Returns:
        int: 削除されたファイルの数
    """
    removed_count = 0
    old_files = glob.glob(f"{TEMP_DIR}*.mp3")
    logger.info(f"古い一時ファイルのクリーンアップを開始: {len(old_files)}個のファイルをチェック")

    for file in old_files:
        try:
            if os.path.isfile(file) and time.time() - os.path.getmtime(file) > max_age_days * 24 * 60 * 60:
                logger.debug(f"古い一時ファイルを削除: {file}")
                os.remove(file)
                removed_count += 1
        except Exception as e:
            logger.warning(f"ファイルの削除に失敗: {file} - {str(e)}")

    logger.info(f"古い一時ファイルのクリーンアップ完了: {removed_count}個のファイルを削除")
    return removed_count
