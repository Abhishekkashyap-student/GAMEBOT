import asyncio
import logging
import os
from typing import Dict

from telegram import Update
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

import economy
from reactions import react_command


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# In-memory game managers per chat
MANAGERS: Dict[int, Dict] = {}


BRAND = "AXL BOT\nCREATED BY FIGLETAXL\nJOIN - @vfriendschat"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"{BRAND}\n\nWelcome to AXL BOT — Group Games Hub!\nUse /help to see available games."
    try:
        if update.message is not None:
            await update.message.reply_text(text)
            return
        # fallback if message is missing (e.g., some update types)
        chat = update.effective_chat
        if chat is not None:
            await context.bot.send_message(chat.id, text)
    except Exception:
        logger.exception("Failed to send /start response")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Available commands:\n"
        "/startgames - initialize games in this group\n"
        "/stopgames - stop games (admin only)\n"
        "/trivia - start a trivia question\n"
        "/rps - play rock-paper-scissors\n"
        "/hangman - start hangman\n"
        "/hangman_guess <letter> - guess a letter in hangman\n"
        "/guess - start number-guess (or use /guess <number> to answer)\n"
        "/help - this message\n"
    )
    await update.message.reply_text(text)


def ensure_chat(chat_id: int):
    if chat_id not in MANAGERS:
        MANAGERS[chat_id] = {
            "trivia": TriviaGame(),
            "rps": RPSGame(),
            "hangman": HangmanGame(),
            "guess": GuessNumberGame(),
        }
    return MANAGERS[chat_id]


async def startgames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    ensure_chat(chat_id)
    await update.message.reply_text("AXL BOT games initialized for this chat. Use /help to play.")


async def stopgames(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        return
    # Require group admin to stop games
    allowed = await is_chat_admin(update, context)
    if not allowed:
        await update.message.reply_text("Only group admins may stop games.")
        return
    chat_id = update.effective_chat.id
    MANAGERS.pop(chat_id, None)
    await update.message.reply_text("AXL BOT games stopped for this chat.")


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
    query = update.callback_query
    if query is None or query.message is None:
        return
    data = query.data or ""
    chat_id = query.message.chat.id
    if data.startswith("trivia:"):
        mgr = ensure_chat(chat_id)["trivia"]
        await mgr.handle_callback(update, context)
    elif data.startswith("rps:"):
        mgr = ensure_chat(chat_id)["rps"]
        await mgr.handle_callback(update, context)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Use /help to see available commands.")


async def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("Error: set BOT_TOKEN environment variable before running.")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("startgames", startgames))
    app.add_handler(CommandHandler("stopgames", stopgames))
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
    app.add_handler(CommandHandler("revive", economy.cmd_revive))
    app.add_handler(CommandHandler("dead", economy.cmd_dead))
    app.add_handler(CommandHandler("protectme", economy.cmd_protectme))
    app.add_handler(CommandHandler("steal", economy.cmd_steal))
    app.add_handler(CommandHandler("slots", economy.cmd_slots))
    # Reactions
    app.add_handler(CommandHandler("slap", react_command))
    app.add_handler(CommandHandler("love", react_command))
    app.add_handler(CommandHandler("kiss", react_command))
    app.add_handler(CommandHandler("hate", react_command))
    app.add_handler(CommandHandler("sad", react_command))
    # Admin / owner-only
    from admin import cmd_grant, cmd_setpremium
    app.add_handler(CommandHandler("grant", cmd_grant))
    app.add_handler(CommandHandler("setpremium", cmd_setpremium))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("AXL BOT starting...")
    economy.setup()
    try:
        # run_polling handles initialize/start/polling and shutdown cleanly
        await app.run_polling()
    except (KeyboardInterrupt, SystemExit):
        logger.info("AXL BOT stopped by signal")
    except Exception:
        logger.exception("Unhandled exception in bot run loop")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("AXL BOT stopped")
