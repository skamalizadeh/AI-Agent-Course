"""
رابط چت وب سیستم پشتیبانی — همان رابط پروژهٔ ۱، با برچسب متخصص پاسخ‌دهنده.

اجرا:
    python app.py
"""

import gradio as gr

from orchestrator import SupportSystem

CSS = """
* { font-family: Vazirmatn, Tahoma, sans-serif; }
footer { display: none !important; }
"""

LABELS = {"orders": "🚚 پیگیری سفارش", "billing": "💳 صورت‌حساب",
          "technical": "🛠️ پشتیبانی فنی", "human": "👤 ارجاع به کارشناس"}

WELCOME = ("سلام! به پشتیبانی فروشگاه خوش آمدید. دربارهٔ سفارش، صورت‌حساب یا مشکل فنی "
           "برنامه بپرسید.")


def respond(message, chat, state):
    if not message.strip():
        return "", chat, state
    system = state or SupportSystem()
    try:
        reply = system.handle(message)
        text = f"**{LABELS.get(reply.agent, reply.agent)}**\n\n{reply.text}"
    except Exception as e:
        text = f"خطا در ارتباط با مدل: {type(e).__name__}. تنظیمات .env را بررسی کنید."
    chat = chat + [{"role": "user", "content": message},
                   {"role": "assistant", "content": text}]
    return "", chat, system


with gr.Blocks(title="Support Agents") as demo:
    gr.Markdown("## پشتیبانی هوشمند فروشگاه", rtl=True)
    chat = gr.Chatbot(rtl=True, height=480, value=[{"role": "assistant", "content": WELCOME}])
    box = gr.Textbox(placeholder="پرسش خود را بنویسید…", rtl=True, show_label=False)
    gr.Examples(["سفارش ۱۰۴۲ من کی می‌رسد؟",
                 "برای صورت‌حساب INV-77 دو بار از کارتم کم شده. پولم را برگردانید.",
                 "برنامه موقع ورود بسته می‌شود.",
                 "این کلاهبرداری است! شکایت می‌کنم."], inputs=box)
    state = gr.State()
    box.submit(respond, [box, chat, state], [box, chat, state])

if __name__ == "__main__":
    demo.launch(css=CSS)
