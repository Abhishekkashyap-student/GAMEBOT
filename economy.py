import time
import random
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.firebase_db import (
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
        new_balance = get_user(user.id)["balance"]
        await update.message.reply_text(
            f"💰 Daily Claim Successful (Premium)!\n"
            f"✨ +{DAILY_AMOUNT} ₹ (No cooldown)\n"
            f"💼 Your NEW Balance: {new_balance} ₹"
        )
        return
    ok = claim_daily(user.id, DAILY_AMOUNT, now)
    if not ok:
        await update.message.reply_text("⏰ You have already claimed daily. Come back in 24 hours!")
        return
    new_balance = get_user(user.id)["balance"]
    await update.message.reply_text(
        f"💰 Daily Claim Successful!\n"
        f"✨ +{DAILY_AMOUNT} ₹\n"
        f"💼 Your NEW Balance: {new_balance} ₹"
    )


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    user = update.effective_user
    if user is None:
        return
    row = get_user(user.id)
    if row is None:
        await update.message.reply_text("❌ User not found in database")
        return
    bal = row["balance"]
    dead_status = "💀 DEAD" if row["is_dead"] else "✅ ALIVE"
    premium_tag = "👑 PREMIUM" if row["is_premium"] else "⭕ REGULAR"
    await update.message.reply_text(
        f"👤 {user.mention_html()}\n"
        f"💼 Balance: <b>{bal} ₹</b>\n"
        f"Status: {dead_status} | {premium_tag}\n"
        f"🆔 ID: {user.id}",
        parse_mode="HTML"
    )


async def cmd_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    if update.message is None or update.message.reply_to_message is None:
        await update.message.reply_text(
            "💸 TRANSFER COINS 💸\n\n"
            "Usage: Reply to a user + /send <amount>\n"
            "Example: (reply to user) /send 100"
        )
        return
    try:
        amount = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text("💸 Usage: /send <amount> (reply to user)")
        return
    sender = update.effective_user
    if sender is None:
        return
    if amount <= 0:
        await update.message.reply_text("❌ Amount must be greater than 0!")
        return
    ensure_user(sender.id, sender.username)
    recipient = update.message.reply_to_message.from_user
    ensure_user(recipient.id, recipient.username)

    sender_row = get_user(sender.id)
    if sender_row["balance"] < amount:
        await update.message.reply_text(
            f"❌ Insufficient balance!\n"
            f"You have: {sender_row['balance']} ₹\n"
            f"Transfer amount: {amount} ₹"
        )
        return

    ok = transfer(sender.id, recipient.id, amount)
    if not ok:
        await update.message.reply_text("❌ Transfer failed. Try again.")
        return

    sender_new_balance = get_user(sender.id)["balance"]
    recipient_new_balance = get_user(recipient.id)["balance"]

    await update.message.reply_text(
        f"💳 TRANSFER SUCCESSFUL! 💳\n"
        f"👤 From: {sender.mention_html()}\n"
        f"👤 To: {recipient.mention_html()}\n"
        f"💰 Amount: {amount} ₹\n\n"
        f"📊 Your balance: {sender_row['balance']} ₹ → <b>{sender_new_balance} ₹</b>\n"
        f"📊 Recipient balance: {recipient_new_balance} ₹",
        parse_mode="HTML"
    )


async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = top_users(15)
    if not rows:
        await update.message.reply_text("📊 No users in database yet. Play /daily to start!")
        return
    # Build inline keyboard: each user is a button that opens a profile callback
    keyboard = []
    text = "🏆 TOP 15 RICHEST PLAYERS 🏆\n" + "=" * 55 + "\n\n"
    pos = 1
    for r in rows:
        username = r["username"] if r["username"] else f"anonyme_user_{r['user_id']}"
        balance = r["balance"]
        is_dead = "💀" if r["is_dead"] else "✅"
        is_premium = "👑" if r["is_premium"] else ""
        medal = "🥇" if pos == 1 else "🥈" if pos == 2 else "🥉" if pos == 3 else ""

        line = f"{medal} #{pos} — {username} — {balance} ₹ {is_dead} {is_premium}"
        # add a button per user to view profile
        keyboard.append([InlineKeyboardButton(text=line, callback_data=f"profile:{r['user_id']}")])
        pos += 1

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def callback_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    data = query.data or ""
    if not data.startswith("profile:"):
        return
    try:
        user_id = int(data.split(":", 1)[1])
    except Exception:
        await query.answer("Invalid user id", show_alert=True)
        return
    user = get_user(user_id)
    if not user:
        await query.answer("User not found", show_alert=True)
        return
    username = user.get("username") or f"anonyme_user_{user_id}"
    bal = user.get("balance", 0)
    dead_status = "💀 DEAD" if user.get("is_dead") else "✅ ALIVE"
    premium_tag = "👑 PREMIUM" if user.get("is_premium") else "⭕ REGULAR"

    text = (
        f"👤 <b>{username}</b>\n"
        f"🆔 ID: {user_id}\n"
        f"💼 Balance: <b>{bal} ₹</b>\n"
        f"Status: {dead_status} | {premium_tag}"
    )

    # Answer callback with a modal alert containing profile info
    await query.answer(text, show_alert=True)


async def cmd_revive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    user = update.effective_user
    if update.message is None:
        return
    if update.message.reply_to_message is None:
        await update.message.reply_text("💊 Usage: Reply to the dead user with /revive to revive them (costs 200 ₹)")
        return
    target = update.message.reply_to_message.from_user
    ensure_user(user.id, user.username)
    ensure_user(target.id, target.username)
    sender_row = get_user(user.id)
    target_row = get_user(target.id)
    if not target_row["is_dead"]:
        await update.message.reply_text("❌ Target is not dead.")
        return
    # Premium users don't pay revive cost
    if not is_premium(user.id):
        if sender_row["balance"] < REVIVE_COST:
            await update.message.reply_text(f"❌ Not enough ₹ to revive (200 ₹ required)")
            return
        change_balance(user.id, -REVIVE_COST)
    set_dead(target.id, False)
    reviver_balance = get_user(user.id)["balance"]
    await update.message.reply_text(
        f"💊 REVIVE SUCCESSFUL! 💊\n"
        f"👤 Reviver: {user.mention_html()} (@{user.username})\n"
        f"🆙 Revived: {target.mention_html()} (@{target.username})\n"
        f"💳 Cost: -{REVIVE_COST} ₹\n"
        f"💼 Your NEW Balance: {reviver_balance} ₹",
        parse_mode="HTML"
    )


async def cmd_dead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    if update.message is None or update.message.reply_to_message is None:
        await update.message.reply_text("💀 Usage: Reply to a user with /dead to mark them dead.")
        return
    actor = update.effective_user
    target = update.message.reply_to_message.from_user
    ensure_user(actor.id, actor.username)
    ensure_user(target.id, target.username)
    actor_row = get_user(actor.id)
    # Dead users cannot kill others unless premium
    if actor_row["is_dead"] and not is_premium(actor.id):
        await update.message.reply_text("💀 You are dead and cannot kill others.")
        return
    # Can't kill self
    if actor.id == target.id:
        await update.message.reply_text("🚫 You cannot kill yourself.")
        return
    # Protected?
    now = int(time.time())
    trow = get_user(target.id)
    # Protected users cannot be killed unless actor is premium
    if trow["protect_until"] and now < trow["protect_until"] and not is_premium(actor.id):
        await update.message.reply_text("🛡️ Target is protected and cannot be killed now.")
        return
    set_dead(target.id, True)
    await update.message.reply_text(
        f"⚰️ DEAD! ⚰️\n"
        f"👤 Killer: {actor.mention_html()} (@{actor.username})\n"
        f"💀 Victim: {target.mention_html()} (@{target.username})\n"
        f"Status: DEAD - Cannot perform actions until revived!",
        parse_mode="HTML"
    )


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
            await update.message.reply_text(f"❌ Not enough ₹ to buy protection (200 ₹ required)")
            return
        change_balance(user.id, -PROTECT_COST)
    until = int(time.time()) + 24 * 3600
    set_protect(user.id, until)
    new_balance = get_user(user.id)["balance"]
    await update.message.reply_text(
        f"🛡️ PROTECTION ACTIVATED! 🛡️\n"
        f"⏱️ Duration: 24 hours\n"
        f"✅ You are now PROTECTED!\n"
        f"❌ Others cannot kill or steal from you\n"
        f"💳 Cost: -{PROTECT_COST} ₹\n"
        f"💼 Your NEW Balance: {new_balance} ₹"
    )


async def cmd_steal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    if update.message is None or update.message.reply_to_message is None:
        await update.message.reply_text("💰 Usage: Reply to a user with /steal to attempt a robbery")
        return
    thief = update.effective_user
    target = update.message.reply_to_message.from_user
    ensure_user(thief.id, thief.username)
    ensure_user(target.id, target.username)
    thief_row = get_user(thief.id)
    if thief_row["is_dead"] and not is_premium(thief.id):
        await update.message.reply_text("💀 Dead users cannot steal.")
        return
    target_row = get_user(target.id)
    now = int(time.time())
    if target_row["protect_until"] and now < target_row["protect_until"] and not is_premium(thief.id):
        await update.message.reply_text("🛡️ Target is protected. Steal failed.")
        return
    amount = max(1, int(target_row["balance"] * random.uniform(0.05, 0.3)))
    if amount <= 0:
        await update.message.reply_text("💸 Target has nothing to steal.")
        return
    # success chance
    if random.random() < 0.5:
        ok = transfer(target.id, thief.id, amount)
        if ok:
            thief_new_balance = get_user(thief.id)["balance"]
            target_new_balance = get_user(target.id)["balance"]
            await update.message.reply_text(
                f"🤑 ROB SUCCESSFUL! 🤑\n"
                f"👤 Thief: {thief.mention_html()} (@{thief.username})\n"
                f"🎯 Victim: {target.mention_html()} (@{target.username})\n"
                f"💰 Stolen: +{amount} ₹\n"
                f"💼 Your NEW Balance: {thief_new_balance} ₹\n"
                f"🏦 Victim Balance: {target_new_balance} ₹",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ Steal failed (target may have insufficient funds).")
    else:
        await update.message.reply_text("❌ Steal attempt failed! The target caught you red-handed!")


async def cmd_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ensure_called_user(update)
    user = update.effective_user
    if user is None or update.message is None:
        return
    try:
        bet = int(context.args[0])
    except (IndexError, ValueError):
        await update.message.reply_text(
            "🎰 SLOTS GAME 🎰\n\n"
            "Usage: /slots <bet_amount>\n"
            "Example: /slots 50\n\n"
            "🎁 Prizes:\n"
            "🎉 All Match = 5x win!\n"
            "🥳 Two Match = 2x win!\n"
            "😢 No Match = Lose bet\n\n"
            "Emojis: 🍒 🍋 🔔 ⭐ 7️⃣"
        )
        return
    ensure_user(user.id, user.username)
    row = get_user(user.id)

    # Validation
    if bet <= 0:
        await update.message.reply_text("❌ Bet must be greater than 0!")
        return
    if bet > 10000:
        await update.message.reply_text("❌ Maximum bet is 10000 ₹!")
        return
    if row["balance"] < bet:
        await update.message.reply_text(
            f"❌ Insufficient balance!\n"
            f"You have: {row['balance']} ₹\n"
            f"Bet required: {bet} ₹\n"
            f"Use /daily to earn more ₹"
        )
        return

    # Emoji effect before bet
    await update.message.reply_text(
        f"🎰 Betting {bet} ₹...\n"
        f"⏳ Spinning the reels... 🎯"
    )

    # Deduct bet
    change_balance(user.id, -bet)

    # Spin reels
    reels = [random.choice(["🍒", "🍋", "🔔", "⭐", "7️⃣"]) for _ in range(3)]
    text = " | ".join(reels)
    new_balance = get_user(user.id)["balance"]

    # Check win conditions
    if reels[0] == reels[1] == reels[2]:
        win = bet * 5
        change_balance(user.id, win)
        new_balance = get_user(user.id)["balance"]
        await update.message.reply_text(
            f"🎰 {text} 🎰\n\n"
            f"🎉🎉🎉 JACKPOT! 🎉🎉🎉\n"
            f"✨ You won {win} ₹ (5x multiplier)!\n"
            f"💼 Previous Balance: {new_balance - win} ₹\n"
            f"💰 NEW Balance: <b>{new_balance} ₹</b>\n"
            f"📈 Profit: +{win - bet} ₹",
            parse_mode="HTML"
        )
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        win = bet * 2
        change_balance(user.id, win)
        new_balance = get_user(user.id)["balance"]
        await update.message.reply_text(
            f"🎰 {text} 🎰\n\n"
            f"🥳 YOU WON! 🥳\n"
            f"✨ You won {win} ₹ (2x multiplier)!\n"
            f"💼 Previous Balance: {new_balance - win} ₹\n"
            f"💰 NEW Balance: <b>{new_balance} ₹</b>\n"
            f"📈 Profit: +{win - bet} ₹",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            f"🎰 {text} 🎰\n\n"
            f"😢 You lost!\n"
            f"❌ Bet lost: {bet} ₹\n"
            f"💼 Previous Balance: {new_balance + bet} ₹\n"
            f"💰 NEW Balance: <b>{new_balance} ₹</b>\n"
            f"📉 Loss: -{bet} ₹\n\n"
            f"💡 Try /daily to earn more coins!",
            parse_mode="HTML"
        )


async def cmd_kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kill a user and get 90-150 rupees reward"""
    await ensure_called_user(update)
    if update.message is None or update.message.reply_to_message is None:
        await update.message.reply_text("💀 Usage: Reply to a user with /kill")
        return
    actor = update.effective_user
    target = update.message.reply_to_message.from_user
    ensure_user(actor.id, actor.username)
    ensure_user(target.id, target.username)
    actor_row = get_user(actor.id)
    # Dead users cannot kill others unless premium
    if actor_row["is_dead"] and not is_premium(actor.id):
        await update.message.reply_text("💀 You are dead and cannot kill others.")
        return
    # Can't kill self
    if actor.id == target.id:
        await update.message.reply_text("🚫 You cannot kill yourself.")
        return
    # Protected?
    now = int(time.time())
    trow = get_user(target.id)
    # Protected users cannot be killed unless actor is premium
    if trow["protect_until"] and now < trow["protect_until"] and not is_premium(actor.id):
        await update.message.reply_text("🛡️ Target is protected and cannot be killed now.")
        return
    set_dead(target.id, True)
    # Reward killer with 90-150 rupees
    reward = random.randint(90, 150)
    change_balance(actor.id, reward)
    killer_balance = get_user(actor.id)["balance"]
    await update.message.reply_text(
        f"💀 KILL SUCCESSFUL! 💀\n"
        f"👤 Killer: {actor.mention_html()} (@{actor.username})\n"
        f"🎯 Target: {target.mention_html()} (@{target.username})\n"
        f"💰 Reward: +{reward} ₹\n"
        f"💼 Your NEW Balance: {killer_balance} ₹",
        parse_mode="HTML"
    )


async def cmd_rob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for /steal command"""
    await cmd_steal(update, context)
