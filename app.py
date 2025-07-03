import datetime
import os
import json
from flask import Flask, request, jsonify, Response, stream_with_context
from dotenv import load_dotenv
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

# Load environment variables
load_dotenv()

# Get API keys from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is required")

# Initialize OpenAI client with OpenRouter base URL
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Map Ollama model to OpenRouter model if needed
# This is a simple mapping, you might want to expand it
model_mapping = {"llama2": "meta-llama/llama-2-13b-chat", "mistral": "mistralai/mistral-7b-instruct", "gpt-3.5-turbo": "openai/gpt-4.1-mini"
    # Add more mappings as needed
}

app = Flask(__name__)

@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Handle Ollama-style generate requests and forward to OpenRouter

    Ollama API format:
    {
        "model": "llama2",
        "prompt": "Why is the sky blue?",
        "stream": false,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            ...
        }
    }

    OpenRouter API format:
    {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Why is the sky blue?"}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        ...
    }
    """
    try:
        # Get request data
        data = request.json

        # Extract parameters from Ollama request
        model = data.get("model", "openai/gpt-4.1-mini")  # Default to GPT-3.5 if not specified
        prompt = data.get("prompt", "")
        stream = data.get("stream", False)
        options = data.get("options", {})




        openrouter_model = model_mapping.get(model, model)

        # Prepare OpenRouter request
        openrouter_request = {
            "model": openrouter_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            # Forward relevant options
            "temperature": options.get("temperature", 0.7),
            "top_p": options.get("top_p", 0.9),
            "max_tokens": options.get("num_predict", 100),
            "stream": stream
        }

        # Set up extra headers for OpenRouter
        extra_headers = {
            "HTTP-Referer": request.headers.get("HTTP-Referer", "https://localhost"),
            "X-Title": "Ollama to OpenRouter Proxy"
        }

        # Send request to OpenRouter using OpenAI client
        completion = client.chat.completions.create(
            extra_headers=extra_headers,
            model=openrouter_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.get("temperature", 0.7),
            top_p=options.get("top_p", 0.9),
            max_tokens=options.get("num_predict", 100),
            stream=stream
        )

        if not stream:
            # Transform OpenAI client response to Ollama format
            ollama_response = {"model": model, "created_at": completion.created, "response": completion.choices[0].message.content, "done": True}
            return jsonify(ollama_response)
        else:
            def generate():
                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        response = {"model": model, "created_at": datetime.datetime.now().timestamp(), "response": chunk.choices[0].delta.content,
                            "done": False}
                        print(response)
                        yield json.dumps(response)+'\n'

                # Send final done message
                final_response = {"model": model, "created_at": datetime.datetime.now().timestamp(), "response": "", "done": True}
                print(final_response)
                yield json.dumps(final_response)+'\n'

            return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Handle Ollama-style chat requests and forward to OpenRouter

    Ollama API format:
    {
        "model": "llama2",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "Tell me a joke."}
        ],
        "stream": false,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            ...
        }
    }

    OpenRouter API format is similar but may have different parameter names
    """
    try:
        # Get request data
        data = request.json
        print(data)
        # Extract parameters from Ollama request
        model = data.get("model", "openai/gpt-3.5-turbo")  # Default to GPT-3.5 if not specified
        messages = data.get("messages", [])
        stream = data.get("stream", False)
        options = data.get("options", {})

        openrouter_model = model_mapping.get(model, model)

        # Prepare OpenRouter request
        openrouter_request = {
            "model": openrouter_model,
            "messages": messages,
            # Forward relevant options
            "temperature": options.get("temperature", 0.7),
            "top_p": options.get("top_p", 0.9),
            "max_tokens": options.get("num_predict", 100),
            "stream": stream
        }

        # Set up extra headers for OpenRouter
        extra_headers = {
            "HTTP-Referer": request.headers.get("HTTP-Referer", "https://localhost"),
            "X-Title": "Ollama to OpenRouter Proxy"
        }

        # Send request to OpenRouter using OpenAI client
        completion:ChatCompletion|Stream[ChatCompletionChunk] = client.chat.completions.create(
            extra_headers=extra_headers,
            model=openrouter_model,
            messages=messages,
            temperature=options.get("temperature", 0.7),
            top_p=options.get("top_p", 0.9),
            max_tokens=options.get("num_predict", 100),
            stream=stream
        )
        if not stream: 
            # Transform OpenAI client response to Ollama format
            assistant_message = {
                "role": "assistant",
                "content": completion.choices[0].message.content
            }
    
            ollama_response = {
                "model": model,
                "created_at": completion.created,
                "message": assistant_message,
                "done": True
            }
            print(ollama_response)
            return jsonify(ollama_response)
        else:
            def generate():
                for chunk in completion:
                    if chunk.choices[0].delta.content is not None:
                        response = {"model": model, "created_at": datetime.datetime.now().timestamp(),
                            "message": {"role": "assistant", "content": chunk.choices[0].delta.content}, "done": False}
                        print(response)
                        yield json.dumps(response)

                # Send final done message
                final_response = {"model": model, "created_at": datetime.datetime.now().timestamp(), "message": {"role": "assistant", "content": ""},
                    "done": True}
                print(final_response)
                yield json.dumps(final_response)

            return Response(stream_with_context(generate()), mimetype='text/event-stream')


    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tags", methods=["GET"])
def list_tags():
    """
    Return a list of available tags for models
    This implementation dynamically fetches model information from OpenRouter
    """
    try:
        # Set up extra headers for OpenRouter
        extra_headers = {
            "HTTP-Referer": request.headers.get("HTTP-Referer", "https://localhost"),
            "X-Title": "Ollama to OpenRouter Proxy"
        }

        # Fetch models from OpenRouter
        openrouter_models = client.models.list(extra_headers=extra_headers)

        # Transform OpenRouter response to match expected format
        models = []

        for model in openrouter_models.data:
            # Extract model ID and other information
            model_id = model.id
            created_timestamp = model.created
            # Parse model information to extract details
            # Format: provider/model-name
            parts = model_id.split('/')
            provider = parts[0] if len(parts) > 1 else ""

            # Create a model entry with the required structure
            model_entry = {
                "name": model.name,
                "model": model_id,
                "modified_at": created_timestamp.isoformat() if hasattr(created_timestamp, 'isoformat') else datetime.datetime.fromtimestamp(created_timestamp),
                "size": getattr(model, 'size', 1337),
                "digest": getattr(model, 'digest', "b867d0390a901bd0bd778f256be38751b2029c756feda5503493b90f57896620"),
                "details": {
                    "parent_model": "",
                    "format": getattr(model,'format','api'),
                    "family": provider,
                    "families": [provider] if provider else [],
                    "parameter_size": getattr(model, 'parameter_size', "Unknown"),
                    "quantization_level": "N/A", "context_length": getattr(model, 'context_length', 4096),
                    "capabilities": getattr(model, 'capabilities', ["chat", "completion"]), "description": getattr(model, 'description', ""),
                    "pricing": getattr(model, 'pricing', {})
                }
            }

            models.append(model_entry)
        # Return the models in the expected format
        return jsonify({"models": sorted(models, key=lambda d:d['name'])})

    except Exception as e:
        # If there's an error fetching from OpenRouter, fall back to a minimal static list
        app.logger.error(f"Error fetching models from OpenRouter: {str(e)}")

        # Create a minimal fallback list
        fallback_models = [
            {
                "name": "gpt-3.5-turbo",
                "model": "openai/gpt-3.5-turbo",
                "modified_at": "2023-01-01T00:00:00Z",
                "size": 0,
                "digest": "",
                "details": {
                    "parent_model": "",
                    "format": "api",
                    "family": "openai",
                    "families": ["openai"],
                    "parameter_size": "Unknown",
                    "quantization_level": "N/A"
                }
            },
            {
                "name": "gpt-4",
                "model": "openai/gpt-4",
                "modified_at": "2023-01-01T00:00:00Z",
                "size": 0,
                "digest": "",
                "details": {
                    "parent_model": "",
                    "format": "api",
                    "family": "openai",
                    "families": ["openai"],
                    "parameter_size": "Unknown",
                    "quantization_level": "N/A"
                }
            }
        ]

        return jsonify({"models": fallback_models})

@app.route("/", methods=["GET"])
def index():
    """
    Root endpoint that provides basic information about the API
    """
    info = {
        "name": "Ollama to OpenRouter Proxy",
        "description": "A proxy server that forwards Ollama API requests to OpenRouter",
        "version": "1.0.0",
        "endpoints": [
            "/api/generate",
            "/api/chat",
            "/api/models",
            "/api/tags"
        ]
    }

    return jsonify(info)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 11434))  # Default Ollama port is 11434
    app.run(host="0.0.0.0", port=port, debug=True)
