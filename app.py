from flask import Flask, request, jsonify, Response
import requests
import json
import os
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# API Keys & Credentials
GEMINI_KEY = os.environ.get("GEMINI_KEY")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_secret_token_123")

# Google Sheet အတွက် Render ကနေ JSON credentials လှမ်းဖတ်ခြင်း
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")

def save_to_sheet(user_id, message_text):
    try:
        if not GOOGLE_CREDENTIALS:
            return
        
        # Google Sheet ချိတ်ဆက်ခြင်း
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # ကိုယ့် Google Sheet နာမည် အတိအကျ ထည့်ပါ
        sheet = client.open_by_key("1CJf69o5Gp_oxtoE7tDog3KPov-ylC0jc67T4XTuFlxU").worksheet("Orders")
        
        # Sheet ထဲသို့ ဒေတာ အသစ် သွားရိုက်ထည့်ခြင်း (ဥပမာ- Customer ID နဲ့ သူပြောတဲ့စာ)
        sheet.append_row([user_id, message_text])
        print("Saved to Google Sheet successfully!")
    except Exception as e:
        print("Error saving to sheet:", e)

# ... (စောစောက ask_gemini, verify function တွေက အတူတူပါပဲ) ...

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message") and messaging_event["message"].get("text"):
                    sender_id = messaging_event["sender"]["id"]
                    user_message = messaging_event["message"]["text"]
                    
                    # 💡 ဒီနေရာမှာ Customer ဆီက စာလာတိုင်း Google Sheet ထဲ သွားသိမ်းခိုင်းလိုက်တာပါ
                    save_to_sheet(sender_id, user_message)
                    
                    bot_reply = ask_gemini(user_message)
                    
                    fb_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
                    payload = {
                        "recipient": {"id": sender_id},
                        "message": {"text": bot_reply}
                    }
                    requests.post(fb_url, json=payload)
                    
    return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
