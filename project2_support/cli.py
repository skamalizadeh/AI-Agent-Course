"""
سیستم پشتیبانی در ترمینال.

اجرا:
    python cli.py
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from orchestrator import SupportSystem


def main() -> None:
    system = SupportSystem()
    print(f"Support system | provider: {system.llm.settings.name} | model: {system.llm.model}")
    print("Type 'exit' to quit.\n")
    while True:
        try:
            text = input("Customer: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.lower() == "exit":
            break
        reply = system.handle(text)
        print(f"[{reply.agent}] {reply.text}\n")


if __name__ == "__main__":
    main()
