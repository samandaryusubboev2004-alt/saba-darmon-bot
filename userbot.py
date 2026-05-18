import os
import anthropic
from telethon import TelegramClient, events

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

STOP_LIST = []  # bloklangan user_id lar, masalan: [123456789, 987654321]

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Sen — Saba Darmon klinikasining AI yordamchisisan. Mijozlarga qisqa, aniq va do'stona javob ber. Mijozlarga "siz" deb murojaat qil. Yolg'on gapirma. Tahlil natijalarini izohlama, faqat shifokorga yo'nalt."""

tg_client = TelegramClient('session', API_ID, API_HASH)

@tg_client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handler(event):
    if event.sender_id in STOP_LIST:
        return
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": event.text}]
        )
        await event.reply(response.content[0].text)
    except Exception as e:
        print(f"XATO: {e}")

print("Userbot ishga tushdi!")
tg_client.start()
tg_client.run_until_disconnected()
