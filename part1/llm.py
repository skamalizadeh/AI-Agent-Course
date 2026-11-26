"""
لایهٔ ارتباط با مدل زبانی: فراخوانی با تلاش دوباره.

قاعده (اسلاید «خطاهای رایج اتصال»):
    خطاهای موقت (۴۲۹، ۵۰۰ تا ۵۰۳، قطع شبکه، پایان مهلت) ← دوباره امتحان کن
    خطاهای دائمی (۴۰۰، ۴۰۱، ۴۰۴) ← فوراً گزارش کن
"""

import random
import time

import openai

from config import get_settings, make_client

RETRYABLE_ERRORS = (
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.RateLimitError,
    openai.InternalServerError,
)


class LLM:
    """کلاینت سادهٔ مدل زبانی با تلاش دوباره و عقب‌نشینی نمایی (Exponential Backoff)."""

    def __init__(self, settings=None, max_retries: int = 3, timeout: float = 60.0):
        self.settings = settings or get_settings()
        self.client = make_client(self.settings, timeout=timeout)
        self.model = self.settings.model
        self.max_retries = max_retries

    def chat(self, messages, tools=None, **kwargs):
        """یک فراخوانی chat.completions؛ پاسخ کامل API را برمی‌گرداند."""
        params = {"model": self.model, "messages": messages, **kwargs}
        if tools:
            params["tools"] = tools
        for attempt in range(self.max_retries + 1):
            try:
                return self.client.chat.completions.create(**params)
            except RETRYABLE_ERRORS as e:
                if attempt == self.max_retries:
                    raise
                # فاصلهٔ انتظار: ۱، ۲، ۴ ثانیه ... به‌علاوهٔ کمی تصادف
                wait = 2 ** attempt + random.uniform(0, 0.5)
                print(f"  [retry] {type(e).__name__}: waiting {wait:.1f}s "
                      f"(attempt {attempt + 1}/{self.max_retries})")
                time.sleep(wait)

    def ask(self, prompt: str, system: str | None = None, **kwargs) -> str:
        """پرسش تک‌نوبتی ساده؛ فقط متن پاسخ را برمی‌گرداند."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.chat(messages, **kwargs)
        return response.choices[0].message.content or ""


if __name__ == "__main__":
    llm = LLM()
    print(f"Provider: {llm.settings.name} | Model: {llm.model}")
    print(llm.ask("Say hello in one short sentence."))
