"""🎰 Blackjack/21 for Pyrogram"""
import random


class BlackjackGame:
    """Simple Blackjack - get closer to 21 than dealer"""

    CARDS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]  # Ace=11

    @staticmethod
    def card_value(cards: list) -> int:
        """Calculate hand value"""
        total = sum(cards)
        aces = cards.count(11)
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    @staticmethod
    async def play(bet: int) -> dict:
        """Play blackjack vs dealer"""
        player_hand = [random.choice(BlackjackGame.CARDS) for _ in range(2)]
        dealer_hand = [random.choice(BlackjackGame.CARDS) for _ in range(2)]

        player_value = BlackjackGame.card_value(player_hand)
        dealer_value = BlackjackGame.card_value(dealer_hand)

        # Dealer hits on 16 or less
        while dealer_value < 17:
            dealer_hand.append(random.choice(BlackjackGame.CARDS))
            dealer_value = BlackjackGame.card_value(dealer_hand)

        # Determine winner
        if player_value > 21:
            return {"won": False, "amount": 0, "reason": "BUST - Over 21!"}
        elif dealer_value > 21:
            win = bet * 2
            return {"won": True, "amount": win, "reason": "Dealer bust!"}
        elif player_value > dealer_value:
            win = bet * 2
            return {"won": True, "amount": win, "reason": f"You: {player_value} > Dealer: {dealer_value}"}
        elif player_value == dealer_value:
            return {"won": False, "amount": bet, "reason": "Push - tie!"}
        else:
            return {"won": False, "amount": 0, "reason": f"Dealer: {dealer_value} > You: {player_value}"}
