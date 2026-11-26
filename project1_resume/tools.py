"""
ابزارهای عامل رزومه‌ساز.

بخش اول (اسلاید ۶-۳):
    update_resume   → دادهٔ تازه را با رزومهٔ فعلی ادغام و اعتبارسنجی می‌کند
    missing_fields  → فیلدهای ضروری خالی را برمی‌گرداند
    show_resume     → رزومهٔ فعلی را به شکل JSON برمی‌گرداند
بخش دوم (فصل ۸):
    improve_text    → بهبود متن خلاصه یا یک سابقهٔ کاری با الگوی بازتاب
    build_resume    → ساخت فایل‌های Word و PDF فارسی و/یا انگلیسی

هر کاربر یک شیء ResumeTools دارد تا در رابط وب رزومهٔ کاربران قاطی نشود.
"""

import json
import re
from pathlib import Path

from pydantic import ValidationError

from resume_model import Resume, missing_required

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[+]?[\d\s().-]{7,20}$")


def _merge(current: dict, new: dict) -> dict:
    """ادغام دادهٔ تازه: مقادیر ساده جایگزین می‌شوند؛ فهرست‌ها بدون تکرار اضافه می‌شوند."""
    merged = dict(current)
    for key, value in new.items():
        if key not in merged or value in (None, "", [], {}):
            continue
        if key == "skills":
            seen = {s.lower() for s in merged["skills"]}
            for s in value:
                if isinstance(s, str) and s.strip() and s.strip().lower() not in seen:
                    merged["skills"].append(s.strip())
                    seen.add(s.strip().lower())
        elif key in ("education", "experience", "projects"):
            for item in value:
                if item not in merged[key]:
                    merged[key].append(item)
        else:
            merged[key] = value
    return merged


def _validate_contact(data: dict) -> list[str]:
    warnings = []
    email = data.get("email")
    phone = data.get("phone")
    if email and not EMAIL_RE.match(email):
        warnings.append(f"email format looks unusual: {email}")
    if phone and not PHONE_RE.match(str(phone)):
        warnings.append(f"phone format looks unusual: {phone}")
    return warnings


class ResumeTools:
    """وضعیت رزومهٔ یک کاربر و ابزارهایی که روی آن کار می‌کنند."""

    def __init__(self, llm=None, out_dir: Path = OUTPUT_DIR):
        self.resume = Resume()
        self.llm = llm                      # فقط برای improve_text و ترجمه لازم است
        self.out_dir = Path(out_dir)
        self.files: list[str] = []

    # ---------- ابزارهای بخش اول ----------
    def update_resume(self, **data) -> str:
        """Merge new information into the resume and validate it."""
        unknown = [k for k in data if k not in Resume.model_fields]
        data = {k: v for k, v in data.items() if k in Resume.model_fields}
        warnings = _validate_contact(data)
        try:
            updated = Resume.model_validate(_merge(self.resume.model_dump(), data))
        except ValidationError as e:
            problems = "; ".join(f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors())
            return f"Error: invalid data, nothing saved. {problems}"
        for field in Resume.model_fields:      # به‌روزرسانی همان شیء resume
            setattr(self.resume, field, getattr(updated, field))
        missing = missing_required(self.resume)
        note = f" Ignored unknown fields: {unknown}." if unknown else ""
        warn = f" Warnings: {'; '.join(warnings)}." if warnings else ""
        status = f"Missing required fields: {missing}" if missing else "All required fields are filled."
        return f"Saved.{note}{warn} {status}"

    def missing_fields(self) -> str:
        """List required fields that are still empty."""
        return json.dumps(missing_required(self.resume), ensure_ascii=False)

    def show_resume(self) -> str:
        """Return the current resume data as JSON."""
        return self.resume.model_dump_json(indent=2)

    # ---------- ابزارهای بخش دوم ----------
    def improve_text(self, target: str, index: int = 0) -> str:
        """Improve the summary or one experience description (Reflection pattern)."""
        if self.llm is None:
            return "Error: LLM is not configured."
        from improve import improve_text
        if target == "summary":
            if not self.resume.summary:
                return "Error: summary is empty."
            before = self.resume.summary
            self.resume.summary = improve_text(before, self.llm)
            return f"Improved summary.\nBefore: {before}\nAfter: {self.resume.summary}"
        if target == "experience":
            if not 0 <= index < len(self.resume.experience):
                return f"Error: experience index must be 0..{len(self.resume.experience) - 1}"
            item = self.resume.experience[index]
            before = item.description or f"{item.title} at {item.company}"
            item.description = improve_text(before, self.llm)
            return f"Improved experience {index}.\nBefore: {before}\nAfter: {item.description}"
        return "Error: target must be 'summary' or 'experience'."

    def _translated(self, language: str) -> Resume:
        """نسخهٔ ترجمه‌شدهٔ رزومه؛ نام‌ها نویسه‌نویسی، ایمیل و تلفن بدون تغییر."""
        if language == self.resume.language:
            return self.resume
        if self.llm is None:
            raise RuntimeError("LLM is not configured for translation.")
        target = "English" if language == "en" else "Persian (Farsi)"
        r = self.llm.chat([
            {"role": "system", "content": (
                f"Translate every text value of this resume JSON into {target}. "
                "Transliterate person names; keep emails, phone numbers, years, URLs, and technology names unchanged when appropriate; "
                "do not add or remove information. Return only the JSON with the same keys.")},
            {"role": "user", "content": self.resume.model_dump_json()},
        ], response_format={"type": "json_object"}, temperature=0)
        data = json.loads(r.choices[0].message.content)
        data["language"] = language
        return Resume.model_validate(data)

    def build_resume(self, languages: list[str] | None = None) -> str:
        """Build Word and PDF files for the requested languages."""
        from docx_builder import build_docx
        from pdf_export import to_pdf
        missing = missing_required(self.resume)
        if missing:
            return f"Error: cannot build yet. Missing required fields: {missing}"
        languages = [l for l in (languages or [self.resume.language]) if l in ("fa", "en")]
        if not languages:
            return "Error: languages must contain 'fa' and/or 'en'."
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "resume.json").write_text(self.resume.model_dump_json(indent=2), encoding="utf-8")
        made = []
        for lang in languages:
            try:
                data = self._translated(lang)
            except Exception as e:
                made.append(f"{lang}: translation failed ({type(e).__name__}: {e})")
                continue
            try:
                docx_path = build_docx(data, self.out_dir / f"resume_{lang}.docx", lang)
            except Exception as e:
                made.append(f"{lang}: docx build failed ({type(e).__name__}: {e})")
                continue
            pdf_path = None
            try:
                pdf_path = to_pdf(docx_path)
            except Exception as e:
                made.append(f"{lang}: {docx_path.name} (PDF failed: {type(e).__name__})")
                for p in [docx_path]:
                    if str(p) not in self.files:
                        self.files.append(str(p))
                continue
            for p in (docx_path, pdf_path):
                if p and str(p) not in self.files:
                    self.files.append(str(p))
            made.append(f"{lang}: {docx_path.name}" + (f", {pdf_path.name}" if pdf_path else " (PDF not available)"))
        return "Files built: " + "; ".join(made)

    def funcs(self) -> dict:
        return {"update_resume": self.update_resume, "missing_fields": self.missing_fields,
                "show_resume": self.show_resume, "improve_text": self.improve_text,
                "build_resume": self.build_resume}


# ================= شرح‌وارهٔ ابزارها =================
_EDU = {
    "type": "object",
    "properties": {
        "degree": {"type": "string", "description": "e.g. BSc, MSc, کارشناسی"},
        "field": {"type": "string"},
        "university": {"type": "string"},
        "year": {"type": "string"},
    },
    "required": ["degree", "field", "university"],
}
_EXP = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "company": {"type": "string"},
        "period": {"type": "string", "description": "e.g. 2024-2025 or 6 months"},
        "description": {"type": "string"},
    },
    "required": ["title", "company", "period"],
}
_PROJ = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "technologies": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name"],
}

TOOLS_SESSION1 = [
    {"type": "function", "function": {
        "name": "update_resume",
        "description": ("Save information the user gave into the resume. "
                        "Send only the fields that are new. Lists are appended."),
        "parameters": {"type": "object", "properties": {
            "language": {"type": "string", "enum": ["fa", "en"]},
            "full_name": {"type": "string"}, "email": {"type": "string"},
            "phone": {"type": "string"}, "summary": {"type": "string"},
            "education": {"type": "array", "items": _EDU},
            "experience": {"type": "array", "items": _EXP},
            "projects": {"type": "array", "items": _PROJ},
            "skills": {"type": "array", "items": {"type": "string"}},
        }}}},
    {"type": "function", "function": {
        "name": "missing_fields",
        "description": "List the required resume fields that are still empty.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "show_resume",
        "description": "Show the current resume data as JSON.",
        "parameters": {"type": "object", "properties": {}}}},
]

TOOLS_SESSION2 = [
    {"type": "function", "function": {
        "name": "improve_text",
        "description": ("Make the summary or one experience description more professional "
                        "without adding facts. Use it for vague texts before building."),
        "parameters": {"type": "object", "properties": {
            "target": {"type": "string", "enum": ["summary", "experience"]},
            "index": {"type": "integer", "description": "experience index, starting at 0"},
        }, "required": ["target"]}}},
    {"type": "function", "function": {
        "name": "build_resume",
        "description": ("Build the final Word and PDF files. Call only after all required "
                        "fields are filled and the user chose the language(s)."),
        "parameters": {"type": "object", "properties": {
            "languages": {"type": "array", "items": {"type": "string", "enum": ["fa", "en"]}},
        }, "required": ["languages"]}}},
]

TOOLS = TOOLS_SESSION1 + TOOLS_SESSION2

# نمونهٔ پیش‌فرضی برای سازگاری با کد بخش اول (from tools import TOOLS, FUNCS, resume)
_default = ResumeTools()
resume = _default.resume
FUNCS = _default.funcs()
