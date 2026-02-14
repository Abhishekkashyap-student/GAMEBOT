"""🎡 Roulette Game for Pyrogram"""
import random


class RouletteGame:
    """European Roulette - pick a number 0-36"""

    @staticmethod
    async def play(bet: int, picked_number: int = None) -> dict:
        """Play roulette"""
        if picked_number is None:
            picked_number = random.randint(0, 36)

        winning_number = random.randint(0, 36)

        if picked_number == winning_number:
            win = bet * 36  # 36:1 payout
            return {"won": True, "amount": win, "picked": picked_number, "winning": winning_number}
        elif (picked_number % 2) == (winning_number % 2):  # Even/Odd match
            win = bet * 2
            return {"won": True, "amount": win, "picked": picked_number, "winning": winning_number}
        else:
            return {"won": False, "amount": 0, "picked": picked_number, "winning": winning_number}
