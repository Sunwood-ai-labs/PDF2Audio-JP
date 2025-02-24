def process_feedback_and_regenerate(feedback, *args):
    # Add user feedback to the args
    new_args = list(args)
    new_args.append(feedback)  # Add user feedback as a new argument
    return validate_and_generate_audio(*new_args)

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

    files = args[0]
    if not files:
        return None, None, None, "Please upload at least one PDF file before generating audio."
    try:
        # Combine text from uploaded files
        combined_text = ""
        for file in files:
            with Path(file).open("rb") as f:
                reader = PdfReader(f)
                text = "\n\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
                combined_text += text + "\n\n"

        # Generate dialogue
        intro_instructions = args[7]
        text_instructions = args[8]
        scratch_pad_instructions = args[9]
        prelude_dialog = args[10]
        podcast_dialog_instructions = args[11]
        openai_api_key = args[1]
        text_model = args[2]
        api_base = args[6]

        edited_transcript = args[12] if len(args) > 12 else ""
        user_feedback = args[13] if len(args) > 13 else ""

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
        speaker_1_voice = args[4]
        speaker_2_voice = args[5]
        audio_model = args[3]
        audio_file = generate_audio_from_transcript(dialogue.dialogue, speaker_1_voice, speaker_2_voice, audio_model, openai_api_key)

        # Prepare transcript for output
        transcript = ""
        for line in dialogue.dialogue:
            transcript += f"{line.speaker}: {line.text}\n\n"

        return audio_file, transcript, combined_text, None  # Return None as the error when successful
    except Exception as e:
        # If an error occurs during generation, return None for the outputs and the error message
        return None, None, None, str(e)
