"""
پاسخ کارگاه ۲: عامل با ابزارهای days_between و save_text (چالش).

اجرا از پوشهٔ part1:
    python ../solutions/tool_agent_full.py
"""

import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "part1"))

from tool_agent import FUNCS, TOOLS, main  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def days_between(start: str, end: str) -> str:
    """Number of days from start to end (dates in YYYY-MM-DD)."""
    try:
        d1, d2 = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError:
        return "Error: dates must be in YYYY-MM-DD format"
    return str((d2 - d1).days)


def save_text(filename: str, text: str) -> str:
    """Save text to a file, only inside the output folder (least privilege)."""
    name = os.path.basename(filename)          # جلوگیری از نوشتن بیرون از پوشه (مثل ../)
    if not name or not name.endswith(".txt"):
        return "Error: filename must be a simple name ending with .txt"
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / name
    path.write_text(text, encoding="utf-8")
    return f"Saved {len(text)} characters to output/{name}"


EXTRA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "days_between",
            "description": "Count the days between two dates (YYYY-MM-DD).",
            "parameters": {
                "type": "object",
                "properties": {"start": {"type": "string"}, "end": {"type": "string"}},
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_text",
            "description": "Save a text into a .txt file in the output folder.",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string", "description": "e.g. notes.txt"},
                               "text": {"type": "string"}},
                "required": ["filename", "text"],
            },
        },
    },
]

if __name__ == "__main__":
    main(tools=TOOLS + EXTRA_TOOLS,
         funcs={**FUNCS, "days_between": days_between, "save_text": save_text})
