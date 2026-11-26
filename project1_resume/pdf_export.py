"""
تبدیل Word به PDF با دو راه — فصل ۸-۴.

    ① کتابخانهٔ docx2pdf (ویندوز و مک، با Microsoft Word نصب‌شده)
    ② LibreOffice در حالت بی‌سر (همهٔ سیستم‌عامل‌ها)
اگر هیچ‌کدام در دسترس نبود، None برمی‌گرداند و فقط فایل Word می‌ماند.
"""

import shutil
import subprocess
import sys
from pathlib import Path

WINDOWS_SOFFICE = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]
MAC_SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


def find_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in WINDOWS_SOFFICE + [MAC_SOFFICE]:
        if Path(candidate).exists():
            return candidate
    return None


def to_pdf(docx_path: Path) -> Path | None:
    docx_path = Path(docx_path)
    pdf_path = docx_path.with_suffix(".pdf")
    if sys.platform in ("win32", "darwin"):
        try:
            from docx2pdf import convert                      # ①
            convert(str(docx_path), str(pdf_path))
            if pdf_path.exists():
                return pdf_path
        except Exception as e:
            print(f"  [pdf] docx2pdf failed: {type(e).__name__}; trying LibreOffice")
    soffice = find_soffice()                                  # ②
    if not soffice:
        print("  [pdf] No Word or LibreOffice found; only the .docx file was created.")
        return None
    try:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                        "--outdir", str(docx_path.parent), str(docx_path)],
                       check=True, timeout=120, capture_output=True)
    except Exception as e:
        print(f"  [pdf] LibreOffice failed: {type(e).__name__}")
        return None
    return pdf_path if pdf_path.exists() else None


if __name__ == "__main__":
    target = Path(sys.argv[1])
    print("PDF:", to_pdf(target))
