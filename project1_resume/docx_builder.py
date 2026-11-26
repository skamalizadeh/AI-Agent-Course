"""
ساخت فایل Word رزومه فارسی/انگلیسی (اسلاید ۸-۳).

نکتهٔ اصلی فارسی در python-docx (اسلاید «ساخت Word راست‌به‌چپ»):
    ┌─ w:bidi روی پاراگراف  ┌─ w:rtl روی متن  ┌─ قلم complex script  ┌─ اندازهٔ szCs
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from resume_model import Resume

FONT_FA = "Vazirmatn"
FONT_EN = "Calibri"
ACCENT = RGBColor(0x0E, 0x74, 0x90)
MUTED = RGBColor(0x64, 0x74, 0x8B)

TITLES = {
    "fa": {
        "summary": "خلاصه",
        "education": "تحصیلات",
        "experience": "سوابق کاری",
        "projects": "پروژه‌ها",
        "skills": "مهارت‌ها",
    },
    "en": {
        "summary": "Summary",
        "education": "Education",
        "experience": "Experience",
        "projects": "Projects",
        "skills": "Skills",
    },
}


def has_persian(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06FF" for ch in text or "")


def _paragraph(doc, rtl: bool, space_after: float = 4, bidi: bool | None = None):
    """پاراگراف راست‌چین/چپ‌چین که قلم لاتین درونش (ایمیل، مهارت‌ها) بدون bidi و با تراز راست."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.space_before = Pt(0)
    if rtl:
        if bidi is None or bidi:
            # ┌─ در پاراگراف bidi تراز پیش‌فرض «شروع» یعنی راست است.
            # تراز RIGHT با تنظیم نکنید: Word آن را «پایان» یعنی چپ می‌خواند.
            p._p.get_or_add_pPr().append(OxmlElement("w:bidi"))
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT    # خط فقط‌لاتین در رزومهٔ فارسی
    return p


def _run(p, text: str, rtl: bool, size: float = 11, bold: bool = False, color=None):
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = FONT_FA if rtl else FONT_EN
    if color is not None:
        run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    fonts = rPr.get_or_add_rFonts()
    fonts.set(qn("w:cs"), FONT_FA)                                # ┌─
    if rtl:
        rPr.append(OxmlElement("w:rtl"))                          # ┌─
        if bold:
            rPr.append(OxmlElement("w:bCs"))
    size_cs = OxmlElement("w:szCs")                               # ┌─
    size_cs.set(qn("w:val"), str(int(size * 2)))
    rPr.append(size_cs)
    return run


def _heading(doc, text: str, rtl: bool):
    p = _paragraph(doc, rtl, space_after=2)
    p.paragraph_format.space_before = Pt(10)
    _run(p, text, rtl, size=13, bold=True, color=ACCENT)
    # خط زیر عنوان بخش
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", "CBD5E1")):
        bottom.set(qn(k), v)
    pBdr.append(bottom)
    p._p.get_or_add_pPr().append(pBdr)


def build_docx(resume: Resume, path: Path, language: str | None = None) -> Path:
    """رزومه را در قالب فارسی یا انگلیسی می‌سازد و مسیر فایل را برمی‌گرداند."""
    lang = language or resume.language
    rtl = lang == "fa"
    t = TITLES[lang]
    doc = Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Cm(1.8)
        section.left_margin = section.right_margin = Cm(2.0)

    # سربرگ: نام و اطلاعات تماس
    p = _paragraph(doc, rtl, space_after=2)
    _run(p, resume.full_name or "", rtl, size=22, bold=True)
    contact = "  |  ".join(x for x in (resume.email, resume.phone) if x)
    if contact:
        p = _paragraph(doc, rtl, space_after=6, bidi=has_persian(contact))
        _run(p, contact, rtl and has_persian(contact), size=10, color=MUTED)

    if resume.summary:
        _heading(doc, t["summary"], rtl)
        _run(_paragraph(doc, rtl), resume.summary, rtl)

    if resume.education:
        _heading(doc, t["education"], rtl)
        for e in resume.education:
            p = _paragraph(doc, rtl, space_after=2)
            _run(p, f"{e.degree} {e.field}".strip(), rtl, bold=True)
            p = _paragraph(doc, rtl)
            tail = f"، {e.year}" if rtl and e.year else f", {e.year}" if e.year else ""
            _run(p, e.university + tail, rtl, size=10, color=MUTED)

    if resume.experience:
        _heading(doc, t["experience"], rtl)
        for x in resume.experience:
            p = _paragraph(doc, rtl, space_after=1)
            _run(p, x.title, rtl, bold=True)
            _run(p, ("، " if rtl else ", ") + x.company, rtl)
            p = _paragraph(doc, rtl, space_after=2)
            _run(p, x.period, rtl, size=10, color=MUTED)
            if x.description:
                p = _paragraph(doc, rtl)
                _run(p, "• " + x.description, rtl, size=10.5)

    if resume.projects:
        _heading(doc, t["projects"], rtl)
        for pr in resume.projects:
            p = _paragraph(doc, rtl, space_after=1)
            _run(p, pr.name, rtl, bold=True)
            if pr.technologies:
                tech = ", ".join(pr.technologies)
                _run(p, " — " + tech, rtl and has_persian(tech), size=10, color=MUTED)
            if pr.description:
                p = _paragraph(doc, rtl)
                _run(p, "• " + pr.description, rtl, size=10.5)

    if resume.skills:
        _heading(doc, t["skills"], rtl)
        skills = "  •  ".join(resume.skills)
        _run(_paragraph(doc, rtl, bidi=has_persian(skills)), skills, rtl and has_persian(skills))

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    return path


if __name__ == "__main__":
    import json
    import sys
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "output" / "resume.json"
    r = Resume.model_validate(json.loads(src.read_text(encoding="utf-8")))
    out = build_docx(r, src.parent / f"resume_{r.language}.docx")
    print("Saved:", out)
