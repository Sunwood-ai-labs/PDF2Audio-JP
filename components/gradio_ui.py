import gradio as gr
from components.instruction_templates import INSTRUCTION_TEMPLATES
from components.utility_functions import read_readme, update_instructions
from components.standard_values import STANDARD_TEXT_MODELS, STANDARD_AUDIO_MODELS, STANDARD_VOICES
from components.feedback_processing import process_feedback_and_regenerate
import os
from dotenv import load_dotenv

def load_css(file_path: str) -> str:
    """CSSファイルを読み込む関数

    Args:
        file_path (str): CSSファイルのパス

    Returns:
        str: CSSファイルの内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"CSSファイルの読み込みに失敗しました: {e}")
        return ""

def gradio_ui():
    # 環境変数の読み込み
    load_dotenv()
    openai_api_key_default = os.getenv("OPENAI_API_KEY", "")

    css_content = load_css("static/styles.css")
    
    with gr.Blocks(
        title="PDFをオーディオポッドキャスト、講義、要約などに変換", 
        theme=gr.themes.Ocean(),
        css=css_content
    ) as demo:
        
        with gr.Row(elem_id="header"):
            with gr.Column(scale=4):
                gr.Markdown("""
                # PDFをオーディオポッドキャスト、講義、要約などに変換

                まず、1つ以上のPDFをアップロードし、オプションを選択してから、オーディオ生成をクリックしてください。
                また、さまざまなカスタムオプションを選択して、結果の生成方法を指定することもできます。
                """, elem_id="title")
            with gr.Column(scale=1, elem_classes="animate-fade-in"):
                gr.HTML('''
                    <div id="logo_container">
                        <img src="https://github.com/user-attachments/assets/4aad8436-6d5b-4b5b-9e1a-dc006abfdd18" id="logo_image" alt="Logo">
                    </div>
                ''')
        #gr.Markdown("")    
        submit_btn = gr.Button("オーディオを生成", elem_id="submit_btn")

        with gr.Row(elem_id="main_container"):
            with gr.Column(scale=2, elem_classes="input-container"):
                files = gr.Files(  # gr.File から gr.Files に変更
                    label="ファイルをアップロード (対応形式: PDF, Markdown, テキスト)", 
                    file_types=[".pdf", ".md", ".txt"],
                    type="filepath",  
                    interactive=True,
                    file_count="multiple"
                )
                
                openai_api_key = gr.Textbox(
                    label="OpenAI APIキー",
                    value=openai_api_key_default,  # デフォルト値を環境変数から設定
                    visible=True,  # Always show the API key field
                    placeholder="OpenAI APIキーを入力してください...",
                    type="password"  # Hide the API key input
                )
                text_model = gr.Dropdown(
                    label="テキスト生成モデル",
                    choices=STANDARD_TEXT_MODELS,
                    value="gpt-4o-mini", #"gpt-4o-mini",
                    info="対話テキストを生成するモデルを選択してください。",
                )
                audio_model = gr.Dropdown(
                    label="音声生成モデル",
                    choices=STANDARD_AUDIO_MODELS,
                    value="tts-1",
                    info="音声を生成するモデルを選択してください。",
                )
                speaker_1_voice = gr.Dropdown(
                    label="ホストの声",
                    choices=STANDARD_VOICES,
                    value="alloy",
                    info="ホストの声を選択してください。",
                )
                speaker_2_voice = gr.Dropdown(
                    label="ゲストの声",
                    choices=STANDARD_VOICES,
                    value="echo",
                    info="ゲストの声を選択してください。",
                )
                api_base = gr.Textbox(
                    label="カスタムAPIベースURL",
                    placeholder="カスタム/ローカルモデルを使用する場合はAPIベースURLを入力してください...",
                    info="カスタムまたはローカルモデルを使用する場合は、APIベースURLを入力してください。例: llama.cpp RESTサーバーの場合は http://localhost:8080/v1",
                )

            with gr.Column(scale=3):
                template_dropdown = gr.Dropdown(
                    label="指示テンプレート",
                    choices=list(INSTRUCTION_TEMPLATES.keys()),
                    value="podcast",
                    info="使用する指示テンプレートを選択してください。より細かい結果を得るために、任意のフィールドを編集することもできます。",
                )
                intro_instructions = gr.Textbox(
                    label="導入指示",
                    lines=10,
                    value=INSTRUCTION_TEMPLATES["podcast"]["intro"],
                    info="対話を生成するための導入指示を入力してください。",
                )
                text_instructions = gr.Textbox(
                    label="標準テキスト分析指示",
                    lines=10,
                    placeholder="テキスト分析指示を入力...",
                    value=INSTRUCTION_TEMPLATES["podcast"]["text_instructions"],
                    info="生データとテキストを分析するための指示を入力してください。",
                )
                scratch_pad_instructions = gr.Textbox(
                    label="メモ帳指示",
                    lines=15,
                    value=INSTRUCTION_TEMPLATES["podcast"]["scratch_pad"],
                    info="プレゼンテーション/対話のコンテンツをブレインストーミングするためのメモ帳指示を入力してください。",
                )
                prelude_dialog = gr.Textbox(
                    label="前置き対話",
                    lines=5,
                    value=INSTRUCTION_TEMPLATES["podcast"]["prelude"],
                    info="プレゼンテーション/対話が開発される前の前置き指示を入力してください。",
                )
                podcast_dialog_instructions = gr.Textbox(
                    label="ポッドキャスト対話指示",
                    lines=20,
                    value=INSTRUCTION_TEMPLATES["podcast"]["dialog"],
                    info="プレゼンテーションまたはポッドキャストの対話を生成するための指示を入力してください。",
                )

        audio_output = gr.Audio(label="オーディオ", format="mp3", interactive=False, autoplay=False)
        transcript_output = gr.Textbox(label="トランスクリプト", lines=20, show_copy_button=True)
        original_text_output = gr.Textbox(label="元のテキスト", lines=10, visible=False)
        error_output = gr.Textbox(visible=False, elem_id="error_output")  # Hidden textbox to store error message

        use_edited_transcript = gr.Checkbox(label="編集済みトランスクリプトを使用（最初に生成されたトランスクリプトを編集する場合はチェックしてください）", value=False)
        edited_transcript = gr.Textbox(label="ここでトランスクリプトを編集してください。例: テキストに編集指示を明確に記載します。例: '[マテリオミクスの定義を追加]'", lines=20, visible=False,
                                       show_copy_button=True, interactive=False)

        user_feedback = gr.Textbox(label="フィードバックやメモを入力", lines=10, #placeholder="フィードバックやメモをここに入力してください..."
                                   )
        regenerate_btn = gr.Button("編集とフィードバックを反映してオーディオを再生成")
        # Function to update the interactive state of edited_transcript
        def update_edit_box(checkbox_value):
            return gr.update(interactive=checkbox_value, lines=20 if checkbox_value else 20, visible=True if checkbox_value else False)

        # Update the interactive state of edited_transcript when the checkbox is toggled
        use_edited_transcript.change(
            fn=update_edit_box,
            inputs=[use_edited_transcript],
            outputs=[edited_transcript]
        )
        # Update instruction fields when template is changed
        template_dropdown.change(
            fn=update_instructions,
            inputs=[template_dropdown],
            outputs=[intro_instructions, text_instructions, scratch_pad_instructions, prelude_dialog, podcast_dialog_instructions]
        )

        submit_btn.click(
            fn=process_feedback_and_regenerate,
            inputs=[
                files,  # ファイルを最初に
                text_model,  # モデル名
                audio_model,  # TTSモデル
                speaker_1_voice,  # ホストの声
                speaker_2_voice,  # ゲストの声
                template_dropdown,  # 指示テンプレート
                openai_api_key,  # APIキー
                api_base,  # APIベースURL
                intro_instructions,
                text_instructions,
                scratch_pad_instructions,
                prelude_dialog,
                podcast_dialog_instructions,
                edited_transcript,
                user_feedback
            ],
            outputs=[audio_output, transcript_output, original_text_output, error_output]
        ).then(
            fn=lambda audio, transcript, original_text, error: (
                transcript if transcript else "",
                error if error else None
            ),
            inputs=[audio_output, transcript_output, original_text_output, error_output],
            outputs=[edited_transcript, error_output]
        ).then(
            fn=lambda error: gr.Warning(error) if error else None,
            inputs=[error_output],
            outputs=[]
        )

        regenerate_btn.click(
            fn=lambda use_edit, edit, *args: process_feedback_and_regenerate(
                args[0],  # files
                args[1],  # text_model
                args[2],  # audio_model
                args[3],  # speaker_1_voice
                args[4],  # speaker_2_voice
                args[5],  # template_dropdown
                args[6],  # openai_api_key
                args[7],  # api_base
                args[8],  # intro_instructions
                args[9],  # text_instructions
                args[10],  # scratch_pad_instructions
                args[11],  # prelude_dialog
                args[12],  # podcast_dialog_instructions
                edit if use_edit else "",  # edited_transcript
                args[13]  # user_feedback
            ),
            inputs=[
                use_edited_transcript,
                edited_transcript,
                files,
                text_model,
                audio_model,
                speaker_1_voice,
                speaker_2_voice,
                template_dropdown,
                openai_api_key,
                api_base,
                intro_instructions,
                text_instructions,
                scratch_pad_instructions,
                prelude_dialog,
                podcast_dialog_instructions,
                user_feedback
            ],
            outputs=[audio_output, transcript_output, original_text_output, error_output]
        ).then(
            fn=lambda audio, transcript, original_text, error: (
                transcript if transcript else "",
                error if error else None
            ),
            inputs=[audio_output, transcript_output, original_text_output, error_output],
            outputs=[edited_transcript, error_output]
        ).then(
            fn=lambda error: gr.Warning(error) if error else None,
            inputs=[error_output],
            outputs=[]
        )
                
    return demo
