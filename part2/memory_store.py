"""
حافظهٔ بلندمدت: یادآوری بین گفت‌وگوها — اسلاید ۷-۴.

    ① محل نگهداری  ② ذخیره  ③ بارگذاری  ④ تزریق به زمینه

اجرا (دو بار پشت سر هم):
    python memory_store.py
بار دوم، برنامه چیزهایی را که بار اول گفته‌اید به یاد می‌آورد.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "part1"))
from llm import LLM  # noqa: E402

STORE = Path(__file__).resolve().parent.parent / "output" / "memory"   # ①
SYSTEM_PROMPT = "You are a friendly study assistant. Be brief."


def load_memory(user_id: str) -> dict:
    path = STORE / f"{user_id}.json"
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return {}


def save_memory(user_id: str, data: dict):                              # ②
    STORE.mkdir(parents=True, exist_ok=True)
    (STORE / f"{user_id}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def extract_facts(llm: LLM, text: str, memory: dict) -> dict:
    """اطلاعات ماندگار کاربر را از پیامش استخراج می‌کند (نام، رشته، علاقه‌ها)."""
    r = llm.chat([
        {"role": "system", "content": (
            "Update this JSON memory with lasting facts about the user from the message "
            "(name, field of study, interests, goals). Keep old facts. Return only JSON.")},
        {"role": "user", "content": f"Memory: {json.dumps(memory, ensure_ascii=False)}\nMessage: {text}"},
    ], response_format={"type": "json_object"}, temperature=0)
    try:
        return json.loads(r.choices[0].message.content)
    except json.JSONDecodeError:
        return memory


def main() -> None:
    llm = LLM()
    user = input("User id: ").strip() or "sara"
    memory = load_memory(user)                                          # ③
    print("Loaded memory:", json.dumps(memory, ensure_ascii=False) or "{}")
    system = SYSTEM_PROMPT + "\nKnown user data: "
    system += json.dumps(memory, ensure_ascii=False)                    # ④
    messages = [{"role": "system", "content": system}]
    while True:
        text = input("You: ").strip()
        if not text or text.lower() == "exit":
            break
        messages.append({"role": "user", "content": text})
        answer = llm.chat(messages).choices[0].message.content or ""
        messages.append({"role": "assistant", "content": answer})
        print("Model:", answer)
        memory = extract_facts(llm, text, memory)
        save_memory(user, memory)
    print("Saved memory:", json.dumps(memory, ensure_ascii=False))


if __name__ == "__main__":
    main()
