import os
import json
import time
import anthropic
import urllib.request
from collections import defaultdict

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

chat_history = defaultdict(list)
message_counter = defaultdict(int)
last_request_time = defaultdict(float)

# =========================
# FAQ SYSTEM
# =========================

FAQ = {
    "manzil": "Saba Darmon klinikasi manzili: Toshkent, Shayxontohur tumani, Nurafshon kochasi 7A/3\nXarita: https://maps.app.goo.gl/EYXxv85qVJ7Cc1qd7",
    "telefon": "Telefon: +998712103030",
    "raqam": "Telefon: +998712103030",
    "nomber": "Telefon: +998712103030",
    "ish vaqti": "Klinika dushanba-shanba ishlaydi. Yakshanba kuni faqat navbatchi LOR ishlaydi.",
    "qachon ishlaydi": "Klinika dushanba-shanba ishlaydi. Yakshanba kuni faqat navbatchi LOR ishlaydi.",
    "tahlil javob": "Tahlil javoblari odatda soat 16:00 dan keyin chiqadi. @sabadarmonbot ga ID va parol yuboring.",
    "natija": "Tahlil natijalari odatda soat 16:00 dan keyin chiqadi. @sabadarmonbot ga ID va parol yuboring.",
}

# =========================
# SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = """Sen Saba Darmon klinikasining professional AI yordamchisisan.

QOIDALAR:
- Qisqa va aniq yoz
- Dostona gapir
- Mijozga siz deb murojaat qil
- Emoji ni kam ishlatma
- Markdown ishlatma
- Doktorlarni taqqoslama
- Eng yaxshi, eng arzon degan gaplarni ishlatma
- Tahlil natijalarini izohlama, faqat shifokorga yonalt
- Chegirma, skidka, aksiya haqida soʻrasa faqat: Hozircha bizda chegirmalar mavjud emas. Batafsil: +998712103030
- Tahlil javoblari soat 16:00 dan keyin chiqadi
- Klinika yakshanba kuni ishlamaydi, faqat LOR ishlaydi
- Har javob oxirida bitta tabiiy savol ber

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
- Ginekolog: Isanbaeva Landish | PN-SB 14:00-17:00 yozilish tel 508786015 | Birlamchi: 450,000
- Ginekolog: Azizova Zulxumor | yozilish tel 998739703 | Birlamchi: 500,000 | Takroriy: 150,000 | VIP: 1,200,000
- Ginekolog: Tyan Tatyana | Juma 12:00-14:00 yozilish tel 909957733 | Birlamchi: 300,000
- Ginekolog: Tursinova Nazoqat | yozilish hamshira Lobar 977060941 | Birlamchi: 300,000
- Ginekolog: Samadova Guzal | PN-JM 09:00-14:00 | Birlamchi: 150,000 | Takroriy: 75,000
- Pediatr: Kamilova Durdonaxon | PN-SB 09:00-12:00 | Birlamchi: 150,000 | Takroriy: 75,000
- LOR: Omonjonov Husnidin | PN-JM 09:00-18:00 | Birlamchi: 200,000 | Takroriy: 75,000
- LOR: Alimjonova Komila | Seshanba Payshanba Shanba 9:00-14:00 | Birlamchi: 150,000 | Takroriy: 50,000
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
- Bilirubin: 30,000 | Oqsil: 40,000 | Mochevina: 45,000 | Kreatinin: 45,000
- Xolesterin: 40,000 | Kaliy: 55,000 | Kalsiy: 45,000
- Gepatit B: 60,000 | Gepatit S: 60,000 | HIV: 110,000
- OAM siydik: 50,000 | Mocha Nechipurenko: 50,000
- Spermogramma: 130,000 | Mazok: 70,000
- Koagulogramma: 150,000 | D-dimer: 200,000
- PSA: 110,000 | AMG: 400,000
- Prolaktin LG FSG Progesteron Testosteron: 95,000 har biri
- Kortizol: 95,000 | Estradiol: 100,000
- IgE: 80,000 | VPCh 16/18: 170,000
- Toksoplazmoz IgG: 55,000 | IgM: 75,000
- Sitomegalovirus IgG: 55,000 | IgM: 75,000
- Rubella IgG: 55,000 | IgM: 75,000
- Herpes IgG: 55,000 | IgM: 75,000
- Xlamidiya IgG: 55,000 | IgM: 75,000
- Mikoplazma IgG: 55,000 | IgM: 75,000
- Bak. posev: 110,000 | PCR mazok: 150,000
- Kovid PCR: 300,000 | Biopsiya: 605,000

UZI:
- Buyrak siydik pufagi: 150,000
- Prostata rektal: 130,000
- Jigar ot pufagi: 120,000
- Bachadon transvaginal: 130,000
- Qorin boshlighi: 220,000
- Qalqonsimon bez: 120,000
- Kokrak bezi: 180,000
- Yurak EXO: 180,000
- Homiladorlik 12 haftaga: 100,000
- Homiladorlik 13-40 hafta: 140,000
- Follikulometriya: 60,000
- Doppler pastki oyoqlar: 120,000

RENTGEN: 130,000-170,000
MSKT KT: 320,000-420,000
EKG: 50,000 | Xolter: 200,000
EEG: 120,000 | Video-EEG: 400,000
EGDS gastroskopiya: 350,000-780,000
Kolonoskopiya: 450,000-880,000
Kolposkopiya: 190,000

FIZIOTERAPIYA:
- Elektroforez: 45,000 | Magnit: 80,000 | UVT: 50,000
- Ozonoterapiya: 60,000 | VLOK: 50,000

PROTSEDURA:
- Mushak ichiga: 20,000 | Vena 200ml: 50,000 | Vena 400ml: 95,000

MASSAJ:
- Umumiy: 80,000 | Katta: 200,000"""

# =========================
# TELEGRAM REQUEST
# =========================

def telegram_request(method, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# =========================
# SEND MESSAGE
# =========================

def send_message(chat_id, text):
    telegram_request("sendMessage", {"chat_id": chat_id, "text": text})

# =========================
# GET UPDATES
# =========================

def get_updates(offset=None):
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    body = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Update error: {e}")
        return {"ok": False, "result": []}

# =========================
# RATE LIMIT
# =========================

def check_rate_limit(chat_id):
    now = time.time()
    if now - last_request_time[chat_id] < 1.5:
        return False
    last_request_time[chat_id] = now
    return True

# =========================
# FAQ CHECK
# =========================

def check_faq(text):
    text_lower = text.lower()
    for key, value in FAQ.items():
        if key in text_lower:
            return value
    return None

# =========================
# AI REPLY
# =========================

def get_ai_reply(chat_id, text):
    faq_answer = check_faq(text)
    if faq_answer:
        return faq_answer + "\n\nYana biror savolingiz bormi?"

    history = chat_history[chat_id]
    history.append({"role": "user", "content": text})

    if len(history) > 10:
        history = history[-10:]
        chat_history[chat_id] = history

    try:
        response = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=history
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})

        message_counter[chat_id] += 1
        if message_counter[chat_id] >= 6:
            reply += "\n\nInstagram: https://www.instagram.com/saba_darmon_klinika/"
            message_counter[chat_id] = 0

        return reply

    except Exception as e:
        print(f"Claude error: {e}")
        return "Uzr, vaqtinchalik xatolik yuz berdi. Qayta urinib koring."

# =========================
# MAIN
# =========================

def main():
    print("Bot ishga tushdi!")
    offset = None
    while True:
        result = get_updates(offset)
        if not result.get("ok"):
            continue
        for update in result.get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")

            if not text or not chat_id:
                continue
            if text.startswith("/"):
                continue
            if not check_rate_limit(chat_id):
                send_message(chat_id, "Juda tez yozmoqdasiz, biroz kuting.")
                continue

            reply = get_ai_reply(chat_id, text)
            send_message(chat_id, reply)

if __name__ == "__main__":
    main()
