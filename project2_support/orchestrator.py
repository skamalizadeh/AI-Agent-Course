"""
هماهنگ‌ساز: کنار هم گذاشتن قطعه‌ها — اسلاید «هماهنگ‌ساز».

    ① مسیریابی  ② بررسی ارجاع  ③ پاسخ متخصص  ④ ثبت گزارش
هر خطا به ارجاع امن به انسان ختم می‌شود، نه به پاسخ اشتباه.
"""

import json
from dataclasses import dataclass

from escalation import needs_human
from llm import LLM
from router import Route, route
from specialists import SPECIALISTS
from state_store import LOGS, now
from tools import create_ticket


@dataclass
class Reply:
    agent: str
    text: str


def log_turn(message: str, r: Route, answer: str, escalated: str | None = None) -> None:
    LOGS.mkdir(exist_ok=True)
    record = {"time": now(), "message": message, "route": r.model_dump(),
              "escalated": escalated, "answer": answer}
    with open(LOGS / "turns.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


class SupportSystem:
    def __init__(self, llm: LLM | None = None):
        self.llm = llm or LLM()
        self.history: list = []

    def handle(self, message: str) -> Reply:
        try:
            r = route(message, self.llm, self.history)                  # ①
        except Exception:
            r = Route(agent="human", confidence=0, reason="invalid router output")
        reason = needs_human(message, r)                                # ②
        if reason:
            ticket = create_ticket(message, reason)
            text = (f"درخواست شما با شمارهٔ تیکت {ticket} برای کارشناس ارسال شد. "
                    "به‌زودی با شما تماس می‌گیریم.")
            self.history += [{"role": "user", "content": message}, {"role": "assistant", "content": text}]
            log_turn(message, r, text, escalated=reason)
            return Reply("human", text)
        agent = SPECIALISTS[r.agent]                                    # ③
        self.history.append({"role": "user", "content": message})
        answer = agent.answer(self.llm, self.history)
        self.history.append({"role": "assistant", "content": answer})
        log_turn(message, r, answer)                                    # ④
        return Reply(r.agent, answer)
