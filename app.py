import gradio as gr
from components.gradio_ui import gradio_ui

demo = gradio_ui()

# Enable queueing for better performance
demo.queue(max_size=20, default_concurrency_limit=32)

# Launch the Gradio app
if __name__ == "__main__":
    demo.launch()
