"""
حلقهٔ عامل (ReAct) — همان حلقهٔ بخش اول، با ابزارها به‌عنوان ورودی.
"""

import json

from llm import LLM

VERBOSE = True


def run_agent(llm: LLM, messages: list, tools: list, funcs: dict, max_steps: int = 6) -> str:
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
                result = f"Error: tool '{name}' is not allowed for this agent"
            except Exception as e:
                result = f"Error: {e}"
            if VERBOSE:
                print(f"    [tool] {name}({call.function.arguments}) -> {str(result)[:70]}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": str(result)})
    return "Stopped: step limit reached."
