"""
بهبود متن با الگوی بازتاب (Reflection) — اسلاید «الگوی بازتاب در کد».

    ① سقف دور  ② منتقد  ③ شرط توقف  ④ نویسنده
منتقد و نویسنده دو فراخوانی جدا با دو پرامپت متفاوت‌اند.
"""

from llm import LLM

CRITIC = ("You review resume bullet points. List at most 3 issues: "
          "vague, no action verb, no result. If it is good, "
          "reply only NO_ISSUES.")
WRITER = ("Rewrite the resume bullet to fix the issues. Keep every "
          "fact; never add facts. Same language. One sentence. "
          "Reply with the rewritten bullet only.")


def improve_text(text: str, llm: LLM, rounds: int = 2, verbose: bool = False) -> str:
    draft = text
    for i in range(rounds):                                  # ①
        critique = llm.ask(draft, system=CRITIC, temperature=0)   # ②
        if verbose:
            print(f"  [critic {i + 1}] {critique[:120]}")
        if "NO_ISSUES" in critique:                          # ③
            break
        draft = llm.ask(                                     # ④
            f"Bullet: {draft}\nIssues: {critique}",
            system=WRITER, temperature=0.3)
        if verbose:
            print(f"  [writer {i + 1}] {draft[:120]}")
    return draft.strip()


if __name__ == "__main__":
    sample = "شش ماه در یک شرکت کارآموز بودم و کارهای بک‌اند انجام می‌دادم."
    print("Before:", sample)
    print("After :", improve_text(sample, LLM(), verbose=True))
