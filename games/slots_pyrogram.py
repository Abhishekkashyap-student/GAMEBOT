"""🎰 Slots Game for Pyrogram"""
import random


class SlotsGame:
    """Slots game - spin and win"""

    SYMBOLS = ["🍒", "🍋", "🔔", "⭐", "7️⃣"]

    @staticmethod
    async def play(bet: int) -> dict:
        """Play slots, return (won, amount)"""
        reels = [random.choice(SlotsGame.SYMBOLS) for _ in range(3)]
        text = " | ".join(reels)

        if reels[0] == reels[1] == reels[2]:
            win = bet * 5
            return {"won": True, "amount": win, "multiplier": "5x JACKPOT", "text": text}
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            win = bet * 2
            return {"won": True, "amount": win, "multiplier": "2x", "text": text}
        else:
            return {"won": False, "amount": 0, "multiplier": "LOST", "text": text}
