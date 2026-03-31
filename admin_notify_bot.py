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

admin_ids: set = set()
target_group_id: int = None


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
    if event.chat_id != target_group_id:
        return

    sender_id = event.sender_id
    if sender_id is None or sender_id not in admin_ids:
        return

    try:
        sender = await event.get_sender()
        name = getattr(sender, "first_name", "") or getattr(sender, "title", "Admin")
        username = f"@{sender.username}" if getattr(sender, "username", None) else ""
        group_title = (await event.get_chat()).title
        header = f"🔔 **[Admin {name} {username}]**\n📢 **{group_title}**\n{'─'*28}\n"
        text = event.message.message or ""

        if event.message.media:
            await client.forward_messages(FORWARD_TO, event.message)
            if text:
                await client.send_message(FORWARD_TO, header + text)
        else:
            await client.send_message(FORWARD_TO, header + text)

        log.info(f"📨 Forwarded from {name} ({sender_id})")
    except Exception as e:
        log.error(f"❌ Lỗi: {e}")


async def main():
    global target_group_id

    log.info("🚀 Khởi động Admin Notify Bot...")
    await client.start()
    log.info("✅ Đã đăng nhập")

    try:
        # Nếu TARGET_GROUP là số nguyên (group ID)
        group_id = int(TARGET_GROUP)
        entity = await client.get_entity(group_id)
    except ValueError:
        entity = await client.get_entity(TARGET_GROUP)

    target_group_id = entity.id
    log.info(f"✅ Group: {entity.title} (ID: {target_group_id})")

    await refresh_admins()

    client.add_event_handler(on_new_message, events.NewMessage(chats=target_group_id))

    asyncio.create_task(auto_refresh_admins(30))

    log.info(f"👀 Đang theo dõi... Forward sang: {FORWARD_TO}")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
