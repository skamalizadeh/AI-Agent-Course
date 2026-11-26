"""
رابط وب عامل رزومه‌ساز با Gradio (فصل ۸).

    ┌─ یک عامل برای هر کاربر (gr.State)  ┌─ یک نوبت گفت‌وگو
    ┌─ خروجی‌ها: پاسخ، تاریخچه و فایل‌ها  ┌─ اجرا

اجرا:
    python app.py
سپس نشانی نمایش‌داده‌شده (معمولاً http://127.0.0.1:7860) را در مرورگر باز کنید.
"""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from agent import ResumeAgent
from resume_model import missing_required

CSS = """
.gradio-container { max-width: 1180px !important; margin: auto; }
#title-row { margin-bottom: 0.5rem; }
#status-box textarea { font-size: 0.92rem; }
footer { display: none !important; }
"""

WELCOME = (
    "سلام! من دستیار ساخت رزومه هستم. اطلاعات تحصیلی، سوابق کاری و مهارت‌هایت را "
    "بگو تا رزومه‌ات را بسازم. می‌توانی فارسی یا انگلیسی صحبت کنی."
)


def _resume_status(agent: ResumeAgent) -> str:
    r = agent.resume
    missing = missing_required(r)
    lines = ["## وضعیت رزومه", ""]
    lines.append(f"**نام:** {r.full_name or '—'}")
    lines.append(f"**ایمیل:** {r.email or '—'}")
    lines.append(f"**تلفن:** {r.phone or '—'}")
    lines.append(f"**زبان:** {r.language}")
    lines.append(f"**تحصیلات:** {len(r.education)} مورد")
    lines.append(f"**سوابق کاری:** {len(r.experience)} مورد")
    lines.append(f"**پروژه‌ها:** {len(r.projects)} مورد")
    lines.append(f"**مهارت‌ها:** {len(r.skills)} مورد")
    if r.summary:
        short = r.summary.strip().replace("\n", " ")
        lines.append(f"**خلاصه:** {short[:180]}{'...' if len(short) > 180 else ''}")
    lines.append("")
    if missing:
        lines.append("**فیلدهای ضروری باقی‌مانده:**")
        for m in missing:
            lines.append(f"- {m}")
    else:
        lines.append("**همهٔ فیلدهای ضروری پر شده‌اند.**")
    if agent.files:
        lines.append("")
        lines.append("**فایل‌های ساخته‌شده:**")
        for f in agent.files:
            lines.append(f"- {f}")
    return "\n".join(lines)


def _chat(agent: ResumeAgent) -> list[dict]:
    # فقط پیام‌های کاربر/دستیار را برای نمایش برمی‌گردانیم
    msgs = [{"role": "assistant", "content": WELCOME}]
    for m in agent.messages:
        role = m.get("role") if isinstance(m, dict) else getattr(m, "role", None)
        content = m.get("content") if isinstance(m, dict) else getattr(m, "content", None)
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            msgs.append({"role": role, "content": content})
    return msgs


def respond(message, chat, state):
    if not message or not message.strip():
        return "", chat, state, _resume_status(state or ResumeAgent()), (state.files if state else None)
    agent = state or ResumeAgent()                                  # ┌─
    try:
        answer = agent.step(message)                                # ┌─
    except Exception as e:
        answer = f"خطا در ارتباط با مدل: {type(e).__name__}. تنظیمات .env را بررسی کنید."
    display = answer.replace("DONE", "").strip() or "رزومه آماده شد."
    chat = chat + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": display},
    ]
    files = agent.files or None                                     # ┌─
    return "", chat, agent, _resume_status(agent), files


def reset_chat():
    agent = ResumeAgent()
    return _chat(agent), agent, _resume_status(agent), None, ""


def _supported_kwargs(cls, **kwargs):
    try:
        import inspect
        params = inspect.signature(cls.__init__).parameters
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
            return kwargs
        return {k: v for k, v in kwargs.items() if k in params}
    except Exception:
        return kwargs


with gr.Blocks(**_supported_kwargs(gr.Blocks, title="Resume Agent")) as demo:
    gr.Markdown("# رزومه‌ساز هوشمند\nاطلاعاتت را در چت بگو؛ عامل رزومه را کامل می‌کند و فایل Word/PDF می‌سازد.", elem_id="title-row")
    state = gr.State()

    with gr.Row():
        with gr.Column(scale=3):
            chat = gr.Chatbot(**_supported_kwargs(
                gr.Chatbot,
                label="گفت‌وگو",
                height=520,
                value=[{"role": "assistant", "content": WELCOME}],
                rtl=True,
                show_label=False,
            ))
            box = gr.Textbox(**_supported_kwargs(
                gr.Textbox,
                placeholder="پیام خود را بنویسید… (Enter برای ارسال، Shift+Enter برای خط جدید)",
                rtl=True,
                show_label=False,
                lines=3,
                elem_id="msg-box",
            ))
            with gr.Row():
                send = gr.Button("ارسال", variant="primary", elem_id="send-btn")
                clear = gr.Button("گفت‌وگوی جدید")

        with gr.Column(scale=2):
            status = gr.Markdown(_resume_status(ResumeAgent()), elem_id="status-box")
            files = gr.File(label="فایل‌های آمادهٔ دانلود", file_count="multiple")

    gr.Markdown(
        "راهنما: ابتدا نام، ایمیل، تحصیلات و مهارت‌ها را بگو. بعد از تکمیل فیلدهای ضروری، "
        "عامل متن‌ها را بهبود می‌دهد و با تأیید تو فایل Word/PDF فارسی یا انگلیسی می‌سازد."
    )

    inputs = [box, chat, state]
    outputs = [box, chat, state, status, files]
    send.click(respond, inputs, outputs, show_progress="hidden")
    clear.click(reset_chat, outputs=[chat, state, status, files, box], show_progress="hidden")
    demo.load(js="""
    () => {
      if (window.__resumeEnterSend) return;
      window.__resumeEnterSend = true;
      document.addEventListener('keydown', (e) => {
        const box = e.target.closest('#msg-box textarea');
        if (!box) return;
        if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
          e.preventDefault();
          const send = document.querySelector('#send-btn');
          if (send) send.click();
        }
        // Shift+Enter: let browser insert newline normally.
      }, true);
    }
    """)

if __name__ == "__main__":
    output_dir = str(Path(__file__).resolve().parent.parent / "output")
    launch_kwargs = _supported_kwargs(
        demo.launch,
        css=CSS,
        allowed_paths=[output_dir],
    )
    demo.launch(**launch_kwargs)
