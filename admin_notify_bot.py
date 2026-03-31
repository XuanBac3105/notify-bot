"""
Admin Notify Bot - Telethon Userbot (Railway)
Theo dõi group Telegram và forward tin nhắn của CHANNEL (không phải member thường)
"""

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat
import asyncio
import logging
import os

# ============================================================
# CẤU HÌNH QUA ENVIRONMENT VARIABLES (Railway)
# ============================================================

API_ID       = int(os.environ["API_ID"])
API_HASH     = os.environ["API_HASH"]
SESSION      = os.environ["SESSION_STRING"]   # Lấy bằng gen_session.py
TARGET_GROUP = os.environ["TARGET_GROUP"]     # username hoặc group ID (số)
FORWARD_TO   = os.environ.get("FORWARD_TO", "me")

# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

target_group_id: int | None = None


async def on_new_message(event):
    if event.chat_id != target_group_id:
        return

    # Chỉ lấy tin nhắn được gửi bởi Channel (bài đăng chính thức)
    # Bỏ qua tin nhắn của member thường (User)
    sender = await event.get_sender()
    if not isinstance(sender, (Channel, Chat)):
        return

    try:
        name = getattr(sender, "title", "Channel")
        username = f"@{sender.username}" if getattr(sender, "username", None) else ""
        header = f"📢 **{name}** {username}\n{'─'*28}\n"
        text = event.message.message or ""

        if event.message.media:
            await client.forward_messages(FORWARD_TO, event.message)
            if text:
                await client.send_message(FORWARD_TO, header + text)
        else:
            if text:
                await client.send_message(FORWARD_TO, header + text)

        log.info(f"📨 Forwarded from channel: {name} | sender_id={sender.id}")
    except Exception as e:
        log.error(f"❌ Lỗi: {e}")


async def main():
    global target_group_id

    log.info("🚀 Khởi động Admin Notify Bot...")
    await client.start()
    log.info("✅ Đã đăng nhập")

    try:
        group_id = int(TARGET_GROUP)
        entity = await client.get_entity(group_id)
    except ValueError:
        entity = await client.get_entity(TARGET_GROUP)

    target_group_id = entity.id
    log.info(f"✅ Group: {entity.title} (ID: {target_group_id})")

    client.add_event_handler(on_new_message, events.NewMessage(chats=target_group_id))

    log.info(f"👀 Đang theo dõi... Chỉ forward tin nhắn từ Channel → {FORWARD_TO}")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
