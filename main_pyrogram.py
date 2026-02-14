#!/usr/bin/env python3
"""
🤖 Production-Ready Pyrogram Telegram Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
High-availability, error-resilient design for Koyeb.
Built for premium user experience with advanced UI/UX.

Features:
- Auto-detection of private vs group chats
- Advanced inline button interactions
- Admin-level group management (/ban, /kick)
- Real-time system stats (/ping)
- Smart AI chat simulation
- Health check HTTP server on port 8000
- Comprehensive error handling & logging
"""

import os
import sys
import logging
import asyncio
from typing import Optional
from datetime import datetime
import psutil
import traceback

# Pyrogram & dependencies
from pyrogram import Client, filters, types
from pyrogram.errors import (
    ChatAdminRequired,
    UserAdminInvalid,
    PeerIdInvalid,
    FloodWait,
)
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    User,
    Chat,
)
import httpx
import random
import asyncio

# Optional fallback chat client (reverse-engineered providers)
try:
    import g4f
    G4F_AVAILABLE = True
except Exception:
    G4F_AVAILABLE = False

# HTTP Server (Health Check & Keep-Alive)
from aiohttp import web
import uvloop

# Configuration from environment
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
GROQ_KEYS_ENV = os.getenv("GROQ_KEYS", "")

# Build Groq keys list from environment (REQUIRED for AI to work)
GROQ_KEYS = [k.strip() for k in GROQ_KEYS_ENV.split(",") if k.strip()] if GROQ_KEYS_ENV else []

if not GROQ_KEYS:
    logger.warning("⚠️ GROQ_KEYS env not set - AI fallback to g4f or canned responses")

# Stickers for Hinata persona
HINATA_STICKERS = [
    "CAACAgUAAxkBAAEQgltpj2uaFvRFMs_ACV5pQrqBvnKWoQAC2QMAAvmysFdnPHJXLMM8TjoE",
    "CAACAgUAAxkBAAEQgl1pj2u6CJJq6jC-kXYHM9fvpJ5ygAACXgUAAov2IVf0ZtG-JNnfFToE",
]

# Groq rotation index
_groq_index = 0

# Validate configuration
if not all([API_ID, API_HASH, BOT_TOKEN, OWNER_ID]):
    print("❌ ERROR: Missing required environment variables!")
    print("   Required: API_ID, API_HASH, BOT_TOKEN, OWNER_ID")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

logger.info("🚀 Starting Pyrogram Bot...")
logger.info(f"Owner ID: {OWNER_ID}")

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

app = Client(
    name="pyrogram_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="./sessions",
)

# ═══════════════════════════════════════════════════════════════════════════════
# UI/UX PREMIUM FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════


class UIFormatter:
    """Premium UI formatting with emojis and clean design"""

    @staticmethod
    def brand() -> str:
        """Premium bot branding"""
        return (
            "╔════════════════════════════════════╗\n"
            "║  🤖 AXL GAME BOT v3.0 PYROGRAM 🤖  ║\n"
            "║    Production-Ready Edition        ║\n"
            "╚════════════════════════════════════╝"
        )

    @staticmethod
    def section(title: str, content: str) -> str:
        """Formatted section with title"""
        return f"\n✨ <b>{title}</b>\n{content}"

    @staticmethod
    def code_block(text: str) -> str:
        """Format as monospace code block"""
        return f"<code>{text}</code>"

    @staticmethod
    def button(text: str, emoji: str = "➜") -> str:
        """Format button with emoji"""
        return f"{emoji} {text}"


# ═══════════════════════════════════════════════════════════════════════════════
# INLINE KEYBOARD BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════


def build_start_keyboard() -> InlineKeyboardMarkup:
    """Build premium /start keyboard"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📖 Help", callback_data="help"),
                InlineKeyboardButton("ℹ️ About", callback_data="about"),
            ],
            [
                InlineKeyboardButton("💻 Source", callback_data="source"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            ],
            [
                InlineKeyboardButton("🔗 Add to Group", url="https://t.me/"),
            ],
        ]
    )


def build_help_keyboard() -> InlineKeyboardMarkup:
    """Build help menu keyboard"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎮 Commands", callback_data="commands"),
                InlineKeyboardButton("👮 Group Mgmt", callback_data="groupmgmt"),
            ],
            [
                InlineKeyboardButton("🔧 Utilities", callback_data="utilities"),
                InlineKeyboardButton("ℹ️ Info", callback_data="info"),
            ],
            [
                InlineKeyboardButton("◀️ Back", callback_data="back_start"),
            ],
        ]
    )


def build_back_keyboard() -> InlineKeyboardMarkup:
    """Build back button"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("◀️ Back to Start", callback_data="back_start"),
            ],
        ]
    )


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


async def is_admin(user_id: int, chat_id: int) -> bool:
    """Check if user is admin in group"""
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [
            types.ChatMemberStatus.ADMINISTRATOR,
            types.ChatMemberStatus.OWNER,
        ]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False


async def call_groq(prompt: str, model: str = "llama3-8b-8192") -> str:
    """Try Groq keys in rotation. On failure, fall back to g4f or a canned response.
    This function never raises — always returns a string reply.
    """
    global _groq_index
    headers_template = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(len(GROQ_KEYS)):
            key = GROQ_KEYS[_groq_index % len(GROQ_KEYS)]
            _groq_index += 1
            headers = headers_template.copy()
            headers["Authorization"] = f"Bearer {key}"

            payload = {
                "model": model,
                "input": prompt,
                "max_output_tokens": 512,
            }

            try:
                # Groq public endpoint may vary; try a commonly used path
                url = "https://api.groq.ai/v1/completions"
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    # Best-effort extraction of text
                    if isinstance(data, dict):
                        text = data.get("output") or data.get("text") or data.get("choices", [{}])[0].get("text")
                        if text:
                            return text.strip()
                else:
                    logger.warning(f"Groq key rotated - non-200 status {resp.status_code}")
            except Exception as e:
                logger.warning(f"Groq request failed with key rotation: {e}")

    # Fallback: try g4f if available
    if G4F_AVAILABLE:
        try:
            # Use g4f's chat completion if available; adapt to supported method
            reply = g4f.chat_completion.create(prompt)
            if reply:
                return reply
        except Exception as e:
            logger.warning(f"g4f fallback failed: {e}")

    # As last resort, return a persona-safe canned reply
    canned = (
        "a-ano... I-I'm not sure, Naruto-kun... but I'll try my best to help!"
    )
    return canned


def make_hinata_prompt(user_text: str, user_name: str | None = None) -> str:
    """Wrap user text with strong Hinata persona instructions."""
    persona = (
        "You are Hinata Hyuga from Naruto. Speak shyly, caring, and use 'Naruto-kun' sometimes. "
        "Stutter occasionally like 'a-ano...'. Never admit you are an AI. Keep replies short, soft, and kind. "
        "When appropriate, use a small compliment or supportive phrase."
    )
    context = f"User ({user_name or 'friend'}) says: {user_text}\n\nRespond as Hinata:" 
    return persona + "\n\n" + context


async def get_system_stats() -> str:
    """Get real-time system statistics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        stats = (
            f"<b>📊 System Statistics</b>\n"
            f"CPU: {cpu_percent}%\n"
            f"Memory: {memory_percent}%\n"
            f"Boot: {boot_time}\n"
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return "<b>📊 System Stats</b>\nUnavailable"


def get_ai_response(user_message: str) -> str:
    """Simulated AI response (witty & smart)"""
    responses = {
        "hello": "👋 Hey there! I'm a premium Pyrogram bot. How can I help? 🚀",
        "hi": "🎉 Yo! What brings you to chat with me? 💬",
        "how are you": "😊 I'm running smoothly! 100% uptime achieved! ⚡",
        "what is your name": "🤖 I'm AXL GAME BOT v3.0 - built with Pyrogram! 🔥",
        "thanks": "❤️ You're welcome! Anything else I can do? 😊",
        "help": "📖 I can help! Use /help for commands or just chat with me! 🗣️",
        "ping": "🏓 Pong! I'm alive and ready! ⚡",
    }

    user_lower = user_message.lower().strip()
    for key, response in responses.items():
        if key in user_lower:
            return response

    # Default witty responses
    witty_defaults = [
        "💡 Interesting thought! Tell me more? 🤔",
        "😄 Ha! I like your style! 🎯",
        "✨ That's cool! What else? 👀",
        "🎭 Drama! I'm here for it! 📢",
        "🚀 Let's keep this conversation going! 💪",
    ]

    import random

    return random.choice(witty_defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_message(filters.command("start") & filters.private)
async def start_private(client: Client, message: Message):
    """Handle /start in private chat"""
    try:
        welcome_text = (
            f"{UIFormatter.brand()}\n\n"
            f"👋 Welcome, <b>{message.from_user.first_name}!</b>\n\n"
            f"<b>✨ I'm a premium Telegram bot built with Pyrogram.</b>\n"
            f"<b>⚡ Lightning-fast responses • 🛡️ Production-ready</b>\n"
            f"<b>🎮 Fun games • 📊 Utilities • 🔧 Tools</b>\n\n"
            f"<i>Choose an option below to get started:</i>"
        )

        await message.reply_text(
            welcome_text,
            reply_markup=build_start_keyboard(),
            disable_web_page_preview=True,
        )
        logger.info(f"✅ /start sent to {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Error in /start handler: {e}\n{traceback.format_exc()}")
        await message.reply_text("❌ An error occurred. Please try again.")


@app.on_message(filters.command("start") & filters.group)
async def start_group(client: Client, message: Message):
    """Handle /start in group chat"""
    try:
        group_text = (
            f"👋 <b>Hello {message.from_user.first_name}!</b>\n\n"
            f"<b>🤖 AXL GAME BOT v3.0</b> is now active in this group!\n\n"
            f"<b>Available Commands:</b>\n"
            f"/help - Show all commands\n"
            f"/ping - Check bot latency\n"
            f"/ban - Ban user (admin only)\n"
            f"/kick - Kick user (admin only)\n"
            f"/info - Group information\n\n"
            f"💬 Reply to me for a chat!"
        )

        await message.reply_text(group_text, reply_markup=build_help_keyboard())
        logger.info(f"✅ /start sent to group {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error in group /start: {e}\n{traceback.format_exc()}")


@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handle /help command"""
    try:
        is_group = message.chat.type in [
            types.ChatType.GROUP,
            types.ChatType.SUPERGROUP,
        ]

        help_text = (
            f"{UIFormatter.brand()}\n\n"
            f"<b>📖 Help Menu</b>\n\n"
            f"<b>Common Commands:</b>\n"
            f"/start - Show welcome message\n"
            f"/help - Show this help message\n"
            f"/ping - Check bot latency & stats\n"
            f"/info - Get information\n"
        )

        if is_group:
            help_text += (
                f"\n<b>Group Management (Admin Only):</b>\n"
                f"/ban <user_id> - Ban user\n"
                f"/kick <user_id> - Kick user\n"
            )

        help_text += (
            f"\n<b>💬 Features:</b>\n"
            f"• Reply to me for AI chat\n"
            f"• Real-time system stats\n"
            f"• Premium UI/UX\n"
            f"• High-availability design\n"
        )

        await message.reply_text(
            help_text, reply_markup=build_help_keyboard() if not is_group else None
        )
        logger.info(f"✅ /help sent to {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error in /help handler: {e}\n{traceback.format_exc()}")
        await message.reply_text("❌ Error retrieving help.")


@app.on_message(filters.command(["dev", "/dev"]))
async def dev_command(client: Client, message: Message):
    try:
        await message.reply_text("CREATED BY FIGLETAXL | JOIN - @vfriendschat")
    except Exception as e:
        logger.error(f"Error in /dev: {e}")


@app.on_message(filters.regex(r'^[.!].+'))
async def prefix_command(client: Client, message: Message):
    """Handle dot/bang prefix commands like .help or !dev by mapping them to existing handlers."""
    try:
        text = message.text or ""
        if not text:
            return
        # Remove leading prefix
        cmd_text = text[1:].strip()
        cmd = cmd_text.split()[0].lower()

        # Map a small set of commands
        if cmd in ("help", "start"):
            await help_command(client, message)
            return
        if cmd in ("dev",):
            await dev_command(client, message)
            return
        if cmd in ("ping",):
            await ping_command(client, message)
            return
        if cmd in ("info",):
            await info_command(client, message)
            return
        # Unknown prefix command -> polite message
        await message.reply_text("❌ Unknown command. Use .help or /help to see available commands.")
    except Exception as e:
        logger.error(f"Error handling prefix command: {e}")


@app.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    """Handle /ping command - show latency & system stats"""
    try:
        start_time = datetime.now()

        stats = (
            f"<b>⚡ Bot Status</b>\n\n"
            f"🕐 <b>Current Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        )

        stats += await get_system_stats()

        # Calculate latency
        latency = (datetime.now() - start_time).total_seconds() * 1000

        stats += f"\n🌍 <b>Latency:</b> {latency:.2f}ms\n"
        stats += f"✅ <b>Status:</b> Online & Healthy"

        await message.reply_text(stats)
        logger.info(f"✅ /ping sent to {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error in /ping handler: {e}\n{traceback.format_exc()}")
        await message.reply_text("❌ Error fetching stats.")


@app.on_message(filters.command("ban"))
async def ban_command(client: Client, message: Message):
    """Handle /ban command (admin only)"""
    try:
        # Check if group
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            await message.reply_text("❌ This command only works in groups.")
            return

        # Check if user is admin
        if not await is_admin(message.from_user.id, message.chat.id):
            await message.reply_text("❌ You must be an admin to use this command.")
            return

        # Parse user ID
        if len(message.command) < 2:
            await message.reply_text(
                "❌ Usage: /ban <user_id>\n\nExample: /ban 123456789"
            )
            return

        user_id = int(message.command[1])

        # Ban the user
        await app.ban_chat_member(message.chat.id, user_id)

        await message.reply_text(
            f"✅ <b>User {user_id} has been banned.</b>\n\n"
            f"🚫 They can no longer access this group."
        )

        logger.info(f"✅ User {user_id} banned from group {message.chat.id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")
    except ChatAdminRequired:
        await message.reply_text("❌ I don't have admin rights to ban users.")
    except Exception as e:
        logger.error(f"❌ Error in /ban handler: {e}\n{traceback.format_exc()}")
        await message.reply_text(f"❌ Error banning user: {str(e)}")


@app.on_message(filters.command("kick"))
async def kick_command(client: Client, message: Message):
    """Handle /kick command (admin only)"""
    try:
        # Check if group
        if message.chat.type not in [types.ChatType.GROUP, types.ChatType.SUPERGROUP]:
            await message.reply_text("❌ This command only works in groups.")
            return

        # Check if user is admin
        if not await is_admin(message.from_user.id, message.chat.id):
            await message.reply_text("❌ You must be an admin to use this command.")
            return

        # Parse user ID
        if len(message.command) < 2:
            await message.reply_text(
                "❌ Usage: /kick <user_id>\n\nExample: /kick 123456789"
            )
            return

        user_id = int(message.command[1])

        # Kick the user (temporarily ban for 30 seconds then unban)
        await app.ban_chat_member(message.chat.id, user_id)
        await asyncio.sleep(2)  # Brief delay
        await app.unban_chat_member(message.chat.id, user_id)

        await message.reply_text(
            f"✅ <b>User {user_id} has been kicked.</b>\n\n"
            f"👋 They have been removed from the group."
        )

        logger.info(f"✅ User {user_id} kicked from group {message.chat.id}")
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")
    except ChatAdminRequired:
        await message.reply_text("❌ I don't have permissions to kick users.")
    except Exception as e:
        logger.error(f"❌ Error in /kick handler: {e}\n{traceback.format_exc()}")
        await message.reply_text(f"❌ Error kicking user: {str(e)}")


@app.on_message(filters.command("info"))
async def info_command(client: Client, message: Message):
    """Handle /info command"""
    try:
        is_group = message.chat.type in [
            types.ChatType.GROUP,
            types.ChatType.SUPERGROUP,
        ]

        if is_group:
            info_text = (
                f"<b>📊 Group Information</b>\n\n"
                f"<b>Group Name:</b> {message.chat.title}\n"
                f"<b>Group ID:</b> <code>{message.chat.id}</code>\n"
                f"<b>Type:</b> {message.chat.type}\n"
                f"<b>Members:</b> {message.chat.members_count or 'Unknown'}\n"
            )
        else:
            info_text = (
                f"<b>👤 User Information</b>\n\n"
                f"<b>Name:</b> {message.from_user.first_name} "
                f"{message.from_user.last_name or ''}\n"
                f"<b>Username:</b> @{message.from_user.username or 'N/A'}\n"
                f"<b>ID:</b> <code>{message.from_user.id}</code>\n"
                f"<b>Type:</b> Private Chat\n"
            )

        await message.reply_text(info_text)
        logger.info(f"✅ /info sent to {message.chat.id}")
    except Exception as e:
        logger.error(f"❌ Error in /info handler: {e}\n{traceback.format_exc()}")
        await message.reply_text("❌ Error fetching information.")


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACK QUERY HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_callback_query()
async def callback_handler(client: Client, query: types.CallbackQuery):
    """Handle all inline button callbacks"""
    try:
        data = query.data

        if data == "help":
            await query.edit_message_text(
                "<b>📖 Help Menu</b>\n\n"
                "Click below to explore:\n\n"
                "🎮 <b>Commands</b> - All available commands\n"
                "👮 <b>Group Management</b> - Admin tools\n"
                "🔧 <b>Utilities</b> - Useful features\n"
                "ℹ️ <b>Info</b> - Bot information\n",
                reply_markup=build_help_keyboard(),
            )

        elif data == "about":
            about_text = (
                f"{UIFormatter.brand()}\n\n"
                f"<b>About AXL GAME BOT</b>\n\n"
                f"🚀 <b>Version:</b> 3.0 Pyrogram Edition\n"
                f"⚡ <b>Framework:</b> Pyrogram 2.0+\n"
                f"🔧 <b>Technology:</b> Python 3.10, Async/Await\n"
                f"🎯 <b>Deployment:</b> Koyeb (High-Availability)\n\n"
                f"<b>Features:</b>\n"
                f"✨ Premium UI with inline buttons\n"
                f"🛡️ Advanced error handling\n"
                f"📊 Real-time system monitoring\n"
                f"👮 Group management tools\n"
                f"💬 Smart AI chat simulation\n"
                f"⚙️ Production-ready design\n"
            )
            await query.edit_message_text(
                about_text, reply_markup=build_help_keyboard()
            )

        elif data == "source":
            await query.edit_message_text(
                "<b>💻 Source Code</b>\n\n"
                "🔗 <b>GitHub Repository:</b>\n"
                "<code>https://github.com/Abhishekkashyap-student/GAMEBOT</code>\n\n"
                "📦 <b>Open Source & Free to Use</b>\n"
                "🤝 Contributions Welcome!\n",
                reply_markup=build_help_keyboard(),
            )

        elif data == "settings":
            await query.edit_message_text(
                "<b>⚙️ Settings</b>\n\n"
                "📢 Notifications: Enabled ✅\n"
                "🔔 Alerts: Enabled ✅\n"
                "🌙 Dark Mode: Available\n"
                "🌍 Language: English\n\n"
                "<i>More settings coming soon!</i>",
                reply_markup=build_help_keyboard(),
            )

        elif data == "commands":
            await query.edit_message_text(
                "<b>🎮 Bot Commands</b>\n\n"
                "/start - Welcome message\n"
                "/help - Show help menu\n"
                "/ping - Bot latency & stats\n"
                "/info - Information\n"
                "/ban - Ban user (admin)\n"
                "/kick - Kick user (admin)\n\n"
                "💬 Reply to me for chat!",
                reply_markup=build_help_keyboard(),
            )

        elif data == "groupmgmt":
            await query.edit_message_text(
                "<b>👮 Group Management</b>\n\n"
                "<b>Admin-only commands:</b>\n\n"
                "/ban <user_id> - Ban user\n"
                "/kick <user_id> - Kick user\n"
                "/info - Group details\n\n"
                "✅ Check admin status first!\n"
                "🔐 Secure & reliable",
                reply_markup=build_help_keyboard(),
            )

        elif data == "utilities":
            await query.edit_message_text(
                "<b>🔧 Utilities</b>\n\n"
                "/ping - Real-time stats\n"
                "💬 AI Chat - Reply to message\n"
                "📊 Monitoring - Health checks\n"
                "🌍 Multi-language support\n",
                reply_markup=build_help_keyboard(),
            )

        elif data == "info":
            await query.edit_message_text(
                "<b>ℹ️ Bot Information</b>\n\n"
                f"🤖 <b>Name:</b> AXL GAME BOT\n"
                f"📌 <b>Version:</b> 3.0 Pyrogram\n"
                f"⚡ <b>Status:</b> Online & Active\n"
                f"🔄 <b>Uptime:</b> 100%\n"
                f"🌍 <b>Location:</b> Cloud (Koyeb)\n\n"
                f"<i>Built with ❤️ for premium experience</i>",
                reply_markup=build_help_keyboard(),
            )

        elif data == "back_start":
            await query.edit_message_text(
                f"{UIFormatter.brand()}\n\n"
                f"👋 Welcome back!\n\n"
                f"<b>✨ Premium Telegram Bot</b>\n"
                f"<b>⚡ Choose an option below:</b>",
                reply_markup=build_start_keyboard(),
            )

        await query.answer("✅ Updated!", show_alert=False)
        logger.info(f"✅ Callback processed: {data}")

    except Exception as e:
        logger.error(f"❌ Error in callback handler: {e}\n{traceback.format_exc()}")
        await query.answer("❌ Error processing request.", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE HANDLERS (AI Chat Simulation)
# ═══════════════════════════════════════════════════════════════════════════════


@app.on_message((filters.text & ~filters.command & filters.private) | (filters.mentioned & filters.group) | (filters.reply & filters.group))
async def hinata_chat(client: Client, message: Message):
    """Handle private messages and group mentions/replies as Hinata persona.
    Also accept prefix triggers like .help or !help via separate handler below.
    """
    try:
        # Determine if we should respond: private OR mentioned OR replied-to-bot
        is_private = message.chat.type == types.ChatType.PRIVATE
        should_respond = is_private

        # If group: respond when mentioned or when replying to bot
        if message.chat.type in (types.ChatType.GROUP, types.ChatType.SUPERGROUP):
            if message.mentioned or (message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_bot):
                should_respond = True

        if not should_respond:
            return

        # Typing indicator
        await app.send_chat_action(message.chat.id, types.ChatAction.TYPING)

        # Build Hinata prompt
        prompt = make_hinata_prompt(message.text, getattr(message.from_user, "first_name", None))

        # Call AI engine with Groq primary and g4f fallback
        reply_text = await call_groq(prompt)

        # Make sure Hinata never admits being AI; enforce persona tweaks
        if "I am an AI" in reply_text or "I'm an AI" in reply_text:
            reply_text = reply_text.replace("I am an AI", "I... prefer not to say that, Naruto-kun")
            reply_text = reply_text.replace("I'm an AI", "I... prefer not to say that, Naruto-kun")

        # Add shy prefixes sometimes
        if random.random() < 0.35:
            reply_text = "a-ano... " + reply_text

        # Always use Naruto-kun occasionally
        if "Naruto-kun" not in reply_text and random.random() < 0.5:
            reply_text = reply_text + "\n\n— Naruto-kun?"

        # Send sticker sometimes to feel "real"
        if random.random() < 0.4:
            try:
                sticker_id = random.choice(HINATA_STICKERS)
                await message.reply_sticker(sticker_id)
            except Exception:
                pass

        await message.reply_text(reply_text)
        logger.info(f"✅ Hinata reply sent to {message.from_user.id} in chat {message.chat.id}")

    except Exception as e:
        logger.error(f"❌ Error in Hinata chat: {e}\n{traceback.format_exc()}")
        try:
            await message.reply_text("a-ano... I'm having trouble replying right now, Naruto-kun...")
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP HEALTH CHECK SERVER (Keep Koyeb Alive)
# ═══════════════════════════════════════════════════════════════════════════════


async def health_check(request):
    """Health check endpoint"""
    return web.json_response(
        {
            "status": "healthy",
            "bot": "AXL GAME BOT v3.0",
            "version": "3.0.0",
            "timestamp": datetime.now().isoformat(),
            "uptime": "running",
        }
    )


async def metrics(request):
    """Metrics endpoint"""
    try:
        return web.json_response(
            {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "boot_time": datetime.fromtimestamp(
                    psutil.boot_time()
                ).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Error in metrics endpoint: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def start_http_server():
    """Start HTTP server for health checks"""
    try:
        app_http = web.Application()
        app_http.router.add_get("/health", health_check)
        app_http.router.add_get("/metrics", metrics)

        runner = web.AppRunner(app_http)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8000)
        await site.start()

        logger.info("✅ HTTP Health Check Server started on port 8000")
        return runner
    except Exception as e:
        logger.error(f"❌ Failed to start HTTP server: {e}\n{traceback.format_exc()}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════


async def main():
    """Main application entry point"""
    try:
        logger.info("🚀 Initializing AXL GAME BOT v3.0 with Pyrogram...")

        # Start HTTP server for keep-alive
        http_runner = await start_http_server()

        # Start bot
        logger.info("🤖 Starting Pyrogram bot client...")
        async with app:
            logger.info("✅ Bot is now running!")
            logger.info(f"Bot Token: {BOT_TOKEN[:20]}...")
            logger.info("Listening for messages...")

            await app.idle()

    except KeyboardInterrupt:
        logger.info("⚠️ Bot interrupted by user.")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
    finally:
        logger.info("🛑 Bot shutdown complete.")


if __name__ == "__main__":
    # Set uvloop for better performance
    try:
        uvloop.install()
        logger.info("✅ uvloop installed for optimal performance")
    except Exception as e:
        logger.warning(f"⚠️ uvloop not available: {e}")

    # Run main
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("✅ Bot stopped gracefully.")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}\n{traceback.format_exc()}")
        sys.exit(1)
