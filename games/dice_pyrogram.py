"""🎲 Dice Roll Game for Pyrogram"""
import random


class DiceGame:
    """Roll dice and win based on outcome"""

    @staticmethod
    async def play(bet: int, player_roll: int = None) -> dict:
        """Roll 2 dice"""
        if player_roll is None:
            die1 = random.randint(1, 6)
            die2 = random.randint(1, 6)
        else:
            die1 = player_roll // 10
            die2 = player_roll % 10

        total = die1 + die2
        text = f"🎲 {die1} + {die2} = {total}"

        # Win conditions
        if total == 7 or total == 11:  # Lucky rolls
            win = bet * 3
            return {"won": True, "amount": win, "text": text, "reason": "Lucky 7 or 11!"}
        elif total == 12:  # Craps
            return {"won": False, "amount": 0, "text": text, "reason": "Craps! 12 is bad"}
        elif total < 7:  # Low
            win = bet * 1.5
            return {"won": True, "amount": int(win), "text": text, "reason": "Low roll (under 7)"}
        else:  # High
            win = bet * 1.5
            return {"won": True, "amount": int(win), "text": text, "reason": "High roll (over 7)"}
