import os
from telegram import Update
from telegram.ext import ContextTypes


async def is_owner(update: Update) -> bool:
    if update.effective_user is None:
        return False
    try:
        owner = int(os.environ.get("OWNER_ID", "0"))
    except Exception:
        return False
    return update.effective_user.id == owner


async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True if the caller is chat admin/creator. Falls back to True in private chats."""
    if update.effective_chat is None or update.effective_user is None:
        return False
    chat = update.effective_chat
    user = update.effective_user
    # For private chats, treat user as allowed
    if chat.type == "private":
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        status = member.status.lower()
        return status in ("administrator", "creator")
    except Exception:
        # If we cannot fetch, deny by default
        return False
