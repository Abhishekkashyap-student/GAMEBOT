import asyncio
import logging
import os
from typing import Dict, Optional
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from games.trivia import TriviaGame
from games.rps import RPSGame
from games.hangman import HangmanGame
from games.guess_number import GuessNumberGame
from utils.permissions import is_chat_admin
from utils.firebase_db import ensure_user, register_group, unregister_group, is_group_registered

import economy
from reactions import react_command


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# 🎮 PROFESSIONAL UI FORMATTING MODULE
# ═══════════════════════════════════════════════════════════════════

class UIFormatter:
    """Professional UI formatting with decorative elements"""
    
    # Decorative borders
    BORDER_TOP = "╔" + "═" * 45 + "╗"
    BORDER_MID = "╠" + "═" * 45 + "╣"
    BORDER_BOT = "╚" + "═" * 45 + "╝"
    DIVIDER = "─" * 47
    
    # Decorative elements
    SPARKLE = "✨"
    STAR = "⭐"
    DIAMOND = "💎"
    FLAME = "🔥"
    TROPHY = "🏆"
    COIN = "💰"
    GAME = "🎮"
    
    @staticmethod
    def title(text: str) -> str:
        """Format title with decorative styling"""
        padding = (47 - len(text)) // 2
        return f"║{' ' * padding}{text}{' ' * (47 - padding - len(text))}║"
    
    @staticmethod
    def section(title: str, items: list) -> str:
        """Format section with title and items"""
        result = f"\n{UIFormatter.SPARKLE} {title}\n"
        for item in items:
            result += f"  {item}\n"
        return result
    
    @staticmethod
    def brand() -> str:
        """Professional branding"""
        brand_text = f"""
{UIFormatter.BORDER_TOP}
{UIFormatter.title("🎮 AXL GAME BOT 🎮")}
{UIFormatter.title("⭐ ADVANCED GAME ECONOMY ⭐")}
{UIFormatter.BORDER_BOT}"""
        return brand_text


# In-memory game managers per chat
MANAGERS: Dict[int, Dict] = {}

# Track registered groups (for persistent commands without /startgames repeat)
REGISTERED_GROUPS: set = set()

# Owner customization settings
OWNER_SETTINGS: Dict[str, any] = {
    "prefix": "/",
    "auto_register": False,
    "ui_theme": "professional",
    "max_bet": 10000,
    "daily_amount": 500,
}

BRAND = UIFormatter.brand()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Advanced /start with inline buttons and rich UI"""
    user = update.effective_user
    chat = update.effective_chat
    
    if user is None:
        return
    
    # Ensure user is registered
    ensure_user(user.id, user.username)
    
    text = f"""{BRAND}

{UIFormatter.DIVIDER}

{UIFormatter.SPARKLE} Welcome, {user.first_name}! {UIFormatter.SPARKLE}

{UIFormatter.section("🏆 FEATURED", [
        "🎮 4 Amazing Games (Trivia, RPS, Hangman, Number Guess)",
        "💰 Advanced Economy System with Rupees (₹)",
        "💣 PVP Mechanics (Kill, Steal, Protect)",
        "👑 Premium Membership System",
        "🎬 Social Reactions with GIFs",
        "📊 Real-time Leaderboards",
    ])}

{UIFormatter.section("✨ QUICK COMMANDS", [
        "/daily - Claim 500 ₹ (24h cooldown)",
        "/startgames - Enable games in group",
        "/balance - Check your balance",
        "/help - See all commands",
    ])}

{UIFormatter.DIVIDER}
📢 Follow: @vfriendschat
🎮 Enjoy premium gaming experience!
"""
    
    # Create inline keyboard with action buttons
    keyboard = [
        [
            InlineKeyboardButton("📖 Help", callback_data="help"),
            InlineKeyboardButton("💰 Economy", callback_data="economy_help"),
        ],
        [
            InlineKeyboardButton("🎮 Games", callback_data="games_help"),
            InlineKeyboardButton("👑 Premium", callback_data="premium_help"),
        ],
        [
            InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if update.message is not None:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            chat_obj = update.effective_chat
            if chat_obj is not None:
                await context.bot.send_message(chat_obj.id, text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e:
        logger.exception(f"Failed to send /start response: {e}")
        # Fallback
        if update.message is not None:
            await update.message.reply_text("Welcome! Use /help to see commands.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Advanced help with inline navigation"""
    text = f"""{UIFormatter.BORDER_TOP}
{UIFormatter.title("📋 COMPLETE COMMAND LIST")}
{UIFormatter.BORDER_BOT}

{UIFormatter.section("🎮 GAMES", [
        "/trivia - Answer a trivia question",
        "/rps - Rock, Paper, Scissors",
        "/hangman - Guess the word",
        "/guess - Guess number (1-50)",
    ])}

{UIFormatter.section("💰 ECONOMY", [
        "/daily - Claim 500 ₹ (24h cooldown)",
        "/balance - Check your balance",
        "/send <amount> - Send ₹ (reply to user)",
        "/leaderboard - Top 15 richest users",
    ])}

{UIFormatter.section("💣 PVP ACTIONS", [
        "/kill - Kill user (90-150 ₹ reward)",
        "/steal - Rob user (50% success rate)",
        "/protectme - 24h protection (200 ₹)",
        "/revive - Revive dead user (200 ₹)",
    ])}

{UIFormatter.section("🎬 SOCIAL", [
        "/slap - Slap someone (reply)",
        "/love - Show love (reply)",
        "/kiss - Send kiss (reply)",
        "/hate - Show hate (reply)",
        "/sad - Cry together (reply)",
    ])}

{UIFormatter.section("🎰 GAMBLING", [
        "/slots <bet> - Play slots (2x/5x multiplier)",
    ])}

{UIFormatter.section("👨‍💼 GROUP ADMIN", [
        "/startgames - Initialize games",
        "/stopgames - Stop games (admin only)",
    ])}

{UIFormatter.section("🛠️ OWNER ONLY", [
        "/grant <amount> - Grant ₹ (reply)",
        "/setpremium on|off - Toggle premium",
        "/adminadd <id> <amount> - Add ₹ by ID",
        "/settings - Customize bot behavior",
    ])}

{UIFormatter.DIVIDER}
💡 Tip: Reply to user before using commands like /kill, /steal, /send
📌 Use /startgames in groups to enable all features
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🔙 Back", callback_data="start"),
            InlineKeyboardButton("❓ FAQ", callback_data="faq"),
        ],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


def ensure_chat(chat_id: int):
    """Ensure chat is registered with game managers"""
    if chat_id not in MANAGERS:
        MANAGERS[chat_id] = {
            "trivia": TriviaGame(),
            "rps": RPSGame(),
            "hangman": HangmanGame(),
            "guess": GuessNumberGame(),
        }
    # Add to registered groups
    REGISTERED_GROUPS.add(chat_id)
    return MANAGERS[chat_id]


async def startgames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register group and initialize all game managers"""
    if update.effective_chat is None:
        return
    
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Group"
    
    # Register the group
    ensure_chat(chat_id)
    
    text = f"""{UIFormatter.BORDER_TOP}
{UIFormatter.title("✅ GAMES INITIALIZED")}
{UIFormatter.BORDER_BOT}

{UIFormatter.SPARKLE} Group: {chat_title}
{UIFormatter.SPARKLE} Status: ACTIVE
{UIFormatter.SPARKLE} All commands enabled!

{UIFormatter.section("🎮 READY TO PLAY", [
        "Type any command now (no /startgames needed again)",
        "Use /trivia, /rps, /hangman, /guess for games",
        "Use /daily, /balance, /leaderboard for economy",
        "Use /help to see all 30+ commands",
    ])}

{UIFormatter.DIVIDER}"""
    
    await update.message.reply_text(text, parse_mode="HTML")
    logger.info(f"Games registered for chat {chat_id} ({chat_title})")


async def stopgames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop games and unregister group"""
    if update.effective_chat is None:
        return
    
    # Require group admin to stop games
    allowed = await is_chat_admin(update, context)
    if not allowed:
        await update.message.reply_text("⛔ Only group admins may stop games.")
        return
    
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title or "Group"
    
    # Remove from memory
    MANAGERS.pop(chat_id, None)
    REGISTERED_GROUPS.discard(chat_id)
    
    # Unregister from database
    unregister_group(chat_id)
    
    text = f"""{UIFormatter.BORDER_TOP}
{UIFormatter.title("🛑 GAMES STOPPED")}
{UIFormatter.BORDER_BOT}

Games have been disabled for {chat_title}.
Admin can use /startgames to re-enable.
"""
    
    await update.message.reply_text(text, parse_mode="HTML")
    logger.info(f"Games stopped for chat {chat_id} ({chat_title})")


async def trivia_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat is None:
        return
    mgr = ensure_chat(chat.id)["trivia"]
    await mgr.send_question(update, context)


async def rps_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat is None:
        return
    mgr = ensure_chat(chat.id)["rps"]
    await mgr.start_rps(update, context)


async def hangman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat is None:
        return
    mgr = ensure_chat(chat.id)["hangman"]
    await mgr.start_game(update, context)


async def hangman_guess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat is None:
        return
    if not context.args:
        await update.message.reply_text("Usage: /hangman_guess <letter>")
        return
    letter = context.args[0]
    mgr = ensure_chat(chat.id)["hangman"]
    await mgr.try_guess(update, context, letter)


async def guess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat is None:
        return
    mgr = ensure_chat(chat.id)["guess"]
    if context.args:
        try:
            n = int(context.args[0])
            await mgr.try_guess(update, context, n)
            return
        except ValueError:
            pass
    await mgr.start_game(update, context)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button callbacks"""
    query = update.callback_query
    if query is None or query.message is None:
        return
    
    data = query.data or ""
    chat_id = query.message.chat.id
    
    try:
        # Game callbacks
        if data.startswith("trivia:"):
            mgr = ensure_chat(chat_id)["trivia"]
            await mgr.handle_callback(update, context)
        elif data.startswith("rps:"):
            mgr = ensure_chat(chat_id)["rps"]
            await mgr.handle_callback(update, context)
        elif data.startswith("profile:"):
            await economy.callback_profile(update, context)
        
        # Menu callbacks
        elif data == "help":
            await help_cmd(update, context)
            await query.answer("📖 Help menu", show_alert=False)
        
        elif data == "economy_help":
            text = f"""{UIFormatter.SPARKLE} ECONOMY GUIDE {UIFormatter.SPARKLE}

/daily - Earn 500₹ every 24 hours
/balance - Check your balance
/send <amount> - Transfer to user
/leaderboard - Top 15 richest
/slots <bet> - Gamble (2x/5x wins)

{UIFormatter.SPARKLE} PVP ACTIONS {UIFormatter.SPARKLE}

/kill - Get 90-150₹ reward
/steal - 50% success, 5-30% steal
/protectme - 200₹ for 24h safety
/revive - 200₹ to revive dead user

👑 PREMIUM: Free costs & no cooldown!"""
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            await query.answer()
        
        elif data == "games_help":
            text = f"""{UIFormatter.SPARKLE} GAMES {UIFormatter.SPARKLE}

🎮 /trivia - Answer questions
🏀 /rps - Rock Paper Scissors  
📝 /hangman - Guess the word
🎲 /guess - Guess 1-50

{UIFormatter.SPARKLE} HOW TO PLAY {UIFormatter.SPARKLE}

• Use /startgames in group first
• Type any game command
• Follow instructions
• Win coins & climb leaderboard!"""
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            await query.answer()
        
        elif data == "premium_help":
            text = f"""{UIFormatter.DIAMOND} PREMIUM FEATURES {UIFormatter.DIAMOND}

👑 OWNER EXCLUSIVE BENEFITS:

✨ NO COOLDOWN on /daily
✨ FREE costs on /revive & /protectme
✨ BYPASS protection on /kill & /steal
✨ ACT while DEAD
✨ Marked with 👑 in leaderboard

{UIFormatter.SPARKLE} SET PREMIUM {UIFormatter.SPARKLE}

Owner command:
/setpremium on (reply to user)
/setpremium off (reply to user)

🔥 Features activate INSTANTLY!"""
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            await query.answer()
        
        elif data == "settings":
            if query.from_user.id != int(os.environ.get("OWNER_ID", "0")):
                await query.answer("⛔ Owner only!", show_alert=True)
                return
            
            text = f"""{UIFormatter.SPARKLE} ⚙️ BOT SETTINGS {UIFormatter.SPARKLE}

Current Configuration:
• Max Bet: {OWNER_SETTINGS['max_bet']}₹
• Daily Reward: {OWNER_SETTINGS['daily_amount']}₹
• UI Theme: {OWNER_SETTINGS['ui_theme']}
• Auto Register: {OWNER_SETTINGS['auto_register']}

Coming Soon:
- Customizable settings ui
- Max bet adjustment
- Daily reward amount
"""
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            await query.answer()
        
        elif data == "start":
            # Recreate start menu
            await start(update, context)
            await query.answer()
        
        elif data == "faq":
            text = f"""{UIFormatter.SPARKLE} FAQ {UIFormatter.SPARKLE}

Q: How do I earn ₹?
A: Use /daily for 500₹, or win games!

Q: Can dead users act?
A: No, unless they're premium ✨

Q: How long is protection?
A: 24 hours (100%)

Q: What if I lose all ₹?
A: Use /daily tomorrow!

Q: How to get premium?
A: Owner uses /setpremium

Q: Do I need to tag bot?
A: No! After /startgames, all commands work!"""
            
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            await query.answer()
        
        else:
            await query.answer()
    
    except Exception as e:
        logger.exception(f"Callback error: {e}")
        await query.answer("❌ Error processing request", show_alert=True)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Unknown command. Use /help to see available commands.")



def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ Error: set BOT_TOKEN environment variable before running.")
        print("   Example: export BOT_TOKEN='your_token_here'")
        return

    app = ApplicationBuilder().token(token).build()

    # ═══════════════════════════════════════════════════════════════
    # LOAD REGISTERED GROUPS FROM DATABASE
    # ═══════════════════════════════════════════════════════════════
    from utils.firebase_db import get_all_registered_groups
    
    registered = get_all_registered_groups()
    for group_info in registered:
        group_id = group_info["group_id"]
        ensure_chat(group_id)
    
    if registered:
        logger.info(f"✅ Loaded {len(registered)} registered groups from database")
    
    # ═══════════════════════════════════════════════════════════════
    # COMMAND HANDLERS
    # ═══════════════════════════════════════════════════════════════
    
    # Core commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    
    # Group management
    app.add_handler(CommandHandler("startgames", startgames))
    app.add_handler(CommandHandler("stopgames", stopgames))
    
    # Game commands
    app.add_handler(CommandHandler("trivia", trivia_cmd))
    app.add_handler(CommandHandler("rps", rps_cmd))
    app.add_handler(CommandHandler("hangman", hangman_cmd))
    app.add_handler(CommandHandler("hangman_guess", hangman_guess_cmd))
    app.add_handler(CommandHandler("guess", guess_cmd))
    
    # Economy commands
    app.add_handler(CommandHandler("daily", economy.cmd_daily))
    app.add_handler(CommandHandler(["balance", "bal"], economy.cmd_balance))
    app.add_handler(CommandHandler("send", economy.cmd_send))
    app.add_handler(CommandHandler("leaderboard", economy.cmd_leaderboard))
    
    # PVP commands
    app.add_handler(CommandHandler("revive", economy.cmd_revive))
    app.add_handler(CommandHandler("dead", economy.cmd_dead))
    app.add_handler(CommandHandler("kill", economy.cmd_kill))
    app.add_handler(CommandHandler("protectme", economy.cmd_protectme))
    app.add_handler(CommandHandler("steal", economy.cmd_steal))
    app.add_handler(CommandHandler("rob", economy.cmd_rob))
    
    # Gambling
    app.add_handler(CommandHandler("slots", economy.cmd_slots))
    
    # Social reactions
    app.add_handler(CommandHandler("slap", react_command))
    app.add_handler(CommandHandler("love", react_command))
    app.add_handler(CommandHandler("kiss", react_command))
    app.add_handler(CommandHandler("hate", react_command))
    app.add_handler(CommandHandler("sad", react_command))
    
    # Admin / owner-only
    from admin import cmd_grant, cmd_setpremium, cmd_adminadd
    app.add_handler(CommandHandler("grant", cmd_grant))
    app.add_handler(CommandHandler("setpremium", cmd_setpremium))
    app.add_handler(CommandHandler("adminadd", cmd_adminadd))
    
    # ═══════════════════════════════════════════════════════════════
    # CALLBACK & MESSAGE HANDLERS
    # ═══════════════════════════════════════════════════════════════
    
    # Inline button callbacks
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # Unknown command handler (must be last)
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("=" * 50)
    logger.info("🚀 AXL GAME BOT STARTING")
    logger.info("=" * 50)
    
    economy.setup()
    
    try:
        # Set up bot commands
        async def set_commands(app):
            commands = [
                BotCommand("start", "Start the bot"),
                BotCommand("help", "Show all commands"),
                BotCommand("startgames", "Enable games in group"),
                BotCommand("daily", "Claim 500₹"),
                BotCommand("balance", "Check balance"),
                BotCommand("trivia", "Play trivia"),
                BotCommand("rps", "Rock-Paper-Scissors"),
                BotCommand("hangman", "Play hangman"),
                BotCommand("guess", "Guess the number"),
                BotCommand("leaderboard", "Top 15 users"),
                BotCommand("kill", "Kill someone"),
                BotCommand("steal", "Steal coins"),
                BotCommand("protectme", "Buy protection"),
                BotCommand("slots", "Play slots"),
            ]
            await app.bot.set_my_commands(commands)
        
        # Initialize
        app.run_polling(drop_pending_updates=False)
        
    except (KeyboardInterrupt, SystemExit):
        logger.info("✅ AXL BOT stopped cleanly")
    except Exception as e:
        logger.exception(f"❌ Unhandled exception: {e}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("AXL BOT stopped")
