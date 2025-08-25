#!.venv/bin/python3

import datetime
import json
import os

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, stream_with_context
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
model_mapping = {
    "llama2": "meta-llama/llama-2-13b-chat",
    "mistral": "mistralai/mistral-7b-instruct",
    "gpt-3.5-turbo": "openai/gpt-4.1-mini",
    # Add more mappings as needed
}

from typing import Dict


def extra_headers() -> Dict[str, str]:
    "Showing where the request comes from, or defaulting to the github repo for clarity in billing."
    return {
        "HTTP-Referer": request.headers.get(
            "HTTP-Referer", "https://github.com/educationwarehouse/forwardllm"
        ),
        "X-Title": "Ollama to OpenRouter Proxy",
    }


app = Flask(__name__)


def generate_stream(
    for_what_function: callable, completion: Stream[ChatCompletionChunk], model: str
):
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            response = {
                "model": model,
                "created_at": str(datetime.datetime.now().timestamp()),
                "done": False,
            }
            if for_what_function == chat:
                response |= {
                    "message": {
                        "role": "assistant",
                        "content": chunk.choices[0].delta.content,
                    }
                }
            else:
                response |= {"response": chunk.choices[0].delta.content}
            yield f"{json.dumps(response)}\n"

    # Send final done message
    final_response = {
        "model": model,
        "created_at": str(datetime.datetime.now().timestamp()),
        "done": True,
    }
    if for_what_function == chat:
        final_response |= {"response": ""}
    else:
        final_response |= {"message": {"role": "assistant", "content": ""}}
    yield f"{json.dumps(final_response)}\n"


@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Handle generation requests by forwarding them to the OpenRouter API.

    This endpoint accepts a JSON payload containing a model name, prompt text, streaming preference,
    and generation options. It maps the requested model to an OpenRouter-compatible model, sends the
    completion request, and returns the response in Ollama-compatible format.

    Returns:
        JSON response containing the generated text and metadata if not streaming.
        A streaming response if stream=True, yielding partial completion chunks.

    Error Handling:
        Raises the original exception and returns a JSON error message with HTTP status 500 if an exception occurs.
    """
    try:
        # Get request data
        data = request.json
        # Extract parameters from Ollama request
        model = data.get(
            "model", "openai/gpt-4.1-mini"
        )  # Default to GPT-3.5 if not specified
        prompt = data.get("prompt", "")
        stream = data.get("stream", False)
        options = data.get("options", {}) or {}

        openrouter_model = model_mapping.get(model, model)

        prompt = prompt or "?"
        # Send request to OpenRouter using OpenAI client
        completion = client.chat.completions.create(
            extra_headers=extra_headers(),
            model=openrouter_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=options.get("temperature", 0.7),
            top_p=options.get("top_p", 0.9),
            max_tokens=options.get("num_predict", -1),
            stream=stream,
        )

        if not stream:
            # Transform OpenAI client response to Ollama format
            ollama_response = {
                "model": model,
                "created_at": str(completion.created),
                "response": completion.choices[0].message.content,
                "done": True,
            }
            return jsonify(ollama_response)
        else:
            return Response(
                stream_with_context(generate_stream(chat, completion, model)),
                mimetype="text/event-stream",
            )

    except Exception as e:
        raise
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Handle chat requests by forwarding them to the OpenRouter API.

    This endpoint accepts a JSON payload containing model details, messages, streaming preference, and options.
    It maps the requested model to an OpenRouter-compatible model, sends the chat completion request,
    and returns the response in Ollama-compatible format.

    Returns:
        JSON response containing the assistant's message and metadata if not streaming.
        A streaming response if stream=True, yielding partial chat completion chunks.

    Error Handling:
        Returns a JSON error message with HTTP status 500 if an exception occurs.
    """
    try:
        # Get request data
        data = request.json
        print(json.dumps(data, indent=2))
        # Extract parameters from Ollama request
        model = data.get(
            "model", "openai/gpt-4.1-nano"
        )  # Default to GPT-3.5 if not specified
        messages = data.get("messages", [])
        stream = data.get("stream", False)
        options = data.get("options", {})

        openrouter_model = model_mapping.get(model, model)

        # Set up extra headers for OpenRouter

        # Send request to OpenRouter using OpenAI client
        completion: ChatCompletion | Stream[ChatCompletionChunk] = (
            client.chat.completions.create(
                extra_headers=extra_headers(),
                model=openrouter_model,
                messages=messages,
                temperature=options.get("temperature", 0.7),
                top_p=options.get("top_p", 0.9),
                max_tokens=options.get("num_predict", -1),
                stream=stream,
            )
        )
        if not stream:
            # Transform OpenAI client response to Ollama format
            assistant_message = {
                "role": "assistant",
                "content": completion.choices[0].message.content,
            }
            ollama_response = {
                "model": model,
                "created_at": str(completion.created),
                "message": assistant_message,
                "done": True,
            }
            return jsonify(ollama_response)
        else:
            return Response(
                stream_with_context(generate_stream(chat, completion, model)),
                mimetype="text/event-stream",
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/show", methods=["GET", "POST"])
def show():
    """
    Handle Ollama-style show requests to display model information
    """
    try:
        if request.method == "GET":
            model = request.args.get("name", "gpt-3.5-turbo")
        else:
            data = request.json
            model = data.get("name", "gpt-3.5-turbo")
        openrouter_model = model_mapping.get(model, model)

        # Mock response in Ollama format
        model_info = {
            "license": "apache-2.0",
            "modelfile": "",
            "parameters": "Unknown",
            "template": "{{ .Prompt }}",
            "name": model,
            "model_info": {
                "format": "api",
                "family": openrouter_model.split("/")[0]
                if "/" in openrouter_model
                else "",
                "parameter_size": "Unknown",
                "quantization_level": "none",
            },
        }

        return jsonify(model_info)

    except Exception as e:
        raise
        return jsonify({"error": str(e)}), 500


def convert_timestamp(epoch_time):
    """Convert epoch timestamp to ISO 8601 format with timezone"""
    dt = datetime.datetime.fromtimestamp(epoch_time)
    timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    dt = dt.replace(tzinfo=timezone)
    return dt.isoformat()


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
            "X-Title": "Ollama to OpenRouter Proxy",
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
            parts = model_id.split("/")
            provider = parts[0] if len(parts) > 1 else ""

            # Create a model entry with the required structure
            model_entry = {
                "name": model.id,
                "model": model.id,
                "modified_at": convert_timestamp(created_timestamp),
                "size": getattr(model, "size", 0),
                "digest": getattr(
                    model,
                    "digest",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ),
                "details": {
                    "parent_model": "",
                    "format": getattr(model, "format", "api"),
                    "family": provider,
                    "families": [provider] if provider else [],
                    "parameter_size": getattr(model, "parameter_size", "Unknown"),
                    "quantization_level": "N/A",
                    "context_length": getattr(model, "context_length", 4096),
                    "capabilities": getattr(
                        model, "capabilities", ["chat", "completion"]
                    ),
                    "description": getattr(model, "description", ""),
                    "pricing": getattr(model, "pricing", {}),
                },
            }

            models.append(model_entry)
        # Return the models in the expected format
        return jsonify({"models": sorted(models, key=lambda d: d["name"])})

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
                    "quantization_level": "N/A",
                },
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
                    "quantization_level": "N/A",
                },
            },
        ]

        return jsonify({"models": fallback_models})


@app.route("/", methods=["GET"])
def index():
    """
    Root endpoint providing API metadata.

    Returns a JSON object containing the name, description, version, and a list of available endpoints
    for the Ollama to OpenRouter Proxy server. This can be used as a simple health or info check.

    Example response:
    {
        "name": "Ollama to OpenRouter Proxy",
        "description": "A proxy server that forwards Ollama API requests to OpenRouter",
        "version": "1.0.0",
        "endpoints": ["/api/generate", "/api/chat", "/api/models", "/api/tags"]
    }
    """

    info = {
        "name": "Ollama to OpenRouter Proxy",
        "description": "A proxy server that forwards Ollama API requests to OpenRouter",
        "version": "1.0.0",
        "endpoints": ["/api/generate", "/api/chat", "/api/models", "/api/tags"],
    }
    return jsonify(info)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 11434))  # Default Ollama port is 11434
    app.run(host="0.0.0.0", port=port, debug=True)
