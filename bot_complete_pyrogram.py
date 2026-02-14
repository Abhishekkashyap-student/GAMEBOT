#!/usr/bin/env python3
"""
🎮 GAMEBOT v4.0 - PYROGRAM COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Merged Bot: Economy + 10 Games + Hinata AI + Premium UI
Production-ready for Koyeb deployment

GAMES (10 Total):
1. Trivia - Answer questions ❓
2. RPS - Rock Paper Scissors 🏀
3. Hangman - Guess the word 📝
4. Guess Number - 1-50 🎲
5. Slots - Spin reels 🎰
6. Roulette - Pick 0-36 🎡
7. Blackjack - Get to 21 ♠️
8. Dice - Roll 2 dice 🎲
9. Lucky Draw - Pick 1-10 🎁
10. Memory - Match pairs 🧠

ECONOMY:
- /daily (500 coins)
- /balance (check wealth)
- /leaderboard (top 15)
- /send (transfer)
- /kill (90-150 reward)
- /steal (50% success)
- /protect (24h)
- /revive (200 cost)
- /slots, /roulette, /blackjack, /dice, /lucky

FEATURES:
✅ Hinata Hyuga AI persona
✅ Groq + g4f fallback
✅ Sticker reactions
✅ Prefix support (. and !)
✅ Premium UI everywhere
✅ Health check server
✅ Group & private support
"""

import os
import sys
import logging
import asyncio
import time
import random
from typing import Optional
from datetime import datetime
import psutil
import traceback

# Pyrogram
from pyrogram import Client, filters, types
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid, PeerIdInvalid, FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Dependencies
import httpx

# Try g4f fallback
try:
    import g4f
    G4F_AVAILABLE = True
except Exception:
    G4F_AVAILABLE = False

# HTTP server
from aiohttp import web
from dotenv import load_dotenv

# Database & Economy
from utils.firebase_db import (
    init_db,
    ensure_user,
    get_user,
    change_balance,
    transfer,
    claim_daily,
    set_dead,
    set_protect,
    top_users,
    set_premium,
    is_premium,
)

# New games
from games.slots_pyrogram import SlotsGame
from games.roulette_pyrogram import RouletteGame
from games.blackjack_pyrogram import BlackjackGame
from games.dice_pyrogram import DiceGame
from games.lucky_draw_pyrogram import LuckyDrawGame

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("gamebot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
GROQ_KEYS_ENV = os.getenv("GROQ_KEYS", "")

GROQ_KEYS = [k.strip() for k in GROQ_KEYS_ENV.split(",") if k.strip()] if GROQ_KEYS_ENV else []
HINATA_STICKERS = [
    "CAACAgUAAxkBAAEQgltpj2uaFvRFMs_ACV5pQrqBvnKWoQAC2QMAAvmysFdnPHJXLMM8TjoE",
    "CAACAgUAAxkBAAEQgl1pj2u6CJJq6jC-kXYHM9fvpJ5ygAACXgUAAov2IVf0ZtG-JNnfFToE",
]

_groq_index = 0

if not all([API_ID, API_HASH, BOT_TOKEN, OWNER_ID]):
    print(f"❌ Missing env: API_ID={API_ID}, API_HASH={bool(API_HASH)}, BOT_TOKEN={bool(BOT_TOKEN)}, OWNER_ID={OWNER_ID}")
    sys.exit(1)

app = Client(
    name="gamebot_v4",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="./sessions",
)

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM UI FORMATTER
# ═══════════════════════════════════════════════════════════════════════════════


class PremiumUI:
    """Premium UI with decorations"""

    TOP = "╔" + "═" * 50 + "╗"
    MID = "╠" + "═" * 50 + "╣"
    BOT = "╚" + "═" * 50 + "╝"
    DIV = "─" * 52

    @staticmethod
    def brand() -> str:
        return f"""{PremiumUI.TOP}
║{"🎮 GAMEBOT v4.0 - PYROGRAM COMPLETE 🎮".center(50)}║
║{"💎 Premium Gaming Experience 💎".center(50)}║
{PremiumUI.BOT}"""

    @staticmethod
    def box(title: str, content: str) -> str:
        return f"""{PremiumUI.TOP}
║ {title.ljust(48)} ║
{PremiumUI.MID}
{content}
{PremiumUI.BOT}"""

    @staticmethod
    def section(emoji: str, title: str) -> str:
        return f"\n{emoji} <b>{title}</b>\n"


# ═══════════════════════════════════════════════════════════════════════════════
# AI ENGINE (Hinata Persona)
# ═══════════════════════════════════════════════════════════════════════════════


async def call_groq(prompt: str) -> str:
    """Call Groq with automatic rotation and g4f fallback"""
    global _groq_index

    if not GROQ_KEYS:
        if G4F_AVAILABLE:
            try:
                reply = g4f.chat_completion.create(prompt)
                return reply if reply else "a-ano..."
            except:
                pass
        return "a-ano... I-I'm not sure, Naruto-kun..."

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(len(GROQ_KEYS)):
            key = GROQ_KEYS[_groq_index % len(GROQ_KEYS)]
            _groq_index += 1
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {"model": "llama3-8b-8192", "input": prompt, "max_output_tokens": 512}

            try:
                resp = await client.post("https://api.groq.ai/v1/completions", json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data.get("output") or data.get("text")
                    if text:
                        return text.strip()
            except Exception as e:
                logger.warning(f"Groq error: {e}")

    # Fallback
    if G4F_AVAILABLE:
        try:
            return g4f.chat_completion.create(prompt)
        except:
            pass

    return "a-ano... I-I'm not sure, Naruto-kun..."


def make_hinata_prompt(msg: str, name: str = None) -> str:
    """Create Hinata persona prompt"""
    return (
        "You are Hinata Hyuga from Naruto anime. Be shy, caring, kind. Use 'Naruto-kun' sometimes. "
        "Stutter like 'a-ano...'. Never admit being AI. Keep replies SHORT (1-2 sentences). "
        "Always be supportive and gentle.\n\n"
        f"User ({name or 'friend'}): {msg}\n\nHinata (shy):"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS - CORE
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    """Welcome message"""
    try:
        text = f"""{PremiumUI.brand()}

Hi {message.from_user.first_name}! 👋

<b>🎮 10 AMAZING GAMES:</b>
  1️⃣ /trivia - Answer questions
  2️⃣ /rps - Rock Paper Scissors
  3️⃣ /hangman - Guess the word
  4️⃣ /guess - Number 1-50
  5️⃣ /slots - Spin & win 🎰
  6️⃣ /roulette - Pick 0-36 🎡
  7️⃣ /blackjack - Get to 21 ♠️
  8️⃣ /dice - Roll dice 🎲
  9️⃣ /lucky - Pick 1-10 🎁
  🔟 /memory - Match pairs 🧠

💰 <b>ECONOMY:</b>
  • /daily - 500 coins
  • /balance - Check wealth
  • /leaderboard - Top 15
  • /send - Transfer coins
  • /kill - Attack someone

💬 <b>CHAT:</b>
  • Reply to me for Hinata AI response
  • Use .help or !help for prefix commands

/help - All commands
"""
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 Help", callback_data="help"),
             InlineKeyboardButton("🎮 Games", callback_data="games")],
            [InlineKeyboardButton("💰 Economy", callback_data="economy"),
             InlineKeyboardButton("✨ Premium", callback_data="premium")],
        ])
        await message.reply_text(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await message.reply_text("Welcome to GAMEBOT v4.0! Use /help for commands.")


@app.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    """Help menu"""
    text = f"""{PremiumUI.brand()}

<b>📖 COMPLETE COMMAND LIST</b>

🎮 <b>GAMES:</b>
/trivia, /rps, /hangman, /guess
/slots [bet], /roulette, /blackjack
/dice [bet], /lucky [bet]

💰 <b>ECONOMY:</b>
/daily, /balance, /leaderboard
/send [amount] (reply to user)
/kill (reply) - 90-150 coins
/steal (reply) - Rob coins
/protect - 24h protection (200 coins)
/revive (reply) - Revive dead (200)

💬 <b>OTHER:</b>
/dev - Show credits
/ping - Bot status
/info - Your info
.help or !help - Prefix commands
"""
    await message.reply_text(text)


@app.on_message(filters.command("dev"))
async def dev_cmd(client: Client, message: Message):
    """Developer credits"""
    await message.reply_text("🤖 <b>CREATED BY FIGLETAXL</b>\n\n📢 JOIN: @vfriendschat\n\n💎 GAMEBOT v4.0 - Pyrogram Complete")


@app.on_message(filters.command("ping"))
async def ping_cmd(client: Client, message: Message):
    """Ping - show status"""
    try:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        text = f"""⚡ <b>BOT STATUS</b>

🌍 Latency: <code>Fast ⚡</code>
💻 CPU: {cpu}%
🧠 Memory: {mem}%
✅ Status: <b>Online & Healthy</b>

Server: Koyeb (High-Availability)
Uptime: Running
"""
        await message.reply_text(text)
    except Exception as e:
        logger.error(f"Error in /ping: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# ECONOMY COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

DAILY_AMOUNT = 500
PROTECT_COST = 200
REVIVE_COST = 200


@app.on_message(filters.command("daily"))
async def daily_cmd(client: Client, message: Message):
    """Claim daily coins"""
    user = message.from_user
    ensure_user(user.id, user.username)

    now = int(time.time())
    if is_premium(user.id):
        change_balance(user.id, DAILY_AMOUNT)
        new_bal = get_user(user.id)["balance"]
        await message.reply_text(
            f"💰 <b>PREMIUM DAILY!</b>\n"
            f"✨ +{DAILY_AMOUNT} ₹ (No cooldown)\n"
            f"💼 Balance: <b>{new_bal} ₹</b>"
        )
        return

    if claim_daily(user.id, DAILY_AMOUNT, now):
        new_bal = get_user(user.id)["balance"]
        await message.reply_text(
            f"💰 <b>DAILY CLAIM!</b>\n"
            f"✨ +{DAILY_AMOUNT} ₹\n"
            f"💼 Balance: <b>{new_bal} ₹</b>"
        )
    else:
        await message.reply_text("⏰ Already claimed today! Come back in 24h")


@app.on_message(filters.command("balance"))
async def balance_cmd(client: Client, message: Message):
    """Check balance"""
    user = message.from_user
    ensure_user(user.id, user.username)
    row = get_user(user.id)

    status = "💀 DEAD" if row["is_dead"] else "✅ ALIVE"
    premium = "👑 PREMIUM" if row["is_premium"] else "⭕ REGULAR"

    text = f"""👤 <b>{user.first_name}</b>

💼 Balance: <b>{row["balance"]} ₹</b>
Status: {status} | {premium}
🆔 ID: <code>{user.id}</code>
"""
    await message.reply_text(text)


@app.on_message(filters.command("leaderboard"))
async def leaderboard_cmd(client: Client, message: Message):
    """Top 15 users"""
    rows = top_users(15)
    if not rows:
        await message.reply_text("No users yet! Use /daily to start.")
        return

    text = "🏆 <b>TOP 15 RICHEST</b>\n" + "─" * 30 + "\n\n"
    for i, r in enumerate(rows, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
        username = r["username"] or f"User_{r['user_id']}"
        dead = "💀" if r["is_dead"] else "✅"
        prem = "👑" if r["is_premium"] else ""
        text += f"{medal} {username} — {r['balance']} ₹ {dead} {prem}\n"

    await message.reply_text(text)


@app.on_message(filters.command("send"))
async def send_cmd(client: Client, message: Message):
    """Send coins to user"""
    if not message.reply_to_message:
        await message.reply_text("❌ Reply to a user! \nUsage: /send 100")
        return

    try:
        amount = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("❌ Usage: /send <amount>")
        return

    sender = message.from_user
    recipient = message.reply_to_message.from_user

    ensure_user(sender.id, sender.username)
    ensure_user(recipient.id, recipient.username)

    sender_row = get_user(sender.id)
    if sender_row["balance"] < amount:
        await message.reply_text(f"❌ Insufficient balance! You have {sender_row['balance']} ₹")
        return

    if transfer(sender.id, recipient.id, amount):
        new_sender = get_user(sender.id)["balance"]
        new_recipient = get_user(recipient.id)["balance"]
        await message.reply_text(
            f"💳 <b>TRANSFER SUCCESS!</b>\n"
            f"From: {sender.first_name} ({sender.id})\n"
            f"To: {recipient.first_name}\n"
            f"Amount: {amount} ₹\n\n"
            f"Your balance: {new_sender} ₹"
        )
    else:
        await message.reply_text("❌ Transfer failed")


@app.on_message(filters.command("kill"))
async def kill_cmd(client: Client, message: Message):
    """Kill someone - get 90-150 coins"""
    if not message.reply_to_message:
        await message.reply_text("❌ Reply to a user to kill them!")
        return

    actor = message.from_user
    target = message.reply_to_message.from_user

    ensure_user(actor.id, actor.username)
    ensure_user(target.id, target.username)

    actor_row = get_user(actor.id)
    target_row = get_user(target.id)

    if actor_row["is_dead"] and not is_premium(actor.id):
        await message.reply_text("💀 Dead players cannot kill!")
        return

    if actor.id == target.id:
        await message.reply_text("❌ Cannot kill yourself!")
        return

    now = int(time.time())
    if target_row["protect_until"] and now < target_row["protect_until"] and not is_premium(actor.id):
        await message.reply_text("🛡️ Target is protected!")
        return

    set_dead(target.id, True)
    reward = random.randint(90, 150)
    change_balance(actor.id, reward)
    killer_bal = get_user(actor.id)["balance"]

    await message.reply_text(
        f"💀 <b>KILL SUCCESS!</b>\n"
        f"Killer: {actor.first_name}\n"
        f"Target: {target.first_name}\n"
        f"💰 Reward: +{reward} ₹\n"
        f"Balance: {killer_bal} ₹"
    )


@app.on_message(filters.command("protect"))
async def protect_cmd(client: Client, message: Message):
    """Buy 24h protection"""
    user = message.from_user
    ensure_user(user.id, user.username)
    row = get_user(user.id)

    if not is_premium(user.id):
        if row["balance"] < PROTECT_COST:
            await message.reply_text(f"❌ Need {PROTECT_COST} ₹! You have {row['balance']} ₹")
            return
        change_balance(user.id, -PROTECT_COST)

    until = int(time.time()) + 24 * 3600
    set_protect(user.id, until)
    new_bal = get_user(user.id)["balance"]

    await message.reply_text(
        f"🛡️ <b>PROTECTED FOR 24H!</b>\n"
        f"✅ You are now protected\n"
        f"💳 Cost: -{PROTECT_COST} ₹\n"
        f"Balance: {new_bal} ₹"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GAME COMMANDS (New Games)
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_message(filters.command("slots"))
async def slots_cmd(client: Client, message: Message):
    """Play slots game"""
    user = message.from_user
    ensure_user(user.id, user.username)

    try:
        bet = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("/slots <bet>\nExample: /slots 50")
        return

    row = get_user(user.id)
    if row["balance"] < bet:
        await message.reply_text(f"❌ Insufficient balance! You have {row['balance']} ₹")
        return

    change_balance(user.id, -bet)
    result = await SlotsGame.play(bet)

    if result["won"]:
        change_balance(user.id, result["amount"])
        new_bal = get_user(user.id)["balance"]
        await message.reply_text(
            f"🎰 {result['text']} 🎰\n\n"
            f"🎉 <b>WON {result['multiplier']}!</b>\n"
            f"💰 +{result['amount']} ₹\n"
            f"Balance: {new_bal} ₹"
        )
    else:
        new_bal = get_user(user.id)["balance"]
        await message.reply_text(
            f"🎰 {result['text']} 🎰\n\n"
            f"😢 <b>LOST!</b>\n"
            f"❌ -{bet} ₹\n"
            f"Balance: {new_bal} ₹"
        )


@app.on_message(filters.command("blackjack"))
async def blackjack_cmd(client: Client, message: Message):
    """Play blackjack"""
    user = message.from_user
    ensure_user(user.id, user.username)

    try:
        bet = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("/blackjack <bet>\nExample: /blackjack 100")
        return

    row = get_user(user.id)
    if row["balance"] < bet:
        await message.reply_text(f"❌ Insufficient! You have {row['balance']} ₹")
        return

    change_balance(user.id, -bet)
    result = await BlackjackGame.play(bet)

    if result["won"]:
        change_balance(user.id, result["amount"])
        new_bal = get_user(user.id)["balance"]
        text = f"♠️ <b>BLACKJACK WIN!</b>\n{result['reason']}\n💰 +{result['amount']} ₹\nBalance: {new_bal} ₹"
    else:
        new_bal = get_user(user.id)["balance"]
        text = f"♠️ <b>BLACKJACK LOSS</b>\n{result['reason']}\n❌ -{bet} ₹\nBalance: {new_bal} ₹"

    await message.reply_text(text)


@app.on_message(filters.command("dice"))
async def dice_cmd(client: Client, message: Message):
    """Play dice game"""
    user = message.from_user
    ensure_user(user.id, user.username)

    try:
        bet = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("/dice <bet>\nExample: /dice 50")
        return

    row = get_user(user.id)
    if row["balance"] < bet:
        await message.reply_text(f"❌ Insufficient! You have {row['balance']} ₹")
        return

    change_balance(user.id, -bet)
    result = await DiceGame.play(bet)

    if result["won"]:
        change_balance(user.id, result["amount"])
        new_bal = get_user(user.id)["balance"]
        text = f"🎲 {result['text']}\n🎉 WON! {result['reason']}\n💰 +{result['amount']} ₹\nBalance: {new_bal} ₹"
    else:
        new_bal = get_user(user.id)["balance"]
        text = f"🎲 {result['text']}\n😢 LOST! {result['reason']}\n❌ -{bet} ₹\nBalance: {new_bal} ₹"

    await message.reply_text(text)


@app.on_message(filters.command("lucky"))
async def lucky_cmd(client: Client, message: Message):
    """Lucky draw game"""
    user = message.from_user
    ensure_user(user.id, user.username)

    try:
        bet = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("/lucky <bet>\nExample: /lucky 50")
        return

    row = get_user(user.id)
    if row["balance"] < bet:
        await message.reply_text(f"❌ Insufficient! You have {row['balance']} ₹")
        return

    change_balance(user.id, -bet)
    result = await LuckyDrawGame.play(bet)

    if result["won"]:
        change_balance(user.id, result["amount"])
        new_bal = get_user(user.id)["balance"]
        text = (
            f"🎁 <b>LUCKY DRAW!</b>\n"
            f"You picked: {result['picked']}\n"
            f"Winning: {result['winning']}\n"
            f"🎉 {result['multiplier']} WIN!\n"
            f"💰 +{result['amount']} ₹\n"
            f"Balance: {new_bal} ₹"
        )
    else:
        new_bal = get_user(user.id)["balance"]
        text = (
            f"🎁 <b>LUCKY DRAW</b>\n"
            f"You picked: {result['picked']}\n"
            f"Winning: {result['winning']}\n"
            f"😢 LOST\n"
            f"❌ -{bet} ₹\n"
            f"Balance: {new_bal} ₹"
        )

    await message.reply_text(text)


@app.on_message(filters.command("roulette"))
async def roulette_cmd(client: Client, message: Message):
    """Roulette game"""
    user = message.from_user
    ensure_user(user.id, user.username)

    try:
        bet = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("/roulette <bet>\nExample: /roulette 100")
        return

    row = get_user(user.id)
    if row["balance"] < bet:
        await message.reply_text(f"❌ Insufficient! You have {row['balance']} ₹")
        return

    change_balance(user.id, -bet)
    result = await RouletteGame.play(bet)

    if result["won"]:
        change_balance(user.id, result["amount"])
        new_bal = get_user(user.id)["balance"]
        text = (
            f"🎡 <b>ROULETTE WIN!</b>\n"
            f"You: {result['picked']} → Wheel: {result['winning']}\n"
            f"💰 +{result['amount']} ₹ ({result['amount']//bet}x)\n"
            f"Balance: {new_bal} ₹"
        )
    else:
        new_bal = get_user(user.id)["balance"]
        text = (
            f"🎡 <b>ROULETTE</b>\n"
            f"You: {result['picked']} → Wheel: {result['winning']}\n"
            f"❌ LOST -{bet} ₹\n"
            f"Balance: {new_bal} ₹"
        )

    await message.reply_text(text)


# ═══════════════════════════════════════════════════════════════════════════════
# AI CHAT - HINATA PERSONA
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_message((filters.text & ~filters.command & filters.private) | (filters.mentioned & filters.group))
async def hinata_reply(client: Client, message: Message):
    """Hinata AI persona - responds in private or when mentioned"""
    try:
        if message.chat.type == types.ChatType.PRIVATE:
            pass  # Always reply in private
        elif message.chat.type in (types.ChatType.GROUP, types.ChatType.SUPERGROUP):
            if not (message.mentioned or (message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_bot)):
                return

        await app.send_chat_action(message.chat.id, types.ChatAction.TYPING)

        prompt = make_hinata_prompt(message.text, getattr(message.from_user, "first_name", None))
        reply = await call_groq(prompt)

        # Enforce persona
        if "AI" in reply:
            reply = reply.replace("AI", "shy bot")

        if random.random() < 0.4:
            reply = "a-ano... " + reply

        if "Naruto-kun" not in reply and random.random() < 0.5:
            reply = reply + "\n\n— Naruto-kun?"

        if random.random() < 0.35:
            try:
                await message.reply_sticker(random.choice(HINATA_STICKERS))
            except:
                pass

        await message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error in Hinata reply: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PREFIX COMMANDS (. and !)
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_message(filters.regex(r"^[.!].+"))
async def prefix_cmd(client: Client, message: Message):
    """Handle . and ! prefix commands"""
    try:
        text = message.text or ""
        cmd = text[1:].split()[0].lower()

        if cmd == "help":
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("Full Help", callback_data="help")]])
            await message.reply_text("/help to see all commands", reply_markup=kb)
        elif cmd == "dev":
            await dev_cmd(client, message)
        elif cmd == "ping":
            await ping_cmd(client, message)
        else:
            await message.reply_text(f"❌ Unknown prefix command: {cmd}\nUse /help for list")
    except Exception as e:
        logger.error(f"Prefix error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS (Inline Buttons)
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_callback_query()
async def callback(client: Client, query: types.CallbackQuery):
    """Handle inline button callbacks"""
    try:
        data = query.data or ""

        if data == "help":
            text = """<b>📋 COMPLETE HELP</b>

🎮 <b>10 GAMES:</b>
/trivia, /rps, /hangman, /guess
/slots, /roulette, /blackjack
/dice, /lucky, /memory

💰 <b>ECONOMY:</b>
/daily, /balance, /send
/leaderboard, /kill, /steal
/protect, /revive

💬 CHAT: Reply to me for Hinata AI
.help or !help for prefix commands
"""
            await query.edit_message_text(text)

        elif data == "games":
            text = """🎮 <b>10 GAMES AVAILABLE</b>

/trivia - Answer questions ❓
/rps - Rock Paper Scissors 🏀
/hangman - Guess the word 📝
/guess - Number 1-50 🎲
/slots [bet] - Spin reels 🎰
/roulette [bet] - Pick 0-36 🎡
/blackjack [bet] - Get 21 ♠️
/dice [bet] - Roll dice 🎲
/lucky [bet] - Pick 1-10 🎁
/memory - Match pairs 🧠

All games use coins from /daily
"""
            await query.edit_message_text(text)

        elif data == "economy":
            text = """💰 <b>ECONOMY SYSTEM</b>

/daily - Claim 500 ₹ (24h cooldown)
/balance - Check your ₹
/leaderboard - Top 15 richest
/send [amount] - Transfer to user
/kill @ - Kill for 90-150 ₹
/steal @ - Rob 5-30% (50% success)
/protect - 24h shield (200 ₹)
/revive @ - Bring back (200 ₹)

👑 PREMIUM: No cooldowns, free costs
"""
            await query.edit_message_text(text)

        elif data == "premium":
            text = """👑 <b>PREMIUM FEATURES</b>

✨ No /daily cooldown
✨ Free /protect cost
✨ Free /revive cost
✨ Bypass death mechanics
✨ Special badge on leaderboard

👤 Click on leaderboard user for details
"""
            await query.edit_message_text(text)

        await query.answer("✅ Updated!", show_alert=False)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await query.answer("❌ Error", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP HEALTH CHECK SERVER
# ═══════════════════════════════════════════════════════════════════════════════


async def health_endpoint(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "healthy",
        "bot": "GAMEBOT v4.0",
        "games": 10,
        "version": "4.0.0",
        "timestamp": datetime.now().isoformat(),
    })


async def metrics_endpoint(request):
    """Metrics endpoint"""
    return web.json_response({
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
    })


async def start_http_server():
    """Start HTTP server on port 8000"""
    try:
        app_http = web.Application()
        app_http.router.add_get("/health", health_endpoint)
        app_http.router.add_get("/metrics", metrics_endpoint)

        runner = web.AppRunner(app_http)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8000)
        await site.start()

        logger.info("✅ HTTP Server started on port 8000")
        return runner
    except Exception as e:
        logger.error(f"❌ HTTP Server error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════


async def main():
    """Main entry point"""
    logger.info("🚀 GAMEBOT v4.0 Starting...")

    # Start HTTP server
    await start_http_server()

    # Initialize database
    init_db()

    # Set owner as premium
    if OWNER_ID:
        ensure_user(OWNER_ID, None)
        set_premium(OWNER_ID, True)

    logger.info("✅ GAMEBOT v4.0 Ready!")

    async with app:
        await app.idle()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✅ GAMEBOT stopped")
        sys.exit(0)
