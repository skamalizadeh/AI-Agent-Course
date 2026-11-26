
"""
Raw HTTP request to ArvanCloud AI.
No OpenAI library is used.

Use:
    python 1_raw_request_OpenRouter.py
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv


# --------------------------------------------------
# 1. Load local environment variables
# --------------------------------------------------

env_file = Path(__file__).resolve().parent / ".env"

if not env_file.is_file():
    print("Error: Local .env file not found:", env_file)
    sys.exit(1)

# Always prioritize the local .env file
load_dotenv(dotenv_path=env_file, override=True)


# --------------------------------------------------
# 2. Read configuration
# --------------------------------------------------

base_url = os.getenv("OPENROUTER_BASE_URL", "").strip().rstrip("/")
api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
model = os.getenv("OPENROUTER_MODEL", "").strip()


# --------------------------------------------------
# 3. Validate configuration
# --------------------------------------------------

if not base_url or not api_key or not model:
    print("Error: Missing environment variables.")
    sys.exit(1)


# --------------------------------------------------
# 4. Normalize API key
# --------------------------------------------------

# Remove accidental prefixes
while True:
    if api_key.lower().startswith("bearer "):
        api_key = api_key[7:].strip()
    elif api_key.lower().startswith("apikey "):
        api_key = api_key[7:].strip()
    else:
        break


# --------------------------------------------------
# 5. Build HTTP endpoint and headers
# --------------------------------------------------

url = f"{base_url}/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}


# --------------------------------------------------
# 6. Build request body
# --------------------------------------------------

body = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": "Hi!"
        }
    ],
    "max_tokens": 512
}


# --------------------------------------------------
# 7. Display request information
# --------------------------------------------------

print("Environment file:", env_file)
print("POST", url)
print("Base URL:", base_url)
print(
    "API Key:",
    f"{api_key[:8]}...{api_key[-4:]}"
    if len(api_key) > 12 else "INVALID"
)
print("Model:", model)


# --------------------------------------------------
# 8. Send HTTP request
# --------------------------------------------------

try:
    response = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=(20, 120)
    )

    print("\nStatus code:", response.status_code)

    # Handle HTTP errors
    if response.status_code != 200:
        print("Error body:", response.text[:1000])
        sys.exit(1)

    # Parse JSON response
    data = response.json()

    # Extract assistant response
    answer = data["choices"][0]["message"]["content"]

    print("\nAnswer:", answer)
    print("Finish reason:", data["choices"][0].get("finish_reason"))
    print("Usage:", data.get("usage"))


# --------------------------------------------------
# 9. Handle exceptions
# --------------------------------------------------

except requests.exceptions.SSLError as e:
    print("SSL Error:", str(e))

except requests.exceptions.ConnectTimeout:
    print("Connection timeout: Could not establish a connection.")

except requests.exceptions.ReadTimeout:
    print("Read timeout: The server did not respond in time.")

except requests.exceptions.ConnectionError as e:
    print("Connection error:", str(e))

except requests.exceptions.RequestException as e:
    print("HTTP request error:", str(e))

except (ValueError, KeyError, IndexError) as e:
    print("Response parsing error:", str(e))
