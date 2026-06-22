"""
Gradio interface for Pydantic Agent
"""

import os
import gradio as gr
from agent import PydanticAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize agent
api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

agent = PydanticAgent(api_key, model)


def chat_interface(user_message: str, history: list) -> tuple[list, str]:
    """
    Chat interface for the Pydantic agent
    
    Args:
        user_message: User's question
        history: Chat history
        
    Returns:
        Updated history and empty input field
    """
    if not user_message.strip():
        return history, ""
    
    # Get response from agent
    response = agent.query(user_message)
    
    # Add to history in new Gradio format
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response.answer})
    
    return history, ""


def reset_chat():
    """Reset chat history"""
    return [], ""


# Create Gradio interface
with gr.Blocks(title="Pydantic Agent") as demo:
    gr.Markdown("# 🔧 Pydantic Agent")
    gr.Markdown("Ask anything about Pydantic! The agent will answer based on the documentation.")
    
    chatbot = gr.Chatbot(
        label="Chat History",
        height=400,
    )
    
    with gr.Row():
        msg = gr.Textbox(
            label="Your Question",
            placeholder="Ask a question about Pydantic...",
            lines=1,
            scale=5,
        )
        submit_btn = gr.Button("Send", scale=1)
    
    with gr.Row():
        clear_btn = gr.Button("Clear Chat", scale=1)
    
    gr.Markdown("---")
    gr.Markdown("""
    **Tips:**
    - Ask questions about Pydantic validation, models, and features
    - Answers are kept short and concise
    - Based on official Pydantic documentation
    """)
    
    # Set up event handlers
    submit_btn.click(
        chat_interface,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg],
    )
    
    msg.submit(
        chat_interface,
        inputs=[msg, chatbot],
        outputs=[chatbot, msg],
    )
    
    clear_btn.click(reset_chat, outputs=[chatbot, msg])


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        share=False,
    )
