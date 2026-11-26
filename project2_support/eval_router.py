"""
آزمون خودکار مسیریاب — اسلاید «آزمون خودکار مسیریاب».

هر بار پرامپت یا مدل را عوض کردید، این آزمون را دوباره اجرا کنید.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from llm import LLM
from router import route

TESTS = [
    ("Where is my order 1042?", "orders"),
    ("I was charged twice for INV-77", "billing"),
    ("The app crashes when I log in", "technical"),
    ("This is a scam, I will sue you!", "human"),
    ("سفارشم هنوز نرسیده", "orders"),
    ("فاکتورم را می‌خواهم", "billing"),
    ("When will order 1043 be shipped?", "orders"),
    ("Can I change the delivery address of my order?", "orders"),
    ("What is the tracking code of my package?", "orders"),
    ("بستهٔ من با کدام شرکت ارسال شده؟", "orders"),
    ("سفارش ۱۰۴۴ تحویل شد؟", "orders"),
    ("I need a refund for invoice INV-79", "billing"),
    ("My payment failed but money was taken", "billing"),
    ("Why is my invoice still pending?", "billing"),
    ("مبلغ صورت‌حساب اشتباه است", "billing"),
    ("پولم را پس بدهید", "billing"),
    ("I forgot my password", "technical"),
    ("Notifications do not show up on my phone", "technical"),
    ("How do I delete my account?", "technical"),
    ("برنامه خیلی کند است", "technical"),
    ("کد تأیید پیامک نمی‌شود", "technical"),
    ("برنامه موقع ورود بسته می‌شود", "technical"),
    ("I want to talk to your manager right now!", "human"),
    ("Do you sell gift cards for restaurants?", "human"),
    ("از دست شما به دادگاه شکایت می‌کنم", "human"),
    ("هوا فردا چطور است؟", "human"),
]


def main() -> None:
    llm = LLM()
    print(f"Router eval | provider: {llm.settings.name} | model: {llm.model}\n")
    correct = 0
    for text, expected in TESTS:
        try:
            got = route(text, llm).agent
        except Exception as e:
            got = f"error:{type(e).__name__}"
        correct += got == expected
        mark = "OK " if got == expected else "BAD"
        print(f"{mark} {expected:>9} -> {got:<9} | {text}")
    print(f"\nRouter accuracy: {correct}/{len(TESTS)}")


if __name__ == "__main__":
    main()
