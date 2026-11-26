"""
پارامترهای مهم فراخوانی: دما (temperature) و سقف توکن خروجی (اسلاید ۳-۵).

یک پرسش خلاقانه را سه بار با دمای پایین و سه بار با دمای بالا می‌فرستد تا تفاوت را ببینیم.
"""

from llm import LLM

llm = LLM()
PROMPT = "Suggest a name for a startup that builds AI agents. Reply with the name only."

for temperature in (0.0, 1.2):
    print(f"\n--- temperature = {temperature} ---")
    for i in range(3):
        r = llm.chat(
            [{"role": "user", "content": PROMPT}],
            temperature=temperature,
            max_tokens=20,
        )
        name = (r.choices[0].message.content or "").strip()
        print(f"  run {i + 1}: {name}   (tokens: {r.usage.total_tokens if r.usage else '?'})")
