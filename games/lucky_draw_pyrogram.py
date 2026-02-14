"""🎁 Lucky Draw for Pyrogram"""
import random


class LuckyDrawGame:
    """Pick a number from 1-10, win based on luck"""

    @staticmethod
    async def play(bet: int, picked: int = None) -> dict:
        """Play lucky draw"""
        if picked is None:
            picked = random.randint(1, 10)

        winning_number = random.randint(1, 10)

        # Multipliers based on luck
        if picked == winning_number:
            multiplier = 10
        elif abs(picked - winning_number) == 1:
            multiplier = 3
        elif abs(picked - winning_number) <= 2:
            multiplier = 1.5
        else:
            multiplier = 0

        win = int(bet * multiplier) if multiplier > 0 else 0

        return {
            "won": multiplier > 0,
            "amount": win,
            "picked": picked,
            "winning": winning_number,
            "multiplier": f"{multiplier}x",
        }
