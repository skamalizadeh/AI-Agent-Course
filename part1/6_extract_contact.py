"""
خروجی ساختاریافته با Pydantic (اسلاید ۴-۵).

اطلاعات تماس را از یک متن آزاد استخراج می‌کند:
    ① قرارداد خروجی  ② درخواست JSON  ③ اعتبارسنجی  ④ مدیریت خطا و تلاش دوباره
"""

import sys

from pydantic import BaseModel, ValidationError

from llm import LLM


class Contact(BaseModel):                  # ①
    name: str
    email: str | None = None
    skills: list[str] = []


SYSTEM = ("Extract name, email and skills from the text. "
          "Return only JSON with keys: name (string), email (string or null), "
          "skills (list of strings).")

SAMPLE = ("سلام، من علی محمدی هستم. دانشجوی کارشناسی کامپیوترم و با Python، "
          "Django و Docker کار کرده‌ام. ایمیلم ali.mohammadi@example.com است.")


def extract(text: str, llm: LLM, max_attempts: int = 2) -> Contact:
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": text}]
    for attempt in range(1, max_attempts + 1):
        resp = llm.chat(
            messages,
            temperature=0,
            response_format={"type": "json_object"},   # ②
        )
        content = resp.choices[0].message.content or ""
        try:
            return Contact.model_validate_json(content)   # ③
        except ValidationError as e:                       # ④
            print(f"Invalid output (attempt {attempt}): {e.errors()[0]['msg']}")
            # خطا را به مدل برمی‌گردانیم تا خودش اصلاح کند
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user",
                             "content": f"Your JSON was invalid: {e}. Return corrected JSON only."})
    raise RuntimeError("Could not get valid JSON from the model.")


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or SAMPLE
    contact = extract(text, LLM())
    print("Name  :", contact.name)
    print("Email :", contact.email)
    print("Skills:", ", ".join(contact.skills))
    print("\nJSON:", contact.model_dump_json(indent=2))
