"""
عامل مسیریاب: تصمیم ساختاریافته — اسلاید «عامل مسیریاب».

    ① مسیرهای مجاز  ② میزان اطمینان  ③ دمای صفر  ④ اعتبارسنجی
"""

from typing import Literal

from pydantic import BaseModel, Field

from llm import LLM


class Route(BaseModel):
    agent: Literal["technical", "billing",
                   "orders", "human"]          # ①
    confidence: float = Field(ge=0, le=1)      # ②
    reason: str


ROUTER_PROMPT = """Classify the customer message.
technical: errors, app problems, setup, how-to.
billing: invoices, payments, charges, refunds.
orders: order status, shipping, delivery.
human: angry customer, legal threat, or other topics.
Use the recent conversation only to understand short follow-ups.
Return JSON: agent, confidence (0-1), reason."""


def route(message: str, llm: LLM, history: list | None = None) -> Route:
    context = ""
    if history:
        last = [f"{m['role']}: {m['content']}" for m in history[-4:] if m.get("content")]
        context = "Recent conversation:\n" + "\n".join(last) + "\n\n"
    r = llm.chat([{"role": "system", "content": ROUTER_PROMPT},
                  {"role": "user", "content": context + "Customer message: " + message}],
                 response_format={"type": "json_object"},
                 temperature=0)                # ③
    return Route.model_validate_json(           # ④
        r.choices[0].message.content)
