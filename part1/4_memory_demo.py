"""
نقش پیام‌ها و بی‌حافظگی API (اسلاید ۳-۵).

API هیچ چیزی را بین دو فراخوانی به یاد نمی‌آورد. «حافظه» یعنی خودمان تاریخچه را دوباره بفرستیم.

اجرا:
    python memory_demo.py              # با تاریخچه: مدل نام را می‌داند
    python memory_demo.py --no-history # بدون تاریخچه: مدل نام را نمی‌داند
"""

import sys

from llm import LLM

llm = LLM()
KEEP_HISTORY = "--no-history" not in sys.argv

messages = [{"role": "system", "content": "Be brief."}]


def chat(text: str) -> str:
    global messages
    if not KEEP_HISTORY:
        # هر بار از صفر: فقط پیام سیستمی می‌ماند
        messages = [{"role": "system", "content": "Be brief."}]
    messages.append({"role": "user", "content": text})
    r = llm.chat(messages)
    answer = r.choices[0].message.content or ""
    messages.append({"role": "assistant", "content": answer})
    return answer


print(f"Keep history: {KEEP_HISTORY}\n")
print("You  : My name is Sara.")
print("Model:", chat("My name is Sara."))
print("You  : What is my name?")
print("Model:", chat("What is my name?"))
print(f"\nMessages sent in the last call: {len(messages) - 1}")
