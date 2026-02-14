from telegram import Update
from telegram.ext import ContextTypes
import random


class GuessNumberGame:
    def __init__(self):
        self.active = {}  # chat_id -> target

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat is None:
            return
        target = random.randint(1, 50)
        self.active[chat.id] = target
        await update.message.reply_text(
            "I have chosen a number between 1 and 50. Guess by sending `/guess <number>`.")

    async def try_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, n: int):
        chat = update.effective_chat
        if chat is None:
            return
        if chat.id not in self.active:
            await update.message.reply_text("No active number-guess game. Start with /guess")
            return
        target = self.active[chat.id]
        if n == target:
            await update.message.reply_text(f"🎉 Correct! The number was {target}.")
            self.active.pop(chat.id, None)
        elif n < target:
            await update.message.reply_text("Too low!")
        else:
            await update.message.reply_text("Too high!")
