import gradio as gr
from components.instruction_templates import INSTRUCTION_TEMPLATES
from components.utility_functions import read_readme, update_instructions
from components.standard_values import STANDARD_TEXT_MODELS, STANDARD_AUDIO_MODELS, STANDARD_VOICES
from components.feedback_processing import process_feedback_and_regenerate

def gradio_ui():
    with gr.Blocks(title="PDF to Audio", css="""
        #header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            background-color: transparent;
            border-bottom: 1px solid #ddd;
        }
        #title {
            font-size: 24px;
            margin: 0;
        }
        #logo_container {
            width: 200px;
            height: 200px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        #logo_image {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        #main_container {
            margin-top: 20px;
        }
    """) as demo:
        
        with gr.Row(elem_id="header"):
            with gr.Column(scale=4):
                gr.Markdown("# Convert PDFs into an audio podcast, lecture, summary and others\n\nFirst, upload one or more PDFs, select options, then push Generate Audio.\n\nYou can also select a variety of custom option and direct the way the result is generated.", elem_id="title")
            with gr.Column(scale=1):
                gr.HTML('''
                    <div id="logo_container">
                        <img src="https://huggingface.co/spaces/lamm-mit/PDF2Audio/resolve/main/logo.png" id="logo_image" alt="Logo">
                    </div>
                ''')
        #gr.Markdown("")    
        submit_btn = gr.Button("Generate Audio", elem_id="submit_btn")

        with gr.Row(elem_id="main_container"):
            with gr.Column(scale=2):
                files = gr.Files(label="PDFs", file_types=["pdf"], )
                
                openai_api_key = gr.Textbox(
                    label="OpenAI API Key",
                    visible=True,  # Always show the API key field
                    placeholder="Enter your OpenAI API Key here...",
                    type="password"  # Hide the API key input
                )
                text_model = gr.Dropdown(
                    label="Text Generation Model",
                    choices=STANDARD_TEXT_MODELS,
                    value="o1-preview-2024-09-12", #"gpt-4o-mini",
                    info="Select the model to generate the dialogue text.",
                )
                audio_model = gr.Dropdown(
                    label="Audio Generation Model",
                    choices=STANDARD_AUDIO_MODELS,
                    value="tts-1",
                    info="Select the model to generate the audio.",
                )
                speaker_1_voice = gr.Dropdown(
                    label="Speaker 1 Voice",
                    choices=STANDARD_VOICES,
                    value="alloy",
                    info="Select the voice for Speaker 1.",
                )
                speaker_2_voice = gr.Dropdown(
                    label="Speaker 2 Voice",
                    choices=STANDARD_VOICES,
                    value="echo",
                    info="Select the voice for Speaker 2.",
                )
                api_base = gr.Textbox(
                    label="Custom API Base",
                    placeholder="Enter custom API base URL if using a custom/local model...",
                    info="If you are using a custom or local model, provide the API base URL here, e.g.: http://localhost:8080/v1 for llama.cpp REST server.",
                )

            with gr.Column(scale=3):
                template_dropdown = gr.Dropdown(
                    label="Instruction Template",
                    choices=list(INSTRUCTION_TEMPLATES.keys()),
                    value="podcast",
                    info="Select the instruction template to use. You can also edit any of the fields for more tailored results.",
                )
                intro_instructions = gr.Textbox(
                    label="Intro Instructions",
                    lines=10,
                    value=INSTRUCTION_TEMPLATES["podcast"]["intro"],
                    info="Provide the introductory instructions for generating the dialogue.",
                )
                text_instructions = gr.Textbox(
                    label="Standard Text Analysis Instructions",
                    lines=10,
                    placeholder="Enter text analysis instructions...",
                    value=INSTRUCTION_TEMPLATES["podcast"]["text_instructions"],
                    info="Provide the instructions for analyzing the raw data and text.",
                )
                scratch_pad_instructions = gr.Textbox(
                    label="Scratch Pad Instructions",
                    lines=15,
                    value=INSTRUCTION_TEMPLATES["podcast"]["scratch_pad"],
                    info="Provide the scratch pad instructions for brainstorming presentation/dialogue content.",
                )
                prelude_dialog = gr.Textbox(
                    label="Prelude Dialog",
                    lines=5,
                    value=INSTRUCTION_TEMPLATES["podcast"]["prelude"],
                    info="Provide the prelude instructions before the presentation/dialogue is developed.",
                )
                podcast_dialog_instructions = gr.Textbox(
                    label="Podcast Dialog Instructions",
                    lines=20,
                    value=INSTRUCTION_TEMPLATES["podcast"]["dialog"],
                    info="Provide the instructions for generating the presentation or podcast dialogue.",
                )

        audio_output = gr.Audio(label="Audio", format="mp3", interactive=False, autoplay=False)
        transcript_output = gr.Textbox(label="Transcript", lines=20, show_copy_button=True)
        original_text_output = gr.Textbox(label="Original Text", lines=10, visible=False)
        error_output = gr.Textbox(visible=False, elem_id="error_output")  # Hidden textbox to store error message

        use_edited_transcript = gr.Checkbox(label="Use Edited Transcript (check if you want to make edits to the initially generated transcript)", value=False)
        edited_transcript = gr.Textbox(label="Edit Transcript Here. E.g., mark edits in the text with clear instructions. E.g., '[ADD DEFINITION OF MATERIOMICS]'.", lines=20, visible=False,
                                       show_copy_button=True, interactive=False)

        user_feedback = gr.Textbox(label="Provide Feedback or Notes", lines=10, #placeholder="Enter your feedback or notes here..."
                                   )
        regenerate_btn = gr.Button("Regenerate Audio with Edits and Feedback")
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
                files, openai_api_key, text_model, audio_model, 
                speaker_1_voice, speaker_2_voice, api_base,
                intro_instructions, text_instructions, scratch_pad_instructions, 
                prelude_dialog, podcast_dialog_instructions, 
                edited_transcript,  # placeholder for edited_transcript
                user_feedback,  # placeholder for user_feedback
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
                *args[:12],  # All inputs up to podcast_dialog_instructions
                edit if use_edit else "",  # Use edited transcript if checkbox is checked, otherwise empty string
                *args[12:]  # user_feedback and original_text_output
            ),
            inputs=[
                use_edited_transcript, edited_transcript,
                files, openai_api_key, text_model, audio_model, 
                speaker_1_voice, speaker_2_voice, api_base,
                intro_instructions, text_instructions, scratch_pad_instructions, 
                prelude_dialog, podcast_dialog_instructions,
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
        
        # Add README content at the bottom
        gr.Markdown("---")  # Horizontal line to separate the interface from README
        gr.Markdown(read_readme())
        
    return demo
