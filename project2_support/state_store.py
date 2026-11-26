"""
ذخیره‌سازی ساده در فایل JSON برای صف بازپرداخت و تیکت‌ها.
پوشهٔ state هنگام اجرا ساخته می‌شود و در GitHub قرار نمی‌گیرد.
"""

import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
STATE = BASE / "state"
LOGS = BASE / "logs"


def read_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")
