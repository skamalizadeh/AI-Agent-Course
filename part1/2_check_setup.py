"""
برنامهٔ بررسی اتصال (اسلاید «برنامهٔ بررسی اتصال: check_setup.py»).

این برنامه به ترتیب بررسی می‌کند:
    ۱. نسخهٔ Python و کتابخانه‌های لازم
    ۲. وجود فایل .env
    ۳. برای ارائه‌دهندهٔ فعال و هر ارائه‌دهندهٔ پرشده در .env:
       دسترسی به سرور، وجود مدل، یک درخواست ساده و پشتیبانی از فراخوانی ابزار
برای هر خطا، علت محتمل و راه‌حل را چاپ می‌کند.

اجرا:
    python check_setup.py            # آزمون کامل
    python check_setup.py --quick    # بدون آزمون فراخوانی ابزار
"""

import importlib
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OK, FAIL, WARN = "✓", "✗", "!"
WIDTH = 30


def line(label: str, status: str, extra: str = "", indent: int = 0) -> None:
    dots = "." * max(2, WIDTH - len(label) - indent)
    print(f"{' ' * indent}{label} {dots} {status}  {extra}".rstrip())


# ---------- ۱. محیط Python ----------
def check_python() -> bool:
    v = sys.version_info
    ok = v >= (3, 10)
    line(f"Python {v.major}.{v.minor}.{v.micro}", OK if ok else FAIL,
         "" if ok else "Python 3.10 or newer is required")
    return ok


def check_packages() -> bool:
    all_ok = True
    for pkg, module in [("openai", "openai"), ("python-dotenv", "dotenv"),
                        ("pydantic", "pydantic"), ("requests", "requests")]:
        try:
            importlib.import_module(module)
            line(f"Package {pkg}", OK)
        except ImportError:
            line(f"Package {pkg}", FAIL, "run: pip install -r requirements.txt")
            all_ok = False
    return all_ok


# ---------- ۲. راهنمای خطاها ----------
HINTS = {
    401: "check the API key in .env (copy it again, no extra spaces)",
    403: "access denied; the key may lack permission or the region may be blocked",
    404: "check the base URL (it usually ends with /v1) and the exact model name",
    429: "rate limit reached; wait a few seconds or use your own key",
    500: "temporary server error; try again",
    502: "temporary server error; try again",
    503: "server is busy or the model is loading; try again",
}


def explain(err) -> str:
    import openai
    if isinstance(err, openai.APIConnectionError):
        return "cannot reach server (Ollama not running? internet or proxy?)"
    if isinstance(err, openai.APITimeoutError):
        return "timeout; increase timeout or choose a smaller model"
    code = getattr(err, "status_code", None)
    if code:
        return f"{code} {HINTS.get(code, str(err)[:80])}"
    return str(err)[:100]


# ---------- ۳. آزمون یک ارائه‌دهنده ----------
TOOL_TEST = [{
    "type": "function",
    "function": {
        "name": "add_numbers",
        "description": "Add two integers and return the sum.",
        "parameters": {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    },
}]


def check_provider(settings, quick: bool = False) -> bool:
    from config import make_client

    print()
    print(f"Provider: {settings.name}")
    if not settings.is_complete:
        line("Settings complete", FAIL, "fill BASE_URL, API_KEY and MODEL in .env", indent=2)
        return False

    client = make_client(settings, timeout=120)

    # ۳-الف. دسترسی به سرور و فهرست مدل‌ها
    try:
        models = [m.id for m in client.models.list().data]
        line("Server reachable", OK, indent=2)
        if models and settings.model not in models:
            line(f"Model {settings.model}", WARN,
                 "not in model list; check the exact name", indent=2)
        else:
            line(f"Model {settings.model}", OK, indent=2)
    except Exception as e:
        # بعضی ارائه‌دهنده‌ها فهرست مدل ندارند؛ آزمون اصلی درخواست ساده است.
        line("Model list", WARN, explain(e), indent=2)

    # ۳-ب. درخواست ساده
    try:
        t0 = time.time()
        r = client.chat.completions.create(
            model=settings.model,
            messages=[{"role": "user", "content": "Reply with the single word: pong"}],
            max_tokens=10,
        )
        dt = time.time() - t0
        text = (r.choices[0].message.content or "").strip()
        line("Chat request", OK, f"({dt:.1f} s) reply: {text[:30]!r}", indent=2)
    except Exception as e:
        line("Chat request", FAIL, explain(e), indent=2)
        return False

    if quick:
        return True

    # ۳-ج. فراخوانی ابزار
    try:
        r = client.chat.completions.create(
            model=settings.model,
            messages=[{"role": "user", "content": "Use the tool to add 17 and 25."}],
            tools=TOOL_TEST,
        )
        calls = r.choices[0].message.tool_calls
        if calls and calls[0].function.name == "add_numbers":
            line("Tool calling", OK, indent=2)
        else:
            line("Tool calling", WARN,
                 "model answered without a tool; it may not support tools well", indent=2)
    except Exception as e:
        line("Tool calling", FAIL, explain(e) + " (model may not support tools)", indent=2)
    return True


def main() -> None:
    quick = "--quick" in sys.argv
    env_ok = True
    py_ok = check_python()
    pkg_ok = check_packages()
    if not pkg_ok:
        print("\nInstall the missing packages first, then run this script again.")
        sys.exit(1)

    from config import ENV_PATH, PROVIDER_PREFIXES, get_settings
    if ENV_PATH:
        line(".env file found", OK)
    else:
        line(".env file found", FAIL, "copy .env.example to .env and fill it")
        env_ok = False

    # ارائه‌دهندهٔ فعال، سپس ارائه‌دهنده‌های اضافی پرشده که با فعال یکی نیستند
    active = get_settings("LLM")
    to_test = [active]
    for key, prefix in PROVIDER_PREFIXES.items():
        if key == "active":
            continue
        s = get_settings(prefix)
        same = (s.base_url, s.model) == (active.base_url, active.model)
        if s.is_complete and not same:
            to_test.append(s)

    results = [check_provider(s, quick) for s in to_test]

    print()
    if py_ok and env_ok and results and results[0]:
        print("Ready! The active provider works. You can run hello_llm.py now.")
    else:
        print("Not ready yet. Fix the lines marked with ✗ (see the hints above).")


if __name__ == "__main__":
    main()
