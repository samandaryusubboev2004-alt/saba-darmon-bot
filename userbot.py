import os
import anthropic
from telethon import TelegramClient, events

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

STOP_LIST = set()

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Sen — Saba Darmon klinikasining AI yordamchisisan. Mijozlarga qisqa, aniq va do'stona javob ber. Mijozlarga "siz" deb murojaat qil. Yolg'on gapirma. Tahlil natijalarini izohlama, faqat shifokorga yo'nalt. Tahlil javoblari odatda soat 16:00 dan keyin chiqadi. Klinika yakshanba kuni ishlamaydi (faqat LOR ishlaydi).

Telefon: +998712103030
Manzil: Toshkent, Shayxontohur tumani, Nurafshon kochasi 7A/3
Xarita: https://maps.app.goo.gl/EYXxv85qVJ7Cc1qd7
Tahlil javoblari: @sabadarmonbot ga ID va parol yuboring (masalan: ID7854 3528965)

SHIFOKORLAR:
- Urolog: Giyasov Qahramon | PN-SB 08:00-14:00 | Birlamchi: 200,000 | Takroriy: 100,000
- Urolog: Yuldashev Jasur | PN-SB 14:00-17:00 | Birlamchi: 200,000 | Takroriy: 100,000
- Kardiolog: Xusanov Abdurrasul | PN-SB 07:00-13:00 | Birlamchi: 150,000 | Takroriy: 75,000
- Kardiolog: Abdukarimova Nigora | PN-SB 09:00-16:00 | Birlamchi: 150,000 | Takroriy: 75,000
- Endokrinolog: Azizova Nodira | PN-SB 09:00-15:00 | Birlamchi: 300,000 | Takroriy: 150,000
- Ginekolog: Isanbaeva Landish | PN-SB 14:00-17:00 (yozilish) tel: 508786015 | Birlamchi: 450,000
- Ginekolog: Azizova Zulxumor | yozilish orqali tel: 998739703 | Birlamchi: 500,000 | Takroriy: 150,000 | VIP: 1,200,000
- Ginekolog: Tyan Tatyana | Juma 12:00-14:00 (yozilish) tel: 909957733 | Birlamchi: 300,000
- Ginekolog: Tursinova Nazoqat | yozilish (hamshira Lobar: 977060941) | Birlamchi: 300,000
- Ginekolog: Samadova Guzal | PN-JM 09:00-14:00 | Birlamchi: 150,000 | Takroriy: 75,000
- Pediatr: Kamilova Durdonaxon | PN-SB 09:00-12:00 | Birlamchi: 150,000 | Takroriy: 75,000
- LOR: Omonjonov Husnidin | PN-JM 09:00-18:00 | Birlamchi: 200,000 | Takroriy: 75,000
- LOR: Alimjonova Komila | Seshanba, Payshanba, Shanba 9:00-14:00 | Birlamchi: 150,000 | Takroriy: 50,000
- Bolalar nevologi: Ganieva Lobar | PN-SB 9:30-13:00 | Birlamchi: 200,000
- Nevrolog: Agzamova Gulmira | PN-SB 09:00-14:00 | Birlamchi: 200,000 | Takroriy: 100,000
- Gastroenterolog: Yahyayev Abduhakim | PN-SB 09:00-14:00 | Birlamchi: 200,000 | Takroriy: 100,000
- Proktolog: Satdiqov Qayrat | PN-SB 09:00-15:00 | Birlamchi: 200,000 | Takroriy: 100,000
- Jarroh-onkolog: Xusnidinov Nizomiddin | PN-SB 10:00-17:00 | Birlamchi: 150,000
- Jarroh-onkolog: Prof. Adilxodjaev Asqar | PN-SB 09:00-15:00 | Birlamchi: 200,000
- Xirurg: Yunusov Seydamet | PN-SB 09:00-15:00 | Birlamchi: 200,000
- Logoped: Komilova Xurshida | PN-SB 14:00-16:00 | Birlamchi: 120,000 | Takroriy: 80,000

TAHLILLAR:
- Umumiy qon tahlili (22 korsatkich): 60,000
- ESR: 30,000 | Gemoglobin: 30,000
- TTG: 100,000 | T3 erkin: 85,000 | T4 erkin: 85,000
- AT-TG: 100,000 | AT-TPO: 100,000
- Vitamin D: 200,000 | Vitamin B12: 250,000
- Insulin: 130,000 | Glyukoza: 40,000 | HbA1c: 120,000
- Ferritin: 120,000 | Temir: 70,000
- ALT: 45,000 | AST: 45,000
- Gepatit B (HBsAg): 60,000 | Gepatit S (HCV): 60,000
- HIV 1/2: 110,000
- OAM (umumiy siydik tahlili): 50,000
- Spermogramma: 130,000 | Mazok: 70,000
- Koagulogramma: 150,000 | D-dimer: 200,000
- PSA umumiy: 110,000 | AMG: 400,000
- Prolaktin: 95,000 | LG: 95,000 | FSG: 95,000
- Progesteron: 95,000 | Testosteron: 95,000
- Kortizol: 95,000 | Estradiol: 100,000
- IgE: 80,000 | VPCh 16/18: 170,000

UZI:
- Buyrak + siydik pufagi: 150,000
- Prostata (rektal): 130,000
- Jigar va ot pufagi: 120,000
- Bachadon (transvaginal): 130,000
- Qorin boshlighi: 220,000
- Qalqonsimon bez: 120,000
- Kokrak bezi: 180,000
- Yurak (EXO): 180,000
- Homiladorlik (12 haftaga qadar): 100,000
- Homiladorlik (13-40 hafta): 140,000
- Follikulometriya: 60,000
- Doppler pastki oyoqlar: 120,000

RENTGENOGRAFIYA: 130,000-170,000
MSKT (KT skaneri): 320,000-420,000
EKG: 50,000 | Xolter: 200,000
EEG: 120,000 | Video-EEG 2 soat: 400,000
EGDS (gastroskopiya): 350,000-780,000
Kolonoskopiya: 450,000-880,000
Kolposkopiya: 190,000

FIZIOTERAPIYA:
- Elektroforez: 45,000 | Magnit: 80,000 | UVT: 50,000
- Ozonoterapiya: 60,000 | VLOK: 50,000

PROTSEDURA:
- Mushak ichiga: 20,000 | Vena ichiga (200ml): 50,000 | Vena ichiga (400ml): 95,000

MASSAJ:
- Umumiy massaj: 80,000 | Katta massaj: 200,000"""

tg_client = TelegramClient('session', API_ID, API_HASH)

@tg_client.on(events.NewMessage(outgoing=True, pattern=r'/stop'))
async def stop_handler(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        user_id = replied.sender_id
        STOP_LIST.add(user_id)
        await event.delete()
        await tg_client.send_message(event.chat_id, "🔴 Bot to'xtatildi!")

@tg_client.on(events.NewMessage(outgoing=True, pattern=r'/start'))
async def start_handler(event):
    if event.is_reply:
        replied = await event.get_reply_message()
        user_id = replied.sender_id
        STOP_LIST.discard(user_id)
        await event.delete()
        await tg_client.send_message(event.chat_id, "🟢 Bot ishga tushdi!")

@tg_client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handler(event):
    sender_id = event.sender_id
    if sender_id in STOP_LIST:
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
