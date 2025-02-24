def process_feedback_and_regenerate(files, text_model, audio_model, speaker_1_voice, template_dropdown, openai_api_key, api_base, intro_instructions, text_instructions, scratch_pad_instructions, prelude_dialog, podcast_dialog_instructions, edited_transcript, user_feedback):
    return validate_and_generate_audio(files, text_model, audio_model, speaker_1_voice, template_dropdown, openai_api_key, api_base, intro_instructions, text_instructions, scratch_pad_instructions, prelude_dialog, podcast_dialog_instructions, edited_transcript, user_feedback)

def edit_and_regenerate(edited_transcript, user_feedback, *args):
    # Replace the original transcript and feedback in the args with the new ones
    #new_args = list(args)
    #new_args[-2] = edited_transcript  # Update edited transcript
    #new_args[-1] = user_feedback  # Update user feedback
    return validate_and_generate_audio(*new_args)

def validate_and_generate_audio(*args):
    from pathlib import Path
    from pypdf import PdfReader
    from components.dialogue_generation import generate_dialogue
    from components.audio_generation import generate_audio_from_transcript
    from components.data_models import Dialogue
    import os
    import gradio as gr
    from loguru import logger
    import sys

    # ログの設定
    logger.remove()  # 既存のハンドラを削除
    logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.add("processing.log", rotation="500 MB")  # ファイルにもログを出力

    # すべての引数をログに記録
    logger.info("受け取った引数一覧:")
    for i, arg in enumerate(args):
        logger.info(f"引数 {i}: {arg}")

    # 引数の展開とログ
    files, model_name, tts_model, voice_id, instruction_template, openai_api_key, api_base, *other_args = args
    logger.info(f"ファイル: {files}")
    logger.info(f"モデル名: {model_name}")
    logger.info(f"TTSモデル: {tts_model}")
    logger.info(f"音声ID: {voice_id}")
    logger.info(f"指示テンプレート: {instruction_template}")
    logger.info(f"APIキー: {'*' * len(openai_api_key) if openai_api_key else 'なし'}")  # APIキーを隠してログ出力
    logger.info(f"APIベースURL: {api_base}")
    logger.info(f"その他の引数: {[arg[:50] + '...' if isinstance(arg, str) and len(arg) > 50 else arg for arg in other_args]}")
    
    # ファイルチェック
    if not files or not any(files):
        logger.warning("ファイルが提供されていません")
        return None, None, None, "ファイルをアップロードしてください。"

    # ファイルリストの正規化
    if isinstance(files, str):
        files = [files]
    
    logger.info(f"処理するファイル数: {len(files)}")
        
    try:
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

        # Generate dialogue
        intro_instructions = other_args[0]
        text_instructions = other_args[1]
        scratch_pad_instructions = other_args[2]
        prelude_dialog = other_args[3]
        podcast_dialog_instructions = other_args[4]
        api_base = other_args[5]

        edited_transcript = other_args[6] if len(other_args) > 6 else ""
        user_feedback = other_args[7] if len(other_args) > 7 else ""

        instruction_improve='Based on the original text, please generate an improved version of the dialogue by incorporating the edits, comments and feedback.'
        edited_transcript_processed="\nPreviously generated edited transcript, with specific edits and comments that I want you to carefully address:\n"+"<edited_transcript>\n"+edited_transcript+"</edited_transcript>" if edited_transcript !="" else ""
        user_feedback_processed="\nOverall user feedback:\n\n"+user_feedback if user_feedback !="" else ""

        if edited_transcript_processed.strip()!='' or user_feedback_processed.strip()!='':
            user_feedback_processed="<requested_improvements>"+user_feedback_processed+"\n\n"+instruction_improve+"</requested_improvements>" 

        dialogue: Dialogue = generate_dialogue(
            combined_text,
            intro_instructions=intro_instructions,
            text_instructions=text_instructions,
            scratch_pad_instructions=scratch_pad_instructions,
            prelude_dialog=prelude_dialog,
            podcast_dialog_instructions=podcast_dialog_instructions,
            edited_transcript=edited_transcript_processed,
            user_feedback=user_feedback_processed
        )

        # Generate audio from the transcript
        speaker_1_voice = voice_id
        speaker_2_voice = voice_id
        audio_model = tts_model
        audio_file = generate_audio_from_transcript(dialogue.dialogue, speaker_1_voice, speaker_2_voice, audio_model, openai_api_key)

        # Prepare transcript for output
        transcript = ""
        for line in dialogue.dialogue:
            transcript += f"{line.speaker}: {line.text}\n\n"

        return audio_file, transcript, combined_text, None  # Return None as the error when successful
    except Exception as e:
        # If an error occurs during generation, return None for the outputs and the error message
        return None, None, None, str(e)
