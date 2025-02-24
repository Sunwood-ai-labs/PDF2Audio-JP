import os

def load_prompt(filepath):
    with open(filepath, 'r') as f:
        return f.read()

# Define multiple sets of instruction templates
INSTRUCTION_TEMPLATES = {
################# PODCAST ##################
    "podcast": {
        "intro": load_prompt(os.path.join("components", "prompts", "podcast_intro.md")),
        "text_instructions": load_prompt(os.path.join("components", "prompts", "podcast_text_instructions.md")),
        "scratch_pad": load_prompt(os.path.join("components", "prompts", "podcast_scratch_pad.md")),
        "prelude": load_prompt(os.path.join("components", "prompts", "podcast_prelude.md")),
        "dialog": load_prompt(os.path.join("components", "prompts", "podcast_dialog.md")),
    },
################# MATERIAL DISCOVERY SUMMARY ##################
    "SciAgents material discovery summary": {
        "intro": load_prompt(os.path.join("components", "prompts", "sciagents_intro.md")),
        "text_instructions": load_prompt(os.path.join("components", "prompts", "sciagents_text_instructions.md")),
        "scratch_pad": load_prompt(os.path.join("components", "prompts", "sciagents_scratch_pad.md")),
        "prelude": load_prompt(os.path.join("components", "prompts", "sciagents_prelude.md")),
        "dialog": load_prompt(os.path.join("components", "prompts", "sciagents_dialog.md")),
    },
################# LECTURE ##################
    "lecture": {
        "intro": load_prompt(os.path.join("components", "prompts", "lecture_intro.md")),
        "text_instructions": load_prompt(os.path.join("components", "prompts", "lecture_text_instructions.md")),
        "scratch_pad": load_prompt(os.path.join("components", "prompts", "lecture_scratch_pad.md")),
        "prelude": load_prompt(os.path.join("components", "prompts", "lecture_prelude.md")),
        "dialog": load_prompt(os.path.join("components", "prompts", "lecture_dialog.md")),
    },
################# SUMMARY ##################
    "summary": {
        "intro": load_prompt(os.path.join("components", "prompts", "summary_intro.md")),
        "text_instructions": load_prompt(os.path.join("components", "prompts", "summary_text_instructions.md")),
        "scratch_pad": load_prompt(os.path.join("components", "prompts", "summary_scratch_pad.md")),
        "prelude": load_prompt(os.path.join("components", "prompts", "summary_prelude.md")),
        "dialog": load_prompt(os.path.join("components", "prompts", "summary_dialog.md")),
    },
################# SHORT SUMMARY ##################
    "short summary": {
        "intro": load_prompt(os.path.join("components", "prompts", "short_summary_intro.md")),
        "text_instructions": load_prompt(os.path.join("components", "prompts", "short_summary_text_instructions.md")),
        "scratch_pad": load_prompt(os.path.join("components", "prompts", "short_summary_scratch_pad.md")),
        "prelude": load_prompt(os.path.join("components", "prompts", "short_summary_prelude.md")),
        "dialog": load_prompt(os.path.join("components", "prompts", "short_summary_dialog.md")),
    },
}
