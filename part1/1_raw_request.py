"""
زیر پوسته: همان درخواست، بدون کتابخانهٔ openai و فقط با requests (اسلاید ۳-۴).

هدف: دیدن اینکه هر کتابخانه‌ای در نهایت یک درخواست HTTP با بدنهٔ JSON می‌فرستد.
گزینهٔ --full کل پاسخ JSON را چاپ می‌کند (برای اسلاید «کالبدشکافی پاسخ مدل»).
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import find_dotenv, load_dotenv

env_file = Path(__file__).resolve().parent / ".env"

if not env_file.is_file():
    print("Error: Local .env file not found:", env_file)
    sys.exit(1)

load_dotenv(dotenv_path=env_file, override=True)

url = os.getenv("LLM_BASE_URL", "").rstrip("/") + "/chat/completions"  # ①
headers = {
    "Authorization": "Bearer " + os.getenv("LLM_API_KEY", ""),  # ②
    "Content-Type": "application/json",
}
body = {                                                       # ③
    "model": os.getenv("LLM_MODEL"),
    "messages": [{"role": "user", "content": "Hi!"}],
}

print(f"POST {url}")
r = requests.post(url, headers=headers, json=body, timeout=60)
print("Status code:", r.status_code)                           # ④

if r.status_code != 200:
    print("Error body:", r.text[:500])
    sys.exit(1)

data = r.json()
if "--full" in sys.argv:
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print("Answer:", data["choices"][0]["message"]["content"])
    print("Finish reason:", data["choices"][0].get("finish_reason"))
    print("Usage:", data.get("usage"))
