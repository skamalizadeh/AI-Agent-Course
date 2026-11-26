"""
عامل ماشین‌حساب و تاریخ: اولین عامل با فراخوانی ابزار و حلقهٔ ReAct (فصل ۵).

اجزای اسلاید «حلقهٔ عامل در کد»:
    ① سقف گام  ② شرط توقف  ③ اجرای ابزار  ④ بازگرداندن نتیجه

کارگاه ۲:
    ۱. برنامه را اجرا کنید و دو پرسش نمونه را بپرسید.
    ۲. ابزار days_between را خودتان بنویسید (پاسخ: solutions/tool_agent_full.py).
    ۳. توضیح (description) یک ابزار را خالی کنید و ببینید مدل هنوز آن را صدا می‌زند یا نه.
"""

import json
from datetime import date

from llm import LLM


# ================= ابزارها: توابع معمولی Python =================
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression."""
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Error: invalid characters"
    if "**" in expression or len(expression) > 100:
        return "Error: expression not allowed"
    try:
        # eval فقط پس از محدود کردن نویسه‌ها و بدون دسترسی به توابع داخلی
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"


def get_today() -> str:
    """Return today's date in ISO format (YYYY-MM-DD)."""
    return date.today().isoformat()


# ================= طرح‌وارهٔ ابزارها: آنچه مدل می‌بیند =================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate an arithmetic expression. Use it for any math.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string",
                                              "description": "e.g. 4789*6213"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_today",
            "description": "Get today's date. Use it whenever the current date matters.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

FUNCS = {"calculator": calculator, "get_today": get_today}

SYSTEM = ("You are a helpful assistant. Use the tools for math and dates; "
          "never guess numbers or dates. Answer briefly.")


# ================= حلقهٔ عامل =================
def run_agent(llm: LLM, messages: list, tools=TOOLS, funcs=FUNCS, max_steps: int = 8) -> str:
    for step in range(1, max_steps + 1):                       # ①
        resp = llm.chat(messages, tools=tools, temperature=0)
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:                                 # ②
            return msg.content or ""
        for call in msg.tool_calls:                            # ③
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
                result = funcs[name](**args)
            except KeyError:
                result = f"Error: unknown tool '{name}'"
            except Exception as e:
                result = f"Error: {e}"
            print(f"  [step {step}] tool: {name}({call.function.arguments})")
            print(f"           -> {result}")
            messages.append({"role": "tool",                   # ④
                             "tool_call_id": call.id,
                             "content": str(result)})
    return "Stopped: step limit reached."


def main(tools=TOOLS, funcs=FUNCS) -> None:
    llm = LLM()
    print(f"Tool agent | provider: {llm.settings.name} | model: {llm.model}")
    print("Type 'exit' to quit.\n")
    messages = [{"role": "system", "content": SYSTEM}]
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.lower() == "exit":
            break
        messages.append({"role": "user", "content": text})
        print("Agent:", run_agent(llm, messages, tools, funcs), "\n")


if __name__ == "__main__":
    main()
