import os
import gradio as gr
from agent import PydanticAgent
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free") # Use a robust model for synthesis

if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

agent = PydanticAgent(api_key, model)

def run_deep_research(user_query: str, progress=gr.Progress()):
    if not user_query.strip():
        return "Please provide a valid query or ticker symbol."
    
    # Process multi-step pipeline
    response = agent.query(user_query, progress_cb=progress)
    return response.answer

with gr.Blocks(title="Deep Research Agent Engine") as demo:
    gr.Markdown("# 🔍 Deep Research Intelligence Agent")
    gr.Markdown("Submit a stock ticker (e.g., *NVDA*, *AAPL*) or complex analytical topic. The agent will isolate variables, execute real-time parallel search threads, and parse a complete intelligence brief.")
    
    with gr.Row():
        input_box = gr.Textbox(
            label="Research Target Request",
            placeholder="Enter ticker symbols or detailed research subjects...",
            lines=1,
            scale=4
        )
        submit_btn = gr.Button("Generate Deep Report", variant="primary", scale=1)
        
    output_markdown = gr.Markdown(label="Assembled Market Report Output")
    
    # Event wiring
    submit_btn.click(
        fn=lambda: gr.update(interactive=False, value="Generating..."), 
        outputs=[submit_btn]
    ).then(
        fn=run_deep_research,
        inputs=[input_box],
        outputs=[output_markdown]
    ).then(
        fn=lambda: gr.update(interactive=True, value="Generate Deep Report"), 
        outputs=[submit_btn]
    )

    input_box.submit(
        fn=lambda: gr.update(interactive=False, value="Generating..."), 
        outputs=[submit_btn]
    ).then(
        fn=run_deep_research,
        inputs=[input_box],
        outputs=[output_markdown]
    ).then(
        fn=lambda: gr.update(interactive=True, value="Generate Deep Report"), 
        outputs=[submit_btn]
    )

if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True
    )