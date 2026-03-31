"""
Admin Notify Bot - Telethon Userbot (Railway)
Theo dõi group Telegram và forward tin nhắn của admin sang Saved Messages
"""

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import ChannelParticipantsAdmins
import asyncio
import logging
import os

# ============================================================
# CẤU HÌNH QUA ENVIRONMENT VARIABLES (Railway)
# ============================================================

API_ID       = int(os.environ["API_ID"])
API_HASH     = os.environ["API_HASH"]
SESSION      = os.environ["SESSION_STRING"]   # Lấy bằng gen_session.py
TARGET_GROUP      = os.environ["TARGET_GROUP"]      # username hoặc group ID (số)
FORWARD_TO        = os.environ.get("FORWARD_TO", "me")
LINKED_CHANNEL_ID = int(os.environ.get("LINKED_CHANNEL_ID", "0"))  # Channel liên kết với group (nếu có)

# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

admin_ids: set = set()
target_group_id: int = None
linked_channel_id: int = None


async def refresh_admins():
    """Lấy danh sách admin của group"""
    global admin_ids
    try:
        admins = await client.get_participants(target_group_id, filter=ChannelParticipantsAdmins())
        admin_ids = {a.id for a in admins}
        log.info(f"✅ Đã tải {len(admin_ids)} admin")
    except Exception as e:
        log.error(f"❌ Không lấy được danh sách admin: {e}")


async def auto_refresh_admins(interval_minutes=30):
    while True:
        await asyncio.sleep(interval_minutes * 60)
        await refresh_admins()


async def on_new_message(event):
    chat_id = event.chat_id
    sender_id = event.sender_id

    # Tin nhắn từ channel liên kết → forward hết (đây là bài đăng chính thức của admin)
    if linked_channel_id and chat_id == linked_channel_id:
        pass  # cho qua, xử lý bên dưới
    elif chat_id == target_group_id:
        # Tin nhắn trong group → chỉ forward nếu sender là admin
        if sender_id is None or sender_id not in admin_ids:
            return
    else:
        return

    try:
        sender = await event.get_sender()
        if sender:
            name = getattr(sender, "first_name", "") or getattr(sender, "title", "Admin")
            username = f"@{sender.username}" if getattr(sender, "username", None) else ""
        else:
            name = "Admin"
            username = ""

        chat = await event.get_chat()
        group_title = getattr(chat, "title", "Group")
        header = f"🔔 **[Admin {name} {username}]**\n📢 **{group_title}**\n{'─'*28}\n"
        text = event.message.message or ""

        if event.message.media:
            await client.forward_messages(FORWARD_TO, event.message)
            if text:
                await client.send_message(FORWARD_TO, header + text)
        else:
            await client.send_message(FORWARD_TO, header + text)

        log.info(f"📨 Forwarded from {name} ({sender_id}) | chat_id={chat_id}")
    except Exception as e:
        log.error(f"❌ Lỗi: {e}")


async def main():
    global target_group_id, linked_channel_id

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

    await refresh_admins()

    # Xác định channel liên kết
    chats_to_watch = [target_group_id]
    if LINKED_CHANNEL_ID:
        linked_channel_id = LINKED_CHANNEL_ID
        chats_to_watch.append(linked_channel_id)
        log.info(f"🔗 Theo dõi thêm linked channel: {linked_channel_id}")
    else:
        # Tự động phát hiện linked channel từ full_chat
        try:
            from telethon.tl.functions.channels import GetFullChannelRequest
            full = await client(GetFullChannelRequest(entity))
            lc = getattr(full.full_chat, "linked_chat_id", None)
            if lc:
                linked_channel_id = lc
                chats_to_watch.append(linked_channel_id)
                log.info(f"🔗 Tự động phát hiện linked channel: {linked_channel_id}")
        except Exception as e:
            log.warning(f"⚠️ Không phát hiện được linked channel: {e}")

    client.add_event_handler(on_new_message, events.NewMessage(chats=chats_to_watch))

    asyncio.create_task(auto_refresh_admins(30))

    log.info(f"👀 Đang theo dõi {chats_to_watch}... Forward sang: {FORWARD_TO}")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
