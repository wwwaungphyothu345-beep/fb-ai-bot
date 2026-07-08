from flask import Flask, request, jsonify, Response
import requests
import json
import os

app = Flask(__name__)

# API Keys
GEMINI_KEY = os.environ.get("GEMINI_KEY")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN",  "aung_phyo_thu_12")

# AI ကို စျေးရောင်းခိုင်းမယ့် လမ်းညွှန်ချက် (System Instruction)
system_instruction = """
မင်းက အွန်လိုင်းရှော့ပင်းတစ်ခုက တကယ့်လူသား အရောင်းဝန်ထမ်းတစ်ယောက် ဖြစ်တယ်။ 
ယဉ်ကျေးပျူငှါစွာ ပြောဆိုပါ။ မြန်မာလိုပဲ ပြန်ဖြေပါ။
ကိုယ့်ဆိုင်မှာ ရောင်းတဲ့ပစ္စည်းစာရင်း:
- အင်္ကျီ (စျေး: ၁၅,၀၀၀ ကျပ်၊ အရောင်: အနက်၊ အဖြူ)
- ဘောင်းဘီ (စျေး: ၂၀,၀၀၀ ကျပ်၊ အရောင်: ဂျင်းပြာ)
စျေးနှုန်းနဲ့ အရောင်ကို မေးရင် အတိအကျဖြေပါ။ ပစ္စည်းမှာချင်ရင် လိပ်စာနဲ့ ဖုန်းနံပါတ် တောင်းပါ။
"""

def ask_gemini(user_message):
    # grpcio မလိုဘဲ HTTP API ကနေ Gemini ဆီ တိုက်ရိုက်မေးတဲ့အပိုင်း
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": user_message}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        res_json = response.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("Error calling Gemini:", e)
        return "ခဏလေး စောင့်ပေးပါဗျာ။"

@app.route('/', methods=['GET'])
def index():
    return "Facebook AI Bot is Running!"

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403
    return "Hello World", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message") and messaging_event["message"].get("text"):
                    sender_id = messaging_event["sender"]["id"]
                    user_message = messaging_event["message"]["text"]
                    
                    # Gemini AI ဆီ စာပို့ပြီး အဖြေတောင်းခြင်း
                    bot_reply = ask_gemini(user_message)
                    
                    # AI အဖြေကို Messenger API သုံးပြီး Customer ဆီ ပြန်ပို့ခြင်း
                    fb_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
                    payload = {
                        "recipient": {"id": sender_id},
                        "message": {"text": bot_reply}
                    }
                    requests.post(fb_url, json=payload)
                    
    return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
