"""
Chạy file này 1 LẦN DUY NHẤT trên máy local để lấy SESSION_STRING
Sau đó dán vào Railway environment variables
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID   = int(input("Nhập API_ID: "))
API_HASH = input("Nhập API_HASH: ")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("\n✅ SESSION_STRING của bạn:")
    print(client.session.save())
    print("\nDán chuỗi trên vào Railway > Variables > SESSION_STRING")
