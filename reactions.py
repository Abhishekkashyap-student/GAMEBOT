from telegram import Update
from telegram.ext import ContextTypes
import random

GIFS = {
    "slap": [
        "https://media.giphy.com/media/Gf3AUz3eBNbTW/giphy.gif",
        "https://media.giphy.com/media/jLeyZWgtwgr2U/giphy.gif",
        "https://media.giphy.com/media/YxZaAKJnEuD8Y/giphy.gif",
        "https://media.giphy.com/media/wOy6p1mrSvrwI/giphy.gif",
        "https://media.giphy.com/media/3o6ZtpWzx4T8G6gn7i/giphy.gif",
    ],
    "love": [
        "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
        "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
        "https://media.giphy.com/media/3ohzdKGkI1iB1vFmZG/giphy.gif",
        "https://media.giphy.com/media/Py8HY2V7yJSaI/giphy.gif",
        "https://media.giphy.com/media/L95W4LvsscNRT4RVEA/giphy.gif",
    ],
    "kiss": [
        "https://media.giphy.com/media/FqBTvSNjNzeZG/giphy.gif",
        "https://media.giphy.com/media/mWvxJSqx56qUuTflpE/giphy.gif",
        "https://media.giphy.com/media/xT9IgEx8SbQ0teblQc/giphy.gif",
        "https://media.giphy.com/media/g9havMazx1Xh6/giphy.gif",
    ],
    "hate": [
        "https://media.giphy.com/media/oe33xf3B50fsc/giphy.gif",
        "https://media.giphy.com/media/WsG9rSWdxwDA01Mage/giphy.gif",
        "https://media.giphy.com/media/l0HlNaQ9sBZji0NRS/giphy.gif",
        "https://media.giphy.com/media/p4NLw3I4U0obiTziBJ/giphy.gif",
    ],
    "sad": [
        "https://media.giphy.com/media/ROF8OQvDmxytW/giphy.gif",
        "https://media.giphy.com/media/l0MXsnDiWAX8R1KRi/giphy.gif",
        "https://media.giphy.com/media/kKdgdeuO2M08M/giphy.gif",
        "https://media.giphy.com/media/12XMGIQvRXQole/giphy.gif",
    ],
}

EMOJIS = {
    "slap": "👋",
    "love": "💕",
    "kiss": "😘",
    "hate": "😠",
    "sad": "😭",
}


async def react_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    cmd = update.message.text.split()[0].lstrip("/").lower()
    gifs = GIFS.get(cmd, [])
    gif = random.choice(gifs) if gifs else None
    emoji = EMOJIS.get(cmd, "✨")
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
            text = f"{emoji} <b>{update.effective_user.mention_html()} {cmd}s {target.mention_html()}</b> {emoji}"
        else:
            text = f"{emoji} <b>{update.effective_user.mention_html()} {cmd}s {target}</b> {emoji}"
    else:
        text = f"{emoji} <b>{update.effective_user.mention_html()} {cmd}s</b> {emoji}"
    if gif:
        try:
            await update.message.reply_animation(animation=gif, caption=text, parse_mode="HTML")
        except Exception:
            # Fallback if GIF URL fails
            await update.message.reply_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text(text, parse_mode="HTML")
