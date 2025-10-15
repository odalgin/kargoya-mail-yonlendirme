import re
import base64
import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import smtplib
from google.auth.transport.requests import Request
# ========================
# AYARLAR
# ========================
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = "token.pickle" # credentials.json dosyasınızı oluşturduktan sonra kodu çalıştırdığınızda oluşturulacaktır.
CREDENTIALS_PATH = "credentials.json"
LAST_ORDER_FILE = "last_order.txt"

KARGO_MAIL = ""   # Kargo ekibinin mail adresi
GONDEREN_MAIL = ""  # Gönderen mail adresin (SMTP için de kullanılacak)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "" # Gönderen mail adresin
SMTP_PASS = ""  # Gmail uygulama şifresi kullanılmalı


# ========================
# AUTH
# ========================
def gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # Eğer token geçersizse yenilemeye çalış
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, SCOPES
        )
        creds = flow.run_local_server(
            port=0, access_type="offline", include_granted_scopes="true"
        )

    # Token’ı kaydet
    with open(TOKEN_PATH, "wb") as token:
        pickle.dump(creds, token)

    return build("gmail", "v1", credentials=creds)

# ========================
# FONKSİYONLAR
# ========================
def temizle_tutarlar(html_body: str) -> str:
    # ₺ işaretiyle başlayan bütün sayıları sil
    return re.sub(r"₺\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?", "", html_body)


def get_last_order_id():
    if os.path.exists(LAST_ORDER_FILE):
        with open(LAST_ORDER_FILE, "r") as f:
            return int(f.read().strip())
    return 0


def save_last_order_id(order_id: int):
    with open(LAST_ORDER_FILE, "w") as f:
        f.write(str(order_id))


def get_recent_orders(max_results=20):
    service = gmail_service()
    results = service.users().messages().list(
        userId="me", maxResults=max_results, q="subject:'Yeni sipariş'"
    ).execute()
    return results.get("messages", [])


def extract_order_details(message, service):
    msg = service.users().messages().get(userId="me", id=message["id"], format="full").execute()
    headers = msg["payload"]["headers"]
    subject = next(h["value"] for h in headers if h["name"] == "Subject")

    body = ""
    if "parts" in msg["payload"]:
        for part in msg["payload"]["parts"]:
            if part["mimeType"] == "text/html":
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                break
    else:
        body = base64.urlsafe_b64decode(msg["payload"]["body"]["data"]).decode("utf-8")

    match = re.search(r"#(\d+)", subject)
    order_id = int(match.group(1)) if match else None

    return subject, body, order_id


def send_mail(to, subject, html_content):
    msg = MIMEText(html_content, "html")
    msg["Subject"] = subject
    msg["From"] = GONDEREN_MAIL
    msg["To"] = to

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(GONDEREN_MAIL, [to], msg.as_string())


# ========================
# MAIN
# ========================
def main():
    service = gmail_service()
    last_order = get_last_order_id()
    print(f"Son kaydedilen sipariş: #{last_order}")

    messages = get_recent_orders(20)
    if not messages:
        print("Yeni sipariş bulunamadı.")
        return

    # Eski → yeni sıralama için ters çeviriyoruz
    messages = list(reversed(messages))

    latest_id = last_order
    for msg in messages:
        subject, body, order_id = extract_order_details(msg, service)
        if not order_id:
            continue

        if order_id > last_order:
            print(f"Yeni sipariş bulundu: #{order_id}")
            temiz_body = temizle_tutarlar(body)
            send_mail(KARGO_MAIL, subject, temiz_body)
            latest_id = order_id
            print(f"Mail gönderildi: #{order_id}")

    if latest_id > last_order:
        save_last_order_id(latest_id)
        print(f"Son sipariş güncellendi: #{latest_id}")
    else:
        print("Yeni sipariş yok.")


if __name__ == "__main__":

    main()
