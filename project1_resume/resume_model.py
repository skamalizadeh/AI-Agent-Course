"""
مدل دادهٔ رزومه با Pydantic (اسلاید ۶-۲).

    ┌─ زبان رزومه  ┌─ فیلدهای اختیاری که کم‌کم پر می‌شوند  ┌─ فهرست‌های تودرتو
فیلدهای ضروری: نام، ایمیل، دست‌کم یک سابقهٔ تحصیلی و سه مهارت.
"""

from typing import Literal

from pydantic import BaseModel


class Education(BaseModel):
    degree: str
    field: str
    university: str
    year: str | None = None


class Experience(BaseModel):
    title: str
    company: str
    period: str
    description: str = ""


class Project(BaseModel):
    name: str
    description: str = ""
    technologies: list[str] = []


class Resume(BaseModel):
    language: Literal["fa", "en"] = "fa"   # ┌─
    full_name: str | None = None            # ┌─
    email: str | None = None
    phone: str | None = None
    summary: str | None = None
    education: list[Education] = []        # ┌─
    experience: list[Experience] = []
    projects: list[Project] = []
    skills: list[str] = []


MIN_SKILLS = 3


def missing_required(resume: Resume) -> list[str]:
    """فهرست فیلدهای ضروری که هنوز پر نشده‌اند."""
    missing = []
    if not resume.full_name:
        missing.append("full_name")
    if not resume.email:
        missing.append("email")
    if not resume.education:
        missing.append("education (at least one)")
    if len(resume.skills) < MIN_SKILLS:
        missing.append(f"skills (at least {MIN_SKILLS}, now {len(resume.skills)})")
    return missing
