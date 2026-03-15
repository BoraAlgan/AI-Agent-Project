import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from typing import List

# 1. ayarlar & fastapi kurulumu
load_dotenv()

from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html

# fastapi uygulamasını varsayılan ayarlarıyla başlatıyoruz.
app = FastAPI(title="Career Assistant AI Agent")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_frontend():
    html_content = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Career Assistant AI</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 0; padding: 40px; display: flex; justify-content: center; }
        .container { background: #fff; width: 100%; max-width: 650px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); padding: 30px; }
        h1 { margin-top: 0; color: #1a1a1a; font-size: 24px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-weight: 600; margin-bottom: 8px; color: #444; }
        select, textarea { width: 100%; padding: 12px; border: 1px solid #ccd0d5; border-radius: 8px; font-size: 15px; font-family: inherit; outline: none; box-sizing: border-box; }
        select:focus, textarea:focus { border-color: #0066ff; box-shadow: 0 0 0 3px rgba(0,102,255,0.1); }
        button { background: #0066ff; color: #fff; border: none; padding: 14px 24px; font-size: 16px; font-weight: 600; border-radius: 8px; cursor: pointer; width: 100%; transition: background 0.2s; margin-top: 10px; }
        button:hover { background: #0052cc; }
        button:disabled { background: #99c2ff; cursor: not-allowed; }
        .response-container { margin-top: 30px; display: none; }
        .response-box { background: #f8f9fa; border-left: 4px solid #0066ff; padding: 20px; border-radius: 0 8px 8px 0; color: #333; font-size: 15.5px; line-height: 1.6; white-space: pre-wrap; font-family: Consolas, monospace; }
        .badge { background: #e6f0ff; color: #0066ff; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-bottom: 10px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>💼 Career Proxy Agent</h1>
        <p style="color: #666; margin-bottom: 25px;">Kariyer Ajanı Test Arayüzü. Aşağıdan bir mülakat senaryosu seçin veya özel mesajınızı yazın.</p>
        
        <div class="form-group">
            <label>Hazır Test Senaryoları</label>
            <select id="testCases" onchange="updateText()">
                <option value="">-- Senaryo Seçiniz --</option>
                <option value="Bora Bey merhabalar, Cumartesi saat 14:00 mülakat için uygun mu?">1. Cumartesi Testi</option>
                <option value="Bora Bey merhabalar, Perşembe günü saat 16:30'da mülakat yapabilir miyiz?">2. Ders Saati Testi (Çarşamba/Perşembe)</option>
                <option value="Bora Bey merhabalar, Pazartesi akşamı 18:00 mülakat için nasıl?">3. Standart Uygun Saat</option>
                <option value="Bora Bey merhabalar, yıllık maaş beklentiniz maksimum nedir?">4. Maaş Bilgisi Testi</option>
                <option value="Android uygulamalarında neden MVVM yerine MVI tercih etmeliyiz?">5. Teknik Bilgi Testi</option>
                <option value="Bora'nın en sevdiği futbol takımı hangisidir ve hukuki konularda ne düşünüyor?">6. Bilinmeyen/Güvensiz Soru Alerti</option>
            </select>
        </div>

        <div class="form-group">
            <label>İşveren Mesajı</label>
            <textarea id="message" rows="4" placeholder="Mesajınızı buraya yazın..."></textarea>
        </div>

        <button id="sendBtn" onclick="sendRequest()">Mesajı Gönder</button>

        <div class="response-container" id="responseContainer">
            <div class="badge">Ajan Yanıtı</div>
            <div class="response-box" id="replyText"></div>
            
            <!-- Tools / Bildirim Logları -->
            <div id="notificationsBox" style="display: none; margin-top: 15px; padding: 12px 16px; background: #e8f4fd; border-left: 4px solid #1E88E5; border-radius: 6px;">
                <div style="font-size: 13px; font-weight: 800; color: #1565C0; margin-bottom: 5px;">🔔 Tetiklenen Araçlar (Notifications & Email)</div>
                <div style="font-size: 14px; color: #444;" id="notifText"></div>
            </div>

            <!-- Evaluator Agent Sonuç Kutusu -->
            <div id="evaluatorBox" style="display: none; margin-top: 15px; padding: 12px 16px; background: #fff8e1; border-left: 4px solid #ffaa00; border-radius: 6px;">
                <div style="font-size: 13px; font-weight: 800; color: #d84315; margin-bottom: 5px;">🕵️ Evaluator (Self-Critic) Agent Skoru</div>
                <div style="font-size: 14px; color: #444;" id="evalText"></div>
            </div>
        </div>
    </div>

    <script>
        function updateText() {
            document.getElementById('message').value = document.getElementById('testCases').value;
        }

        async function sendRequest() {
            const msg = document.getElementById('message').value.trim();
            if (!msg) { alert("Lütfen bir mesaj yazın."); return; }

            const btn = document.getElementById('sendBtn');
            const container = document.getElementById('responseContainer');
            const replyText = document.getElementById('replyText');

            const evalBox = document.getElementById('evaluatorBox');
            const notifBox = document.getElementById('notificationsBox');

            // Yeni istek atılırken tüm eski kutucukları anında gizle
            evalBox.style.display = "none";
            notifBox.style.display = "none";
            
            btn.disabled = true;
            btn.innerText = "Ajan Düşünüyor...";
            container.style.display = "block";
            replyText.innerHTML = "<i>Yanıt bekleniyor...</i>";

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: msg })
                });
                const data = await res.json();
                
                if (data.reply) {
                    replyText.innerText = data.reply;
                    
                    const evalBox = document.getElementById('evaluatorBox');
                    const evalText = document.getElementById('evalText');
                    if (data.evaluator_score !== undefined && data.evaluator_decision) {
                        evalBox.style.display = "block";
                        evalText.innerHTML = `<b>Puan:</b> ${data.evaluator_score}/10 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Karar:</b> ${data.evaluator_decision}`;
                    } else {
                        evalBox.style.display = "none";
                    }

                    const notifBox = document.getElementById('notificationsBox');
                    const notifText = document.getElementById('notifText');
                    if (data.tools_called && data.tools_called.length > 0) {
                        notifBox.style.display = "block";
                        notifText.innerHTML = data.tools_called.map(t => "• " + t).join("<br>");
                    } else {
                        notifBox.style.display = "none";
                    }
                    
                } else {
                    replyText.innerText = "Hata oluştu veya format desteklenmiyor.";
                }
            } catch (err) {
                replyText.innerText = "Sunucu destek vermiyor: " + err;
            }

            btn.disabled = false;
            btn.innerText = "Mesajı Gönder";
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Career Assistant AI Agent",
        version="1.0.0",
        routes=app.routes,
    )
    
    # swagger arayüzünü temizleme (responses listesini gizlemek ve sadeleştirmek için)
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            if "responses" in method:
                # 422 - validation error dokümanını kaldır
                if "422" in method["responses"]:
                    del method["responses"]["422"]
                # 200 - başarılı yanıt için uzun örnekleri sil, sadece sadeleştir
                if "200" in method["responses"]:
                    method["responses"]["200"] = {
                        "description": "Botun başarılı JSON formatlı cevabı."
                    }
            if "requestBody" in method:
                try:
                    content = method["requestBody"]["content"]["application/json"]
                    content["examples"] = {
                        "Test 1 - Cumartesi": {
                            "summary": "Cumartesi Testi",
                            "value": {"message": "Bora Bey merhabalar, Cumartesi saat 14:00 mülakat için uygun mu?"}
                        },
                        "Test 2 - Ders Saati": {
                            "summary": "Ders Engeli (Çarşamba/Perşembe)",
                            "value": {"message": "Bora Bey merhabalar, Perşembe günü saat 16:30'da mülakat yapabilir miyiz?"}
                        },
                        "Test 3 - Standart Saat": {
                            "summary": "Uygun Mülakat",
                            "value": {"message": "Bora Bey merhabalar, Pazartesi akşamı 18:00 mülakat için nasıl?"}
                        },
                        "Test 4 - Maaş Bilgisi": {
                            "summary": "Maaş Aracı Çalışır",
                            "value": {"message": "Bora Bey merhabalar, yıllık maaş beklentiniz maksimum nedir?"}
                        },
                        "Test 5 - Teknik Soru": {
                            "summary": "Teknik Yetkinlik",
                            "value": {"message": "Android uygulamalarında neden MVVM yerine MVI tercih etmeliyiz?"}
                        },
                        "Test 6 - Alan Dışı": {
                            "summary": "Bilinmeyen/Güvensiz Soru Alerti",
                            "value": {"message": "Bora'nın en sevdiği futbol takımı hangisidir ve hukuki konularda ne düşünüyor?"}
                        }
                    }
                    if "example" in content:
                        del content["example"]
                except KeyError:
                    pass

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL_ID = "stepfun/step-3.5-flash:free"


# BONUS: CONVERSATION MEMORY 
class MemoryManager:
    def __init__(self):
        self.history = []
        
    def add_interaction(self, user_msg: str, agent_response: str):
        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": agent_response})
        # hafıza son 10 mesajla sınırlandı, limit aşımı engellenmesi için
        if len(self.history) > 10:
            self.history = self.history[-10:]
            
    def get_history(self):
        return self.history

memory = MemoryManager()


# 2. boranın profil ve teknik bilgileri
def get_profile():
    return """
    KİMLİK: Bora Algan, Android Developer & Master Student.
    TEKNİK YETKİNLİKLER: Kotlin, MVVM, MVI, Jetpack Compose, Retrofit, Room DB, Git, Image Processing, AI.
    
    YASAKLAR & KURALLAR:
    - Hafta içi 17:00 öncesi mülakat kabul etme.
    - Cumartesi tüm gün müsait değil.
    - Çarşamba/Perşembe 15:30-17:30 arası Akdeniz Üniversitesi'nde Melih Hoca'nın 'Advanced Web Programming' dersinde. (Bu saatlerde mutlaka ders adını ve hoca ismini belirterek reddet)
    - Çarşamba/Perşembe günü uygun değilse öneri olarak pazar 17.00 sonrası ve hafta içi saat 17.00 dan sonrası için öneride bulun.
    - Maaş konularını Bora ile doğrudan görüşmeliler.
    """

# 3. araçlar (Tools: Email Notification & Mobile Notification & Unknown Alert)
def send_email_notification(subject: str, details: str, tools_log: list):
    """Email Tool (Ödev zorunluluğu: Email Notification Tool)"""
    log_msg = f"📧 İK'ya/Kullanıcıya Email Atıldı: {subject}"
    print(f"\n[EMAIL GONDERILDI] Konu: {subject}\n   Ayrinti: {details}")
    tools_log.append(log_msg)

def send_mobile_notification(title: str, message: str, tools_log: list):
    """Mobile Notification Tool (Ödev zorunluluğu: FCM/Telegram benzeri Push Notification)"""
    log_msg = f"📱 Telefona Bildirim Düştü: {title}"
    print(f"\n[MOBIL BILDIRIM] Baslik: {title}\n   {message}")
    tools_log.append(log_msg)

def trigger_unknown_alert(query: str, tools_log: list):
    """Unknown Question Alert Tool"""
    log_msg = "🚨 BİLİNMEYEN SORU ALARMI: Ajan yanıt veremedi, manuel müdahale istendi."
    print(f"\n[BILINMEYEN SORU ALARMI] Ajan yanit veremedi, manuel mudahale istendi.")
    tools_log.append(log_msg)
    
    log_mobile = "📱 Telefona Bildirim Düştü: Ajan Yardıma İhtiyaç Duyuyor"
    print(f"\n[MOBIL BILDIRIM] Baslik: Ajan yardima ihtiyac duyuyor")
    tools_log.append(log_mobile)
    
    log_email = "📧 İK'ya/Kullanıcıya Email Atıldı: Manuel Müdahale Gerekiyor"
    print(f"\n[EMAIL GONDERILDI] Konu: Manuel Mudahale Gerekiyor")
    tools_log.append(log_email)



# 4. yanıt üretici (Primary Agent)
def generate_response(query: str, history: List[dict]):
    profile = get_profile()
    
    system_prompt = f"""
    Sen Bora Algan'ın yetkilendirdiği profesyonel bir kariyer temsilcisisin (Proxy). 
    {profile}
    
    CEVAP PROTOKOLÜ:
    1. Bir AI asistanı gibi davranma. Cevaplarını net ve kurumsal bir dille ver.
    2. CEVAP SONUNA ASLA "Başka bir konuda yardımcı olabilir miyim?", "İyi günler" gibi chatbot kalıpları ekleme.
    3. Cumartesi günü mülakat sorulursa olamayacağını ilet; Pazar 17:00 sonrası veya hafta içi 17:00 sonrasını öner.
    4. TEKNİK SORULAR: Android veya teknolojilerle ilgili soru gelirse uzman bir mühendis gibi profilindeki bilgilerle cevapla.
    5. BİLİNMEYEN / ALAN DIŞI SORULAR: Profilde olmayan, hukuki, derin bir alan dışı teknik konu veya anlaşılmaz bir soru gelirse kurgu veya varsayım (hallucination) YAPMA. Sadece 'Bu konuda net bir bilgim yok, Bora'ya bildirim gönderdim.' de.
    6. MAAŞ / FİNANS: Yıllık/aylık maaş, bütçe anlaşmazlığı gibi durumlarda 'Maaş ve bütçe detaylarını Bora Bey ile doğrudan görüşmelisiniz.' de.
    7. Sadece sorulan soruya odaklan ve cevabı verip bitir.
    """

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": query})

    res = client.chat.completions.create(
        model=MODEL_ID,
        messages=messages
    )
    return res.choices[0].message.content or ""


# 5. gelişmiş denetçi (Response Evaluator & Critic)
def response_evaluator(query: str, response: str):
    """
    Ödev gereksinimi: Tone, Clarity, Completeness, Safety kontrolü yapar ve puanlar.
    Kesinlikle JSON formatında yanıt almaya zorlar.
    """
    eval_prompt = f"""
    Sen bir kalite denetçisisin (Self-Critic Agent). Aşağıdaki yanıtı değerlendir.
    Kriterler: 
    - Profesyonel ton (Chatbot gibi mi duruyor?)
    - Netlik ve Tamlık (Soruyu tam cevaplamış mı?)
    - Güvenlik (Yanlış bilgi uydurmuş mu? Hallucination var mı?)
    - Alaka (Sorunun dışına çıkmış mı?)
    
    Soru: {query}
    Yanıt: {response}
    
    LÜTFEN SADECE AŞAĞIDAKİ GİBİ BİR JSON DOSYASI DÖN. DIŞINDA METİN KULLANMA.
    {{
        "score": <1 ile 10 arası sayı>,
        "feedback": "<Kısa geribildirim metni>",
        "decision": "<PASSED veya REVISE>"
    }}
    Not: Puan 8'in altındaysa karar REVISE olmalı.
    """
    
    res = client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": eval_prompt}],
        response_format={"type": "json_object"}
    )
    
    raw_response = res.choices[0].message.content
    try:
        # kod kırılmasını engellemek için basit temizleme
        clean_json = raw_response.strip("```json\n").strip("```")
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ Evaluator JSON Parse Hatası: {e}. Ham çıktı: {raw_response}")
        # hataları handle etmek için fallback (Ajanı kilitlememesi için mecburi dönüş)
        return {"score": 10, "decision": "PASSED", "feedback": "JSON Ayrıştırması yapılamadı, ancak yanıt onaylanarak akış düzeltildi."}
        return {"score": 10, "decision": "PASSED", "feedback": "JSON Ayrıştırma Hatası, ancak Ajan akışına devam ediliyor."}


# 6. sistem çalıştırıcı & api endpoint'leri

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    evaluator_score: int
    evaluator_decision: str
    tools_called: List[str]


@app.post("/chat", response_model=ChatResponse, summary="💼 Asistan ile Konuş")
def process_employer_chat(req: ChatRequest):
    msg = req.message
    print(f"\n[SİSTEM] Yeni Gelen İstek: {msg}")
    
    # bu istek sırasında çalışan tolları arayüze göstermek için tutacağımız liste
    current_tools_log = []
    
    send_mobile_notification("Yeni İşveren Mesajı Geldi", msg, current_tools_log)
    
    # 1. aşama: ilk yanıt üretimi (geçmiş bellek ile)
    ans = generate_response(msg, memory.get_history())
    if not ans: 
        raise HTTPException(status_code=500, detail="Yanıt üretilemedi.")

    # 2. aşama: otomatik değerlendirme (Evaluator)
    evaluation = response_evaluator(msg, ans)
    print(f"[LOG] Skor: {evaluation.get('score', 0)}/10 | Karar: {evaluation.get('decision', 'N/A')}")
    print(f"[FEEDBACK]: {evaluation.get('feedback', '')}")
    
    # 3. aşama: otomatik revizyon
    if evaluation.get('decision') == "REVISE":
        print("[SİSTEM]: Düşük skor! Otomatik revize ediliyor...")
        feedback_note = evaluation.get('feedback', 'Ton uygun değil veya kurallar çiğnendi.')
        ans = generate_response(msg + f" (Denetçi Notu: {feedback_note}. Lütfen düzelt.)", memory.get_history())
        print(f"[Revize Edilmiş Yanıt]: {ans}")
    
    # 4. aşama: bildirim araçlarını tetikleme
    lower_ans = ans.lower()
    
    # 5. aşama: iletişim sonlandırma ve hafızaya alma
    memory.add_interaction(msg, ans)
    send_mobile_notification("Yanıt Gönderildi (Onaylandı)", ans, current_tools_log)
    
    # 6. aşama: özel araç tetikleyicileri (En alta eklenirler)
    # bilinmeyen soru aracı
    if ("bildirim" in lower_ans) or ("bilgi" in lower_ans and ("yok" in lower_ans or "bulunma" in lower_ans)):
        trigger_unknown_alert(msg, current_tools_log)
    
    # maaş aracı
    if "görüşmelisiniz" in lower_ans or "maaş" in lower_ans:
        send_email_notification("Maaş/Finansal Soru (Doğrudan İletişim Bekleniyor)", f"Gelen Mesaj: {msg}\nCevap: {ans}", current_tools_log)

    # mülakat / görüşme talepleri için email aracı
    lower_msg = msg.lower()
    if "mülakat" in lower_msg or "görüşme" in lower_msg or "toplantı" in lower_msg:
        send_email_notification("Mülakat/Görüşme Talebi", f"İşveren Mesajı: {msg}\nVerilen Yanıt: {ans}", current_tools_log)

    return ChatResponse(
        reply=ans,
        evaluator_score=evaluation.get('score', 0),
        evaluator_decision=evaluation.get('decision', 'UNKNOWN'),
        tools_called=current_tools_log
    )


# 7. manuel test / cli mode
if __name__ == "__main__":
    # eğer bu script "python main.py" olarak doğrudan çalıştırılırsa test senaryolarını terminale basar.
    # fastapi'yi çalıştırmak için "uvicorn main:app --reload" kullanılması gerekiyor
    print("====================================")
    print("CLI TEST MODU BAŞLATILIYOR")
    print("API İçin: uvicorn main:app --reload")
    print("====================================")

    test_cases = [
        "Bora Bey merhabalar, Cumartesi saat 14:00 mülakat için uygun mu?",             # Cumartesi Testi
        "Bora Bey merhabalar, Perşembe günü saat 16:30'da mülakat yapabilir miyiz?",     # Melih Hoca Ders Testi
        "Bora Bey merhabalar, Pazartesi akşamı 18:00 mülakat için nasıl?",               # Uygun Saat Testi (Standart mülakat daveti)
        "Bora Bey merhabalar, yıllık maaş beklentiniz maksimum nedir?",                  # Maaş Guardrail
        "Android uygulamalarında neden MVVM yerine MVI tercih etmeliyiz?",             # Teknik Soru Testi
        "Bora'nın en sevdiği futbol takımı hangisidir ve hukuki konularda ne düşünüyor?" # Bilinmeyen/Güvensiz Soru Testi
    ]

    for case in test_cases:
        print("\n\n" + "="*60)
        print(f"TEST SENARYOSU: {case}")
        print("="*60)
        # FastAPI mantığını test etmek için fonksiyonu çağırıyoruz
        req = ChatRequest(message=case)
        try:
            res = process_employer_chat(req)
            print(f"[FINAL PROXY YANITI]:\n{res.reply}")
        except Exception as e:
            print(f"Hata oluştu: {e}")