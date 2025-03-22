import concurrent.futures as cf
from loguru import logger
from tempfile import NamedTemporaryFile
from typing import List
from ..data_models import DialogueItem
from .audio_core import get_mp3
from .audio_utils import TEMP_DIR, ensure_directory
from .audio_ffmpeg import create_ffmpeg_input_file, concat_audio_files
from .audio_cleanup import cleanup_temp_files, cleanup_old_files

def generate_audio_from_transcript(
    transcript: List[DialogueItem],
    speaker_1_voice: str,
    speaker_2_voice: str,
    audio_model: str,
    openai_api_key: str = None
) -> str:
    """トランスクリプトから音声を生成する

    Args:
        transcript (List[DialogueItem]): 生成するトランスクリプト
        speaker_1_voice (str): ホストの声
        speaker_2_voice (str): ゲストの声
        audio_model (str): 使用する音声モデル
        openai_api_key (str, optional): OpenAI APIキー. Defaults to None.

    Returns:
        str: 生成された音声ファイルのパス
    """
    temp_files = []
    final_audio_file = None
    characters = 0

    # 一時ディレクトリの作成
    ensure_directory(TEMP_DIR)

    try:
        # 並列で音声を生成
        logger.info("音声生成を開始します")
        with cf.ThreadPoolExecutor() as executor:
            logger.info("ThreadPoolExecutorを初期化しました")
            futures = []
            
            # 音声生成タスクの設定
            for line in transcript:
                text = line.text.split(":", 1)[1].strip() if ":" in line.text else line.text.strip()
                voice = speaker_1_voice if line.speaker == "ホスト" else speaker_2_voice
                logger.info(f"話者: {line.speaker}, 声: {voice}, テキスト: {text}")
                
                future = executor.submit(get_mp3, text, voice, audio_model, openai_api_key)
                futures.append((future, text))
                characters += len(text)

            logger.info(f"音声生成タスクの設定完了: 合計{len(futures)}個のタスク")

            # 音声ファイルの保存
            completed_tasks = 0
            for future, text in futures:
                try:
                    audio_chunk = future.result()
                    temp_file = NamedTemporaryFile(
                        dir=TEMP_DIR,
                        delete=False,
                        suffix=".mp3"
                    )
                    temp_file.write(audio_chunk)
                    temp_file.close()
                    temp_files.append(temp_file.name)
                    completed_tasks += 1
                    logger.info(f"進捗: {completed_tasks}/{len(futures)} - 一時ファイルを保存: {temp_file.name}")
                except Exception as e:
                    logger.error(f"音声生成エラー: {str(e)}, テキスト: {text}")
                    raise

        logger.info(f"音声生成完了: 合計{characters}文字を処理")
        logger.info(f"一時ファイル数: {len(temp_files)}")

        # 最終的な結合ファイルの準備
        final_audio_file = NamedTemporaryFile(
            dir=TEMP_DIR,
            delete=False,
            suffix=".mp3"
        ).name

        # 音声ファイルの結合
        file_list = create_ffmpeg_input_file(temp_files)
        concat_audio_files(file_list, final_audio_file)

    except Exception as e:
        logger.error(f"音声生成処理中にエラーが発生しました: {str(e)}")
        raise
    finally:
        # 一時ファイルのクリーンアップ
        cleanup_temp_files(temp_files)
        cleanup_old_files()

    return final_audio_file
