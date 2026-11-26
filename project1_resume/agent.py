"""
عامل رزومه‌ساز: هستهٔ عامل (بخش اول) + ابزارهای بخش دوم.

دو حلقه:
    حلقهٔ بیرونی (main یا رابط وب)  ← گفت‌وگو با کاربر، نوبت به نوبت
    حلقهٔ درونی (run_agent)         ← در هر نوبت ممکن است چند ابزار را پشت سر هم صدا بزند

کلاس ResumeAgent همان حلقه را برای هر کاربر جدا نگه می‌دارد (برای رابط وب app.py).

اجرا در ترمینال:
    python agent.py
    python agent.py --quiet   # بدون چاپ خطوط [tool]
"""

import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from llm import LLM
from prompts import SYSTEM_PROMPT
from tools import TOOLS, ResumeTools

VERBOSE = "--quiet" not in sys.argv


def run_agent(llm: LLM, messages: list, tools: list, funcs: dict, max_steps: int = 12) -> str:
    """حلقهٔ ReAct: همان حلقهٔ فصل ۵-۴."""
    for _ in range(max_steps):
        resp = llm.chat(messages, tools=tools, temperature=0.2)
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return msg.content or ""
        for call in msg.tool_calls:
            name = call.function.name
            args = {}
            try:
                args = json.loads(call.function.arguments or "{}")
                result = funcs[name](**args)
            except KeyError:
                result = f"Error: unknown tool '{name}'"
            except Exception as e:
                result = f"Error: {e}"
            if VERBOSE:
                fields = ", ".join(args) if isinstance(args, dict) else ""
                print(f"  [tool] {name}({fields}) -> {str(result)[:80]}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})
    return "Stopped: step limit reached."


class ResumeAgent:
    """یک عامل رزومه‌ساز با حافظهٔ گفت‌وگو و رزومهٔ مخصوص خودش."""

    def __init__(self, llm: LLM | None = None):
        self.llm = llm or LLM()
        self.tools = ResumeTools(self.llm)
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    @property
    def resume(self):
        return self.tools.resume

    @property
    def files(self) -> list[str]:
        return self.tools.files

    def step(self, text: str) -> str:
        """یک نوبت گفت‌وگو: پیام کاربر ← حلقهٔ عامل ← پاسخ."""
        self.messages.append({"role": "user", "content": text})
        return run_agent(self.llm, self.messages, TOOLS, self.tools.funcs())


def main() -> None:
    agent = ResumeAgent()
    print(f"Resume Agent | provider: {agent.llm.settings.name} | model: {agent.llm.model}")
    print("Resume Agent (type 'exit' to quit)")
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.lower() == "exit":
            break
        answer = agent.step(text)
        print("Agent:", answer)
        if "DONE" in answer:
            print(agent.resume.model_dump_json(indent=2))
            for f in agent.files:
                print("File:", f)
            break


if __name__ == "__main__":
    main()
