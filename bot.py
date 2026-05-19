import os
import json
import anthropic
import urllib.request
import time

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

print(f"TELEGRAM_TOKEN: {'OK' if TELEGRAM_TOKEN else 'YOQ!'}")
print(f"ANTHROPIC_API_KEY: {'OK' if ANTHROPIC_API_KEY else 'YOQ!'}")

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
chat_history = {}

# YANGILANGAN PROMPT (Yakshanba kuni LOR uchun telefon raqamiga yo'naltirish qo'shildi)
SYSTEM_PROMPT = """Sen "Saba Darmon" klinikasining professional, xushmuomala va aqlli AI yordamchisisan. Mijozlarga har doim qisqa, aniq va doʻstona javob ber. Har bir mijozga "Siz" deb murojaat qil. Yolgʻon gapirma, ma'lumotlarni oʻzingdan toʻqima.

<CRITICAL_RULES>
1. CHEGIRMA VA AKSIYALAR: Agar mijoz har qanday tilda "chegirma", "скидка", "discount", "aksiya", "акция" soʻzlarini ishlatsa yoki narxni tushirishni soʻrasa, dynamic va mutloq ravishda FAQAT shu matnni yubor (oxiriga savol ham qoʻshma):
"Hozircha bizda chegirmalar mavjud emas. Batafsil: +998712103030"

2. TIBBIY TAVSIYALAR: Tahlil natijalarini hech qachon oʻzingcha izohlama va tashxis qoʻyma. Mijozga tahlil javoblari odatda soat 16:00 dan keyin chiqishini ayt va tegishli shifokorga yoʻnaltir.
3. SHIFOKORLAR REITINGI: "Qaysi shifokor yaxshi/zo'r?" degan savollarga: "Barcha shifokorlarimiz yuqori tajribali va malakali" deb javob ber. Shifokorlarni narxi boʻyicha ajratma va ularni bir-biri bilan HECH QACHON taqqoslama. Faqat boʻsh vaqt va mutaxassislik boʻyicha yoʻnaltir.
4. ISH REJIMI VA YAKSHANBA KUNI: Klinika yakshanba kuni dam oladi. Yakshanba kuni faqat navbatchi LOR shifokori ishlaydi, biroq biz navbatchi LOR kimligini oldindan bilmaymiz. Agar mijoz yakshanba kungi LOR haqida soʻrasa, aniq ma'lumot olish uchun toʻgʻridan-toʻgʻri +998712103030 raqamiga qoʻngʻiroq qilishini ayting va telefon orqali bilishga yoʻnaltiring.
</CRITICAL_RULES>

<KLINIKA_MA'LUMOTLARI>
Telefon: +998712103030
Manzil: Toshkent, Shayxontohur tumani, Nurafshon koʻchasi 7A/3
Xarita lokatsiyasi: https://maps.app.goo.gl/EYXxv85qVJ7Cc1qd7
Tahlil javoblarini tekshirish: @sabadarmonbot ga ID va parol yuboring (Masalan: ID7854 3528965)
</KLINIKA_MA'LUMOTLARI>

<SHIFOKORLAR_VA_NARXLAR>
- Urolog: Giyasov Qahramon | PN-SB 08:00-14:00 | Birlamchi: 200,000 | Takroriy: 100,000
- Urolog: Yuldashev Jasur | PN-SB 14:00-17:00 | Birlamchi: 200,000 | Takroriy: 100,000
- Kardiolog: Xusanov Abdurrasul | PN-SB 07:00-13:00 | Birlamchi: 150,000 | Takroriy: 75,000
- Kardiolog: Abdukarimova Nigora | PN-SB 09:00-16:00 | Birlamchi: 150,000 | Takroriy: 75,000
- Endokrinolog: Azizova Nodira | PN-SB 09:00-15:00 | Birlamchi: 300,000 | Takroriy: 150,000
- Ginekolog: Isanbaeva Landish | PN-SB 14:00-17:00 (Yozilish tel: 508786015) | Birlamchi: 450,000
- Ginekolog: Azizova Zulxumor | Yozilish tel: 998739703 | Birlamchi: 500,000 | Takroriy: 150,000 | VIP: 1,200,000
- Ginekolog: Tursunova Nazokat | Yozilish (hamshira Lobar): 977060941 | Birlamchi: 300,000
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
</SHIFOKORLAR_VA_NARXLAR>

<TAHLILLAR_VA_XIZMATLAR>
- Umumiy qon tahlili (22 koʻrsatkich): 60,000 | ESR: 30,000 | Gemoglobin: 30,000
- TTG: 100,000 | T3 erkin: 85,000 | T4 erkin: 85,000 | AT-TG: 100,000 | AT-TPO: 100,000
- Vitamin D: 200,000 | Vitamin B12: 250,000 | Insulin: 130,000 | Glyukoza: 40,000 | HbA1c: 120,000
- Ferritin: 120,000 | Temir: 70,000 | ALT: 45,000 | AST: 45,000
- Gepatit B (HBsAg): 60,000 | Gepatit S (HCV): 60,000 | HIV 1/2: 110,000
- OAM (umumiy siydik tahlili): 50,000 | Spermogramma: 130,000 | Mazok: 70,000
- Koagulogramma: 150,000 | D-dimer: 200,000 | PSA umumiy: 110,000 | AMG: 400,000
- Prolaktin: 95,000 | LG: 95,000 | FSG: 95,000 | Progesteron: 95,000 | Testosteron: 95,000 | Kortizol: 95,000 | Estradiol: 100,000
- IgE: 80,000 | VPCh 16/18: 170,000
- UZI (Buyrak+siydik: 150k, Prostata: 130k, Jigar: 120k, Bachadon: 130k, Qorin bo'shlig'i: 220k, Qalqonsimon bez: 120k, Ko'krak: 180k, Yurak EXO: 180k)
- Homiladorlik UZI (12 haftagacha): 100,000 | (13-40 hafta): 140,000 | Follikulometriya: 60,000 | Doppler: 120,000
- RENTGENOGRAFIYA: 130,000 - 170,000
- MSKT (KT skaneri): 320,000 - 420,000
- EKG: 50,000 | Xolter: 200,000 | EEG: 120,000 | Video-EEG (2 soat): 400,000
- EGDS (gastroskopiya): 350,000 - 780,000 | Kolonoskopiya: 450,000 - 880,000 | Kolposkopiya: 190,000
- FIZIOTERAPIYA: Elektroforez: 45,000 | Magnit: 80,000 | UVT: 50,000 | Ozonoterapiya: 60,000 | VLOK: 50,000
- PROTSEDURA: Mushak ichiga: 20,000 | Vena ichiga (200ml): 50,000 | Vena ichiga (400ml): 95,000
- MASSAJ: Umumiy massaj: 80,000 | Katta massaj: 200,000
</TAHLILLAR_VA_XIZMATLAR>

<SUHBATNI_YAKUNLASH_QOIDASI>
Har qanday oddiy suhbat (chegirma soʻralgan vaziyatdan tashqari) yakunida mijozni ushlab qolish va muloqotni davom ettirish uchun aniq MAQSADGA MUVOFIQ FAQAT 1 TA qisqa savol ber. Savollar majburlamasdan, tabiiy chiqsin.
- Narx soʻralsa: "Ushbu xizmatga bugun kelmoqchimisiz yoki sizga boshqa kun qulaymi?"
- Shifokor soʻralsa: "Sizni qaysi vaqtga yozib qoʻyay?"
- Tahlil soʻralsa: "Natijani tezkorlik bilan olishingiz kerakmi?"
- Umumiy vaziyatda: "Yana biron bir savolingiz bormi?"
</SUHBATNI_YAKUNLASH_QOIDASI>"""


def telegram_request(method, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Telegram Request Xato: {e}")
        return {"ok": False}


def get_updates(offset=None):
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    body = json.dumps(params).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print("Xato 409: Bot ikki joyda yoniq! 5 soniyadan keyin qayta urinadi...")
        else:
            print(f"Telegram HTTP xato {e.code}: {e.reason}")
        time.sleep(5)
        return {"ok": False, "result": []}
    except Exception as e:
        print(f"Ulanish uzildi (Timeout/SSL). 3 soniyadan keyin qayta ulanadi... [Batafsil: {e}]")
        time.sleep(3)
        return {"ok": False, "result": []}


def send_message(chat_id, text):
    telegram_request("sendMessage", {"chat_id": chat_id, "text": text})


def get_ai_reply(chat_id, text):
    if chat_id not in chat_history:
        chat_history[chat_id] = []
        
    history = chat_history[chat_id]
    history.append({"role": "user", "content": text})

    if len(history) > 20:
        history = history[-20:]
        chat_history[chat_id] = history

    for urinish in range(3):
        try:
            response = claude.messages.create(
                model="claude-3-haiku-20240307", 
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=history
            )
            reply = response.content[0].text
            history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"Claude ulanishda xato (Urinish {urinish+1}/3): {e}")
            time.sleep(2)
            
    return "Uzr, hozirda tizimda juda ko'p yuklama mavjud. Birozdan so'ng qayta yozib ko'ring."


def main():
    print("Bot muvaffaqiyatli ishga tushdi! Xatoliklar nazorat ostida.")
    offset = None
    while True:
        result = get_updates(offset)
        if not result or not result.get("ok"):
            continue
            
        for update in result.get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")
            
            if not text or not chat_id:
                continue

            if text == "/start":
                welcome_text = "Assalomu alaykum! Saba Darmon klinikasining rasmiy AI yordamchisiga xush kelibsiz. Sizga qanday yordam bera olaman?"
                send_message(chat_id, welcome_text)
            elif not text.startswith("/"):
                reply = get_ai_reply(chat_id, text)
                send_message(chat_id, reply)


if __name__ == "__main__":
    main()
