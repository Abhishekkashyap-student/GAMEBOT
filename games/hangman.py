from telegram import Update
from telegram.ext import ContextTypes
import random


class HangmanGame:
    def __init__(self):
        self.words = ["python", "telegram", "hangman", "bot", "games"]
        self.active = {}  # chat_id -> state

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat is None:
            return
        word = random.choice(self.words)
        state = {
            "word": word,
            "masked": ["_" for _ in word],
            "attempts": 6,
            "guessed": set(),
        }
        self.active[chat.id] = state
        await update.message.reply_text(
            f"Hangman started! Word: {' '.join(state['masked'])}\nAttempts left: {state['attempts']}\nGuess letters with /hangman_guess <letter>"
        )

    async def try_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, letter: str):
        chat = update.effective_chat
        if chat is None:
            return
        cid = chat.id
        if cid not in self.active:
            await update.message.reply_text("No active hangman game. Start with /hangman")
            return
        state = self.active[cid]
        letter = letter.lower()
        if not letter.isalpha() or len(letter) != 1:
            await update.message.reply_text("Send a single letter (a-z).")
            return
        if letter in state["guessed"]:
            await update.message.reply_text(f"Letter '{letter}' already guessed.")
            return
        state["guessed"].add(letter)
        if letter in state["word"]:
            for i, ch in enumerate(state["word"]):
                if ch == letter:
                    state["masked"][i] = letter
            if "_" not in state["masked"]:
                await update.message.reply_text(f"🎉 Word solved: {state['word']}")
                self.active.pop(cid, None)
                return
            await update.message.reply_text(
                f"Good! {' '.join(state['masked'])}\nAttempts left: {state['attempts']}"
            )
        else:
            state["attempts"] -= 1
            if state["attempts"] <= 0:
                await update.message.reply_text(f"Game over. The word was: {state['word']}")
                self.active.pop(cid, None)
                return
            await update.message.reply_text(
                f"Wrong. {' '.join(state['masked'])}\nAttempts left: {state['attempts']}"
            )
