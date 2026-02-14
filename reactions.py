from telegram import Update
from telegram.ext import ContextTypes
import random

GIFS = {
    "slap": [
        "https://media.giphy.com/media/Gf3AUz3eBNbTW/giphy.gif",
        "https://media.giphy.com/media/jLeyZWgtwgr2U/giphy.gif",
    ],
    "love": [
        "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
        "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
    ],
    "kiss": [
        "https://media.giphy.com/media/FqBTvSNjNzeZG/giphy.gif",
    ],
    "hate": [
        "https://media.giphy.com/media/oe33xf3B50fsc/giphy.gif",
    ],
    "sad": [
        "https://media.giphy.com/media/ROF8OQvDmxytW/giphy.gif",
    ],
}


async def react_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    cmd = update.message.text.split()[0].lstrip("/").lower()
    gifs = GIFS.get(cmd, [])
    gif = random.choice(gifs) if gifs else None
    target = None
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        # mention by username if provided
        if context.args:
            target = context.args[0]
    text = ""
    if target:
        if hasattr(target, 'mention_html'):
            text = f"{update.effective_user.mention_html()} {cmd}s {target.mention_html()}"
        else:
            text = f"{update.effective_user.mention_html()} {cmd}s {target}"
    else:
        text = f"{update.effective_user.mention_html()} {cmd}s"
    if gif:
        await update.message.reply_animation(animation=gif, caption=text, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")
