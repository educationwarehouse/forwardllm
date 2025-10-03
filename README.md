# Ollama to OpenRouter Proxy

A Flask web application that acts as an Ollama-compatible server and forwards requests to OpenRouter. This allows you to use Ollama clients with OpenRouter's LLM models.

## Features

- Compatible with Ollama API clients
- Forwards requests to OpenRouter
- Supports both single prompt generation and chat conversations
- Maps Ollama model names to OpenRouter model names
- Configurable via environment variables

## Requirements

- Python 3.7+
- OpenRouter API key (get one at [https://openrouter.ai/keys](https://openrouter.ai/keys))
- Optionally, [uv](https://docs.astral.sh/uv/) for modern installation

## Modern Installation and Usage (with uv)

This is the recommended, streamlined way to run the app without manually managing virtual environments or pip:

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/ForwardLLM.git
   cd ForwardLLM
    ```

2. Create a `.env` file with your OpenRouter API key:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and replace `your_openrouter_api_key_here` with your OpenRouter API key.


3. Run the app directly with `uv`:

   ```bash
   uv run app.py
   ```

`uv` will automatically:

* Create a temporary isolated environment
* Install dependencies (Flask, python-dotenv, OpenAI, etc.)
* Run the proxy server

---

## Traditional Installation and Usage (venv + pip)

If you prefer the classic way:
1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ForwardLLM.git
   cd ForwardLLM
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your OpenRouter API key:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file and replace `your_openrouter_api_key_here` with your actual OpenRouter API key.

### Usage

1. Start the server:
   ```
   python app.py
   ```
   By default, the server runs on port 11434 (the same as Ollama).

2. Run the test script to verify everything is working:
   ```
   python test_api.py
   ```
   This will test all the API endpoints and show the results.

3. Use any Ollama client to connect to the server. For example, using curl:

   **Generate a response to a single prompt:**
   ```bash
   curl -X POST http://localhost:11434/api/generate -d '{
     "model": "gpt-3.5-turbo",
     "prompt": "Tell me a joke about programming",
     "stream": false
   }'
   ```

   **Chat conversation:**
   ```bash
   curl -X POST http://localhost:11434/api/chat -d '{
     "model": "gpt-3.5-turbo",
     "messages": [
       {"role": "user", "content": "Hello, how are you?"},
       {"role": "assistant", "content": "I'm doing well, thank you!"},
       {"role": "user", "content": "Tell me a joke about programming."}
     ]
   }'
   ```

   **List available models:**
   ```bash
   curl http://localhost:11434/api/models
   ```

---

## Model Mapping

The application maps common Ollama model names to their OpenRouter equivalents:

* `llama2` → `meta-llama/llama-2-13b-chat`
* `mistral` → `mistralai/mistral-7b-instruct`

You can also directly use OpenRouter model names like `openai/gpt-4` or `anthropic/claude-2`.

---

## Configuration

Set the following environment variables in your `.env` file:

* `OPENROUTER_API_KEY` (required): Your OpenRouter API key
* `PORT` (optional): The port to run the server on (default: 11434)

---

## License

MIT
