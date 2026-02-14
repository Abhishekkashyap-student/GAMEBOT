from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


class TriviaGame:
    def __init__(self):
        # Small set of sample questions — extend as needed
        self.questions = [
            {
                "q": "Which planet is known as the Red Planet?",
                "options": ["Earth", "Mars", "Jupiter", "Venus"],
                "answer": 1,
            },
            {
                "q": "What is the capital of France?",
                "options": ["Berlin", "London", "Paris", "Rome"],
                "answer": 2,
            },
            {
                "q": "Which language is this bot written in?",
                "options": ["Java", "Python", "C#", "Go"],
                "answer": 1,
            },
        ]
        # active per-chat: chat_id -> {idx, answered}
        self.active = {}

    async def send_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat is None:
            return
        import random

        idx = random.randrange(len(self.questions))
        q = self.questions[idx]
        keyboard = []
        for i, opt in enumerate(q["options"]):
            keyboard.append([InlineKeyboardButton(opt, callback_data=f"trivia:{idx}:{i}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = await update.message.reply_text(f"Trivia: {q['q']}", reply_markup=reply_markup)
        self.active[chat.id] = {"idx": idx, "msg_id": msg.message_id}

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query is None or query.message is None:
            return
        chat = query.message.chat
        data = (query.data or "").split(":")
        if len(data) != 3:
            await query.answer()
            return
        _, idx_s, opt_s = data
        try:
            idx = int(idx_s)
            opt = int(opt_s)
        except ValueError:
            await query.answer()
            return
        q = self.questions[idx]
        correct = q["answer"] == opt
        if correct:
            text = f"✅ Correct! {q['options'][opt]} is right."
        else:
            text = f"❌ Wrong. Correct answer: {q['options'][q['answer']]}"
        await query.edit_message_text(text)
        await query.answer()
        self.active.pop(chat.id, None)
