import os
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception_type
from promptic import llm
from functools import wraps

def conditional_llm(model, api_base=None, api_key=None):
    """
    Conditionally apply the @llm decorator based on the api_base parameter.
    If api_base is provided, it applies the @llm decorator with api_base.
    Otherwise, it applies the @llm decorator without api_base.
    """
    def decorator(func):
        if api_base:
            return llm(model=model, api_base=api_base)(func)
        else:
            return llm(model=model, api_key=api_key)(func)
    return decorator

@retry(retry=retry_if_exception_type(ValidationError))
@conditional_llm(model="o1-preview-2024-09-12", api_base=None, api_key=None)
def generate_dialogue(text: str, intro_instructions: str, text_instructions: str, scratch_pad_instructions: str, 
                      prelude_dialog: str, podcast_dialog_instructions: str,
                      edited_transcript: str = None, user_feedback: str = None, ) -> "Dialogue":
    """
    {intro_instructions}
    
    Here is the original input text:
    
    <input_text>
    {text}
    </input_text>

    {text_instructions}
    
    <scratchpad>
    {scratch_pad_instructions}
    </scratchpad>
    
    {prelude_dialog}
    
    <podcast_dialogue>
    {podcast_dialog_instructions}
    </podcast_dialogue>
    {edited_transcript}{user_feedback}
    """

    # This is a hack to make the type checker happy
    class Dialogue(BaseModel):
        scratchpad: str
        dialogue: list

    return Dialogue(scratchpad="", dialogue=[])
