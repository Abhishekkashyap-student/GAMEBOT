import os
from telegram import Update
from telegram.ext import ContextTypes

from utils.db import ensure_user, change_balance, set_premium, get_user


def _is_owner(user_id: int) -> bool:
    try:
        owner = int(os.environ.get("OWNER_ID", "0"))
    except Exception:
        return False
    return user_id == owner


async def cmd_grant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        return
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Owner-only command.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /grant <amount> (reply to user)")
        return
    if update.message.reply_to_message is None:
        await update.message.reply_text("Reply to a user to grant them coins.")
        return
    try:
        amount = int(context.args[0])
    except Exception:
        await update.message.reply_text("Invalid amount")
        return
    target = update.message.reply_to_message.from_user
    ensure_user(target.id, target.username)
    change_balance(target.id, amount)
    await update.message.reply_text(f"Granted {amount} RUPEES to {target.mention_html()}", parse_mode="HTML")


async def cmd_setpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        return
    if not _is_owner(update.effective_user.id):
        await update.message.reply_text("Owner-only command.")
        return
    # target via reply or arg
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        # first arg could be user id
        try:
            uid = int(context.args[0])
            target = type(update.effective_user)(id=uid)
        except Exception:
            await update.message.reply_text("Reply to a user or provide user id.")
            return
    else:
        await update.message.reply_text("Reply to a user with /setpremium <on|off>")
        return
    flag = (context.args[-1].lower() if context.args else "on")
    val = flag in ("on", "1", "true", "yes")
    ensure_user(target.id, getattr(target, "username", None))
    set_premium(target.id, val)
    await update.message.reply_text(f"Set premium={val} for {get_user(target.id)['username']}")
