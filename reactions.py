from telegram import Update
from telegram.ext import ContextTypes
import random
import urllib.request
import urllib.parse
import json

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
    # Try external free GIF APIs first, then fall back to static list
    def fetch_random_gif_for(cmd_name: str):
        # Map command to waifu.pics endpoints
        waifu_map = {
            "slap": "slap",
            "kiss": "kiss",
            "love": "hug",
            "hug": "hug",
            "sad": "cry",
            "hate": "bonk",
        }
        endpoint = waifu_map.get(cmd_name)
        if endpoint:
            try:
                url = f"https://api.waifu.pics/sfw/{urllib.parse.quote(endpoint)}"
                with urllib.request.urlopen(url, timeout=5) as resp:
                    data = json.load(resp)
                    if isinstance(data, dict) and data.get("url"):
                        return data.get("url")
            except Exception:
                pass

        # Try Tenor public endpoint as a second fallback
        try:
            q = urllib.parse.quote(cmd_name)
            tenor_key = "LIVDSRZULELA"
            url = f"https://g.tenor.com/v1/random?q={q}&key={tenor_key}&limit=1"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.load(resp)
                if isinstance(data, dict) and data.get("results"):
                    res = data["results"][0]
                    # Try to extract gif url from multiple possible fields
                    if "media" in res and isinstance(res["media"], list) and res["media"]:
                        m = res["media"][0]
                        # find any url-like field
                        for v in (m.get("gif"), m.get("mediumgif"), m.get("tinygif")):
                            if isinstance(v, dict) and v.get("url"):
                                return v.get("url")
                    if res.get("url"):
                        return res.get("url")
        except Exception:
            pass

        return None

    gifs = GIFS.get(cmd, [])
    gif = fetch_random_gif_for(cmd) or (random.choice(gifs) if gifs else None)
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
