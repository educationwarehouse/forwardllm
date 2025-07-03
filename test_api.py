#!/usr/bin/env python3
"""
Simple test script to verify the Ollama to OpenRouter proxy is working correctly.
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for the API
BASE_URL = "http://localhost:11434/api"


def test_generate():
    """Test the /api/generate endpoint"""
    print("\n=== Testing /api/generate ===")

    data = {
        "model": "gpt-3.5-turbo",
        "prompt": "Tell me a short joke about programming",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    print(f"Sending request to generate endpoint with model: {data['model']}")
    print(f"Prompt: {data['prompt']}")

    response = requests.post(f"{BASE_URL}/generate", json=data)

    if response.status_code == 200:
        result = response.json()
        print("✅ Successfully generated response")
        print(f"Response: {result.get('response', '')}")
    else:
        print(f"❌ Failed to generate response: {response.status_code}")
        print(response.text)


def test_generate_stream():
    """Test the /api/generate endpoint with streaming enabled"""
    print("\n=== Testing /api/generate with streaming ===")

    data = {"model": "gpt-3.5-turbo", "prompt": "Count from 1 to 5 slowly", "stream": True, "options": {"temperature": 0.7, "top_p": 0.9}}

    print(f"Sending request to generate endpoint with model: {data['model']}")
    print(f"Prompt: {data['prompt']}")

    response = requests.post(f"{BASE_URL}/generate", json=data, stream=True)

    if response.status_code == 200:
        print("✅ Successfully started stream")
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    print(f"Stream chunk: {json_response.get('response', '')}", end='', flush=True)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON: {line}")
        print("\nStream completed")
    else:
        print(f"❌ Failed to start stream: {response.status_code}")
        print(response.text)


def test_chat():
    """Test the /api/chat endpoint"""
    print("\n=== Testing /api/chat ===")

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, thank you!"},
            {"role": "user", "content": "Tell me a short joke about programming."}
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    print(f"Sending request to chat endpoint with model: {data['model']}")
    print(f"Last message: {data['messages'][-1]['content']}")

    response = requests.post(f"{BASE_URL}/chat", json=data)

    if response.status_code == 200:
        result = response.json()
        print("✅ Successfully received chat response")
        print(f"Response: {result.get('message', {}).get('content', '')}")
    else:
        print(f"❌ Failed to get chat response: {response.status_code}")
        print(response.text)

def test_tags():
    """Test the /api/tags endpoint"""
    print("\n=== Testing /api/tags ===")
    response = requests.get(f"{BASE_URL}/tags")

    if response.status_code == 200:
        print("✅ Successfully retrieved tags")
        result = response.json()

        # Check if the response has the expected structure
        if "models" in result and isinstance(result["models"], list):
            models = result["models"]
            print(f"Available models: {len(models)}")

            # Print the first model as an example
            if models:
                first_model = models[0]
                print(f"Example model: {first_model['name']}")
                print(f"  - Size: {first_model.get('size', 'N/A')}")
                print(f"  - Family: {first_model.get('details', {}).get('family', 'N/A')}")
                print(f"  - Parameter size: {first_model.get('details', {}).get('parameter_size', 'N/A')}")
                print(f"  - Quantization level: {first_model.get('details', {}).get('quantization_level', 'N/A')}")
                print(json.dumps(first_model, indent=2))
        else:
            print("❌ Response does not have the expected structure")
            print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ Failed to retrieve tags: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Testing Ollama to OpenRouter Proxy API")
    print("Make sure the server is running (python app.py) before running this test")

    # Check if OPENROUTER_API_KEY is set
    if not os.getenv("OPENROUTER_API_KEY"):
        print("⚠️  Warning: OPENROUTER_API_KEY environment variable is not set.")
        print("   The tests will likely fail. Make sure to set it in your .env file.")

    # Run tests
    # test_generate()
    test_generate_stream()
    # test_chat()
    test_tags()

    print("\nTests completed!")
