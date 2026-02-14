import time
import random
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from utils.db import (
    init_db,
    ensure_user,
    get_user,
    change_balance,
    transfer,
    claim_daily,
    set_dead,
    set_protect,
    set_last_daily,
    top_users,
    set_premium,
    is_premium,
)
import os


DAILY_AMOUNT = 500
REVIVE_COST = 200
PROTECT_COST = 200


def setup():
    init_db()
    # ensure owner is premium
    try:
        owner = int(os.environ.get("OWNER_ID", "0"))
        if owner:
            ensure_user(owner, None)
            set_premium(owner, True)
    except Exception:
        pass


async def ensure_called_user(update: Update):
    user = update.effective_user
    if user is None:
        return
    ensure_user(user.id, user.username)


async def cmd_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    user = update.effective_user
    if user is None:
        return
    row = get_user(user.id)
    now = int(time.time())
    # Claim daily atomically via DB helper. Premium users bypass cooldown (still credited).
    if is_premium(user.id):
        change_balance(user.id, DAILY_AMOUNT)
        await update.message.reply_text(f"You've received {DAILY_AMOUNT} RUPEES! 💵 (premium)")
        return
    ok = claim_daily(user.id, DAILY_AMOUNT, now)
    if not ok:
        await update.message.reply_text("You have already claimed daily. Come back later.")
        return
    await update.message.reply_text(f"You've received {DAILY_AMOUNT} RUPEES! 💵")


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    user = update.effective_user
    if user is None:
        return
    row = get_user(user.id)
    bal = row["balance"]
    await update.message.reply_text(f"{user.mention_html()} — Balance: {bal} RUPEES", parse_mode="HTML")


async def cmd_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    if update.message is None or update.message.reply_to_message is None:
        await update.message.reply_text("Reply to a user with /send <amount>")
        return
    try:
        amount = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /send <amount> (reply to user)")
        return
    sender = update.effective_user
    if sender is None:
        return
    if amount <= 0:
        await update.message.reply_text("Invalid amount")
        return
    ensure_user(sender.id, sender.username)
    recipient = update.message.reply_to_message.from_user
    ensure_user(recipient.id, recipient.username)
    ok = transfer(sender.id, recipient.id, amount)
    if not ok:
        await update.message.reply_text("Insufficient funds or transfer failed.")
        return
    await update.message.reply_text(f"Sent {amount} RUPEES to {recipient.mention_html()}", parse_mode="HTML")


async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = top_users(15)
    text = "🏆 Leaderboard\n"
    pos = 1
    for r in rows:
        uname = r["username"] or str(r["user_id"])
        text += f"{pos}. {uname} — {r['balance']} RUPEES\n"
        pos += 1
    await update.message.reply_text(text)


async def cmd_revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    user = update.effective_user
    if update.message is None:
        return
    if update.message.reply_to_message is None:
        await update.message.reply_text("Reply to the dead user with /revive to revive them (costs 200 RUPEES)")
        return
    target = update.message.reply_to_message.from_user
    ensure_user(user.id, user.username)
    ensure_user(target.id, target.username)
    sender_row = get_user(user.id)
    target_row = get_user(target.id)
    if not target_row["is_dead"]:
        await update.message.reply_text("Target is not dead.")
        return
    # Premium users don't pay revive cost
    if not is_premium(user.id):
        if sender_row["balance"] < REVIVE_COST:
            await update.message.reply_text("Not enough RUPEES to revive (200 required)")
            return
        change_balance(user.id, -REVIVE_COST)
    set_dead(target.id, False)
    await update.message.reply_text(f"{target.mention_html()} has been revived by {user.mention_html()}!", parse_mode="HTML")


async def cmd_dead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    if update.message is None or update.message.reply_to_message is None:
        await update.message.reply_text("Reply to a user with /dead to mark them dead.")
        return
    actor = update.effective_user
    target = update.message.reply_to_message.from_user
    ensure_user(actor.id, actor.username)
    ensure_user(target.id, target.username)
    actor_row = get_user(actor.id)
    # Dead users cannot kill others unless premium
    if actor_row["is_dead"] and not is_premium(actor.id):
        await update.message.reply_text("You are dead and cannot kill others.")
        return
    # Can't kill self
    if actor.id == target.id:
        await update.message.reply_text("You cannot kill yourself.")
        return
    # Protected?
    now = int(time.time())
    trow = get_user(target.id)
    # Protected users cannot be killed unless actor is premium
    if trow["protect_until"] and now < trow["protect_until"] and not is_premium(actor.id):
        await update.message.reply_text("Target is protected and cannot be killed now.")
        return
    set_dead(target.id, True)
    await update.message.reply_text(f"💀 {target.mention_html()} is now dead (killed by {actor.mention_html()})", parse_mode="HTML")


async def cmd_protectme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    user = update.effective_user
    if user is None:
        return
    ensure_user(user.id, user.username)
    row = get_user(user.id)
    # Premium users get protection for free
    if not is_premium(user.id):
        if row["balance"] < PROTECT_COST:
            await update.message.reply_text("Not enough RUPEES to buy protection.")
            return
        change_balance(user.id, -PROTECT_COST)
    until = int(time.time()) + 24 * 3600
    set_protect(user.id, until)
    await update.message.reply_text("Protection activated for 24 hours. Others cannot kill or steal from you.")


async def cmd_steal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    if update.message is None or update.message.reply_to_message is None:
        await update.message.reply_text("Reply to a user with /steal to attempt a robbery")
        return
    thief = update.effective_user
    target = update.message.reply_to_message.from_user
    ensure_user(thief.id, thief.username)
    ensure_user(target.id, target.username)
    thief_row = get_user(thief.id)
    if thief_row["is_dead"] and not is_premium(thief.id):
        await update.message.reply_text("Dead users cannot steal.")
        return
    target_row = get_user(target.id)
    now = int(time.time())
    if target_row["protect_until"] and now < target_row["protect_until"] and not is_premium(thief.id):
        await update.message.reply_text("Target is protected. Steal failed.")
        return
    amount = max(1, int(target_row["balance"] * random.uniform(0.05, 0.3)))
    if amount <= 0:
        await update.message.reply_text("Target has nothing to steal.")
        return
    # success chance
    if random.random() < 0.5:
        ok = transfer(target.id, thief.id, amount)
        if ok:
            await update.message.reply_text(f"You stole {amount} RUPEES from {target.mention_html()}!", parse_mode="HTML")
        else:
            await update.message.reply_text("Steal failed (target may have insufficient funds).")
    else:
        await update.message.reply_text("Steal attempt failed and you got nothing.")


async def cmd_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    user = update.effective_user
    if user is None or update.message is None:
        return
    try:
        bet = int(context.args[0])
    except Exception:
        await update.message.reply_text("Usage: /slots <bet_amount>")
        return
    ensure_user(user.id, user.username)
    row = get_user(user.id)
    if bet <= 0 or row["balance"] < bet:
        await update.message.reply_text("Invalid bet or insufficient funds.")
        return
    change_balance(user.id, -bet)
    reels = [random.choice(["🍒", "🍋", "🔔", "⭐", "7️⃣"]) for _ in range(3)]
    text = " | ".join(reels)
    # win conditions
    if reels[0] == reels[1] == reels[2]:
        win = bet * 5
        change_balance(user.id, win)
        await update.message.reply_text(f"{text}\nJackpot! You won {win} RUPEES")
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        win = bet * 2
        change_balance(user.id, win)
        await update.message.reply_text(f"{text}\nYou won {win} RUPEES")
    else:
        await update.message.reply_text(f"{text}\nYou lost {bet} RUPEES")
