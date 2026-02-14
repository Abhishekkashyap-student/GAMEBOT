from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import random


class RPSGame:
    def __init__(self):
        # No persistent state required for single-round RPS
        pass

    async def start_rps(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("✊ Rock", callback_data="rps:rock")],
            [InlineKeyboardButton("✋ Paper", callback_data="rps:paper")],
            [InlineKeyboardButton("✌️ Scissors", callback_data="rps:scissors")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Choose: Rock, Paper, or Scissors", reply_markup=reply_markup)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query is None or query.data is None:
            return
        choice = query.data.split(":")[1]
        bot_choice = random.choice(["rock", "paper", "scissors"])
        result = self._result(choice, bot_choice)
        emoji = {"rock":"✊","paper":"✋","scissors":"✌️"}
        text = f"You: {emoji.get(choice,choice)}\nBot: {emoji.get(bot_choice,bot_choice)}\n\n{result}"
        await query.edit_message_text(text)
        await query.answer()

    def _result(self, a: str, b: str) -> str:
        if a == b:
            return "It's a tie!"
        wins = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
        if wins[a] == b:
            return "You win!"
        return "You lose!"
