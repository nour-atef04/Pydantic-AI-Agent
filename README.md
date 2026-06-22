# Pydantic Agent with Gradio

A simple AI agent that answers questions about Pydantic using OpenRouter's free models and a Gradio web interface.

## Features

- 🤖 **Pydantic-based validation** - Type-safe requests and responses
- 🎨 **Gradio interface** - Clean, user-friendly web UI
- 💰 **Free AI model** - Uses OpenRouter's free tier models
- 📚 **Doc-aware** - Answers based on provided documentation
- ⚡ **Lightweight** - Minimal dependencies, quick to set up

## Prerequisites

- Python 3.9 or higher
- OpenRouter API key (free at https://openrouter.io)

## Installation

### 1. Clone/Setup the project

```bash
cd Pydantic
```

### 2. Create a virtual environment (optional but recommended)

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get your OpenRouter API key

1. Go to https://openrouter.io
2. Sign up for a free account
3. Navigate to Keys section
4. Create a new API key

### 5. Configure environment variables

Edit the `.env` file and replace `your_api_key_here` with your actual OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-your-actual-key-here
OPENROUTER_MODEL=meta-llama/llama-2-7b-chat:free
```

**Optional:** Choose a different free model:

- `mistralai/mistral-7b-instruct:free` - Fast and capable
- `google/gemma-7b-it:free` - Google's lightweight model
- `huggingfaceh4/zephyr-7b-beta:free` - Based on Mistral

## Usage

### Run the web interface

```bash
python app.py
```

The application will be available at `http://localhost:7860`

### Testing the agent directly

```bash
python agent.py
```

This will test a sample query with the agent.

## Project Structure

```
Pydantic/
├── app.py                 # Gradio web interface
├── agent.py              # Main agent logic with Pydantic models
├── docs.md               # Pydantic documentation (knowledge base)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (your config)
├── .env.example          # Example configuration template
└── README.md             # This file
```

## How It Works

1. **User Input** → Question is validated with Pydantic `QueryRequest` model
2. **Doc Search** → Relevant sections from `docs.md` are extracted based on keywords
3. **API Call** → Question + context sent to OpenRouter's free model
4. **Response** → Answer is validated with Pydantic `AgentResponse` model
5. **Display** → Clean response shown in Gradio interface

## API Endpoints Used

- OpenRouter API: `https://openrouter.io/api/v1/chat/completions`
- Uses free-tier models (no authentication cost)

## Pydantic Models

### QueryRequest

- **question** (str): User's question (1-500 characters)

### AgentResponse

- **answer** (str): Short answer from the agent
- **source** (str, optional): Source reference

## Troubleshooting

### "OPENROUTER_API_KEY not set"

- Make sure `.env` file exists in the project folder
- Verify you've added your actual API key to `.env`
- Restart your terminal/IDE after changing `.env`

### "Connection error"

- Check your internet connection
- Verify your OpenRouter API key is valid
- Check if OpenRouter API is accessible

### "Request timed out"

- Try again - sometimes the free models are slow
- Consider using a faster model from the free options

### Gradio port already in use

- The app tries port 7860 by default
- Edit `app.py` to change `server_port=7860` to another port

## Performance Notes

- First request may take 5-10 seconds (model loading)
- Subsequent requests are faster
- Free models are rate-limited, so be patient between queries
- Answers are intentionally kept short for faster responses

## Examples

**Q:** What is Pydantic?
**A:** Pydantic is a data validation library for Python that uses type hints to validate data at runtime.

**Q:** How do I create a Pydantic model?
**A:** Define a class inheriting from BaseModel and add typed attributes.

## Dependencies

- **pydantic** - Data validation and parsing
- **gradio** - Web interface
- **requests** - HTTP client for OpenRouter API
- **python-dotenv** - Environment variable management

## Future Enhancements

- [ ] Memory/conversation history in database
- [ ] Multiple knowledge bases
- [ ] Advanced context matching
- [ ] Streaming responses
- [ ] Custom model selection via UI
- [ ] Docker support

## License

MIT

## Support

For issues with:

- **Pydantic**: https://docs.pydantic.dev
- **Gradio**: https://www.gradio.app
- **OpenRouter**: https://openrouter.io/docs
