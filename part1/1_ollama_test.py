import ollama

response = ollama.chat(
    model="gemma3:1b",
    messages=[
        {
            "role": "user",
            "content": "Hi"
        }
    ]
)

print(response.message.content)