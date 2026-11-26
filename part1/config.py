"""
تنظیمات اتصال به مدل زبانی.

همهٔ برنامه‌های دوره، نشانی پایه، کلید و نام مدل را از فایل .env در ریشهٔ مخزن می‌خوانند.
با عوض کردن همین سه مقدار، کد بدون تغییر به Ollama، OpenRouter یا آروان‌کلاد وصل می‌شود.

اجرای مستقیم این فایل، تنظیمات فعال را (بدون نمایش کامل کلید) چاپ می‌کند:
    python config.py
"""

import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

# فایل .env را از پوشهٔ جاری یا پوشه‌های بالاتر پیدا و بارگذاری می‌کند.
ENV_PATH = find_dotenv(usecwd=True) or find_dotenv()
load_dotenv(ENV_PATH)

# پیشوندهای شناخته‌شده در فایل .env
PROVIDER_PREFIXES = {
    "active": "LLM",
    "ollama": "OLLAMA",
    "openrouter": "OPENROUTER",
    "arvan": "ARVAN",
}


@dataclass
class Settings:
    """سه مقدار لازم برای هر اتصال، به‌علاوهٔ نام ارائه‌دهنده."""

    name: str
    base_url: str
    api_key: str
    model: str

    @property
    def is_complete(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)

    @property
    def masked_key(self) -> str:
        if not self.api_key:
            return "(empty)"
        if len(self.api_key) <= 8:
            return "****"
        return self.api_key[:6] + "..." + self.api_key[-4:]


def guess_provider(base_url: str) -> str:
    """نام ارائه‌دهنده را از روی نشانی پایه حدس می‌زند (فقط برای نمایش)."""
    url = (base_url or "").lower()
    if "localhost:11434" in url or "127.0.0.1:11434" in url:
        return "ollama"
    if "openrouter.ai" in url:
        return "openrouter"
    if "arvan" in url:
        return "arvan"
    return "custom"


def get_settings(prefix: str = "LLM") -> Settings:
    """مقادیر یک پیشوند (مثلاً LLM یا OPENROUTER) را از متغیرهای محیطی می‌خواند."""
    base_url = os.getenv(f"{prefix}_BASE_URL", "").strip().rstrip("/")
    api_key = os.getenv(f"{prefix}_API_KEY", "").strip()
    model = os.getenv(f"{prefix}_MODEL", "").strip()
    name = guess_provider(base_url) if prefix == "LLM" else prefix.lower()
    return Settings(name=name, base_url=base_url, api_key=api_key, model=model)


def make_client(settings: Settings | None = None, timeout: float = 60.0) -> OpenAI:
    """یک کلاینت سازگار با OpenAI برای ارائه‌دهندهٔ فعال می‌سازد."""
    s = settings or get_settings()
    if not s.is_complete:
        raise RuntimeError(
            "LLM settings are incomplete. Fill LLM_BASE_URL, LLM_API_KEY and "
            "LLM_MODEL in the .env file (see .env.example)."
        )
    # تلاش دوباره را خودمان در llm.py مدیریت می‌کنیم، پس max_retries=0
    return OpenAI(base_url=s.base_url, api_key=s.api_key, timeout=timeout, max_retries=0)


if __name__ == "__main__":
    s = get_settings()
    print(f".env file : {ENV_PATH or 'NOT FOUND'}")
    print(f"Provider  : {s.name}")
    print(f"Base URL  : {s.base_url or '(empty)'}")
    print(f"API key   : {s.masked_key}")
    print(f"Model     : {s.model or '(empty)'}")
    print("Status    :", "OK" if s.is_complete else "INCOMPLETE")
