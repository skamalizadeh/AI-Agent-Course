"""
جست‌وجوی معنایی در راهنمای محصول (RAG) — اسلاید «جست‌وجوی معنایی در کد».

    ① مدل تعبیه  ② قطعه‌بندی  ③ شباهت کسینوسی  ④ k نزدیک‌ترین
اگر ارائه‌دهنده مدل تعبیه نداشته باشد (یا LLM_EMBED_MODEL تنظیم نشده باشد)،
خودکار به جست‌وجوی ساده بر اساس بخش‌های مشترک کلمه‌ها (سه‌حرفی‌ها) برمی‌گردد.
"""

import os
import re
from pathlib import Path

import numpy as np

from config import make_client

KB_PATH = Path(__file__).resolve().parent / "data" / "kb.md"
EMBED_MODEL = os.getenv("LLM_EMBED_MODEL", "").strip()


def load_chunks(path: Path = KB_PATH) -> list[str]:
    """هر بخش ## یک قطعه است."""                               # ②
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"\n(?=## )", text)
    return [p.strip() for p in parts if p.strip().startswith("## ")]


def _tokens(text: str) -> set[str]:
    """سه‌حرفی‌های هر کلمه؛ «رمزم» و «رمز» یا «فراموش» و «فراموشی» اشتراک پیدا می‌کنند."""
    words = re.findall(r"[\w\u0600-\u06FF]+", text.lower())
    grams = set()
    for w in words:
        if len(w) >= 3:
            grams.update(w[j:j + 3] for j in range(len(w) - 2))
    return grams


class KnowledgeBase:
    def __init__(self, path: Path = KB_PATH):
        self.chunks = load_chunks(path)
        self.vectors = None
        self.mode = "keyword"
        if EMBED_MODEL:
            try:
                self.client = make_client()
                self.vectors = self.embed(self.chunks)
                self.mode = "embedding"
            except Exception as e:
                print(f"  [kb] embeddings unavailable ({type(e).__name__}); using keyword search")

    def embed(self, texts: list[str]) -> np.ndarray:
        r = self.client.embeddings.create(model=EMBED_MODEL, input=texts)   # ①
        return np.array([d.embedding for d in r.data])

    def search(self, query: str, k: int = 2) -> list[str]:
        if self.mode == "embedding":
            q = self.embed([query])[0]
            sims = self.vectors @ q / (                                   # ③
                np.linalg.norm(self.vectors, axis=1) * np.linalg.norm(q))
        else:
            qt = _tokens(query)
            sims = np.array([len(qt & _tokens(c)) / (len(qt) or 1) for c in self.chunks])
        best = np.argsort(sims)[::-1][:k]                                # ④
        return [self.chunks[i] for i in best if sims[i] > 0.05]


if __name__ == "__main__":
    kb = KnowledgeBase()
    print(f"Mode: {kb.mode} | chunks: {len(kb.chunks)}")
    for q in ["برنامه موقع ورود بسته می‌شود", "رمزم را فراموش کردم"]:
        print(f"\nQuery: {q}")
        for c in kb.search(q):
            print(" -", c.splitlines()[0])
