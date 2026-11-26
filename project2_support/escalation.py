"""
قواعد ارجاع به انسان — اسلاید «قواعد ارجاع به انسان».

    ① تصمیم مدل  ② اطمینان پایین  ③ قاعدهٔ قطعی (کلمه‌های حساس)
قاعدهٔ ④ (تأیید بازپرداخت) در tools.request_refund است.
قاعده‌های ③ و ④ با کد نوشته شده‌اند، نه با پرامپت؛ پس با تزریق پرامپت دور زده نمی‌شوند.
"""

from router import Route

ANGRY = ["شکایت", "وکیل", "کلاهبرداری", "دادگاه", "lawyer", "sue", "scam", "court"]
MIN_CONFIDENCE = 0.6


def needs_human(message: str, r: Route) -> str | None:
    if r.agent == "human":                       # ①
        return "router chose human"
    if r.confidence < MIN_CONFIDENCE:            # ②
        return f"low confidence ({r.confidence:.2f})"
    text = message.lower()
    if any(w in text for w in ANGRY):            # ③
        return "sensitive wording"
    return None
