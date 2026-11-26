"""
اولین درخواست به مدل زبانی با کتابخانهٔ openai (اسلاید ۳-۵).

چهار جزء شماره‌دار در اسلاید:
    ① کلید دسترسی  ② نشانی پایه  ③ نام مدل  ④ پیام‌ها
"""

import os

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

load_dotenv(find_dotenv(usecwd=True) or find_dotenv())

client = OpenAI(
    api_key=os.getenv("ARVAN_API_KEY"),     # ①
    base_url=os.getenv("ARVAN_BASE_URL"),   # ②
)

response = client.chat.completions.create(
    model=os.getenv("ARVAN_MODEL"),         # ③
    messages=[                            # ④
        {"role": "system", "content": "You are a tutor."},
        {"role": "user", "content": "What is an AI agent?"},
    ],
)
print(response.choices[0].message.content)

# مصرف توکن این درخواست (اسلاید «توکن، هزینه و محدودیت»)
if response.usage:
    print(f"\n[usage] prompt={response.usage.prompt_tokens} "
          f"completion={response.usage.completion_tokens} "
          f"total={response.usage.total_tokens}")
