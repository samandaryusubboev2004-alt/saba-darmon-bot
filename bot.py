import os
import json
import time
import anthropic
import urllib.request
from collections import defaultdict
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CRM_CHANNEL_ID = -1003999990660

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

chat_history = defaultdict(list)
message_counter = defaultdict(int)
last_request_time = defaultdict(float)

# =========================
# ANALYTICS
# =========================

analytics = {
    "total_messages": 0,
    "unique_users": set(),
    "hourly": defaultdict(int),
    "topics": defaultdict(int),
    "last_report": datetime.now().date()
}

TOPIC_KEYWORDS = {
    "Qon tahlili": ["qon", "blood", "кровь"],
    "UZI": ["uzi", "узи", "ultrasound"],
    "Shifokor": ["shifokor", "doktor", "врач", "doctor"],
    "Narx": ["narx", "цена", "price", "qancha", "стоимость"],
    "Manzil": ["manzil", "адрес", "address", "qayer"],
    "Telefon": ["telefon", "телефон", "raqam"],
    "Tahlil natija": ["natija", "результат", "javob"],
    "LOR": ["lor", "лор", "quloq", "burun", "tomoq"],
    "Ginekolog": ["ginekolog", "гинеколог"],
    "Urolog": ["urolog", "уролог"],
    "Kardiolog": ["kardiolog", "кардиолог", "yurak"],
}

def detect_topic(text):
    text_lower = text.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return topic
    return "Boshqa"

def update_analytics(user_id, text):
    analytics["total_messages"] += 1
    analytics["unique_users"].add(user_id)
    hour = datetime.now().hour
    analytics["hourly"][hour] += 1
    topic = detect_topic(text)
    analytics["topics"][topic] += 1

# =========================
# DAILY REPORT — BUG TUZATILDI
# =========================

report_sent_today = False

def send_daily_report():
    global report_sent_today

    today = datetime.now().date()
    top_topics = sorted(analytics["topics"].items(), key=lambda x: x[1], reverse=True)[:3]
    top_hours = sorted(analytics["hourly"].items(), key=lambda x: x[1], reverse=True)[:3]

    topics_text = "\n".join([f"  {i+1}. {t}: {c} ta" for i, (t, c) in enumerate(top_topics)])
    hours_text = "\n".join([f"  {h}:00 - {c} xabar" for h, c in top_hours])

    report = (
        f"📊 Kunlik hisobot — {today}\n\n"
        f"👥 Yangi mijozlar: {len(analytics['unique_users'])} ta\n"
        f"💬 Jami xabarlar: {analytics['total_messages']} ta\n\n"
        f"🔥 Ko'p so'ralgan:\n{topics_text}\n\n"
        f"⏰ Eng faol vaqt:\n{hours_text}"
    )

    try:
        telegram_request("sendMessage", {
            "chat_id": CRM_CHANNEL_ID,
            "text": report
        })
    except Exception as e:
        print(f"Hisobot xato: {e}")

    analytics["total_messages"] = 0
    analytics["unique_users"] = set()
    analytics["hourly"] = defaultdict(int)
    analytics["topics"] = defaultdict(int)
    analytics["last_report"] = today
    report_sent_today = True

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
- Mijozga HAR DOIM "siz" deb murojaat qil, hech qachon "sen" dema
- Faqat togri imlo bilan yoz, xato yozma
- Qisqa va aniq yoz
- Dostona gapir
- Emoji ni kam ishlatma
- Markdown ishlatma
- Doktorlarni taqqoslama
- Eng yaxshi, eng arzon degan gaplarni ishlatma
- Tahlil natijalarini izohlama, faqat shifokorga yonalt
- Chegirma, skidka, aksiya haqida soʻrasa faqat: Hozircha bizda chegirmalar mavjud emas. Batafsil: +998712103030
- Tahlil javoblari soat 16:00 dan keyin chiqadi
- Yakshanba kuni faqat navbatchi LOR ishlaydi, aniq shifokor ismi aytilmaydi
- Shifokor vaqtini aytganda oxirida har doim qosh: Jadval ozgarishi mumkin, aniq vaqt uchun call-markaz bilan boganing: +998712103030
- Birinchi xabarga faqat: Salom! Saba Darmon klinikasiga xush kelibsiz. Sizga qanday yordam bera olaman?
- Qisqa javob ber, keraksiz gap qoshma
- Uylab topilgan sozlarni ishlatma
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
- Ginekolog: Tursunova Nazokat | yozilish hamshira Lobar 977060941 | Birlamchi: 300,000
- Ginekolog: Samadova Guzal | PN-JM 09:00-14:00 | Birlamchi: 150,000 | Takroriy: 75,000
- Pediatr: Kamilova Durdonaxon | PN-SB 09:00-12:00 | Birlamchi: 150,000 | Takroriy: 75,000
- LOR: Omonjonov Husniddin | PN-JM 09:00-18:00 | Birlamchi: 200,000 | Takroriy: 75,000
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
# TYPING INDIKATOR — YANGI
# =========================

def send_typing(chat_id):
    try:
        telegram_request("sendChatAction", {
            "chat_id": chat_id,
            "action": "typing"
        })
    except Exception as e:
        print(f"Typing xato: {e}")

# =========================
# CRM
# =========================

def send_to_crm(user_id, username, first_name, text, reply):
    try:
        name = first_name or "Noma'lum"
        uname = f"@{username}" if username else "username yoq"
        crm_text = (
            f"📩 Yangi xabar!\n"
            f"👤 Ism: {name}\n"
            f"🔗 Username: {uname}\n"
            f"🆔 ID: {user_id}\n"
            f"💬 Savol: {text}\n"
            f"🤖 Javob: {reply[:200]}..."
        )
        telegram_request("sendMessage", {
            "chat_id": CRM_CHANNEL_ID,
            "text": crm_text
        })
    except Exception as e:
        print(f"CRM xato: {e}")

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
            model="claude-sonnet-4-6",
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
    global report_sent_today

    print("Bot ishga tushdi!")
    offset = None

    while True:
        now = datetime.now()

        # Daily report — faqat bir marta soat 20:00 da
        if now.hour == 20 and not report_sent_today:
            send_daily_report()
        if now.hour == 21:
            report_sent_today = False  # Ertangi kun uchun reset

        result = get_updates(offset)
        if not result.get("ok"):
            continue

        for update in result.get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")
            user_id = message.get("from", {}).get("id")
            username = message.get("from", {}).get("username")
            first_name = message.get("from", {}).get("first_name")

            if not text or not chat_id:
                continue

            # /start va boshqa komandalar — YANGI
            if text.startswith("/"):
                if text == "/start":
                    send_typing(chat_id)
                    send_message(chat_id,
                        "Salom! 👋 Saba Darmon klinikasiga xush kelibsiz.\n\n"
                        "Shifokorlar, tahlillar, narxlar yoki manzil haqida "
                        "so'ragan savolingizga javob beramiz.\n\n"
                        "Sizga qanday yordam bera olaman?"
                    )
                continue

            if not check_rate_limit(chat_id):
                send_message(chat_id, "Juda tez yozmoqdasiz, biroz kuting.")
                continue

            update_analytics(user_id, text)

            # Typing indikator — javobdan OLDIN
            send_typing(chat_id)

            reply = get_ai_reply(chat_id, text)
            send_message(chat_id, reply)
            send_to_crm(user_id, username, first_name, text, reply)

if __name__ == "__main__":
    main()
