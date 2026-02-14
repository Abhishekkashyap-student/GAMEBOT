"""Games package for AXL BOT"""

from .trivia import TriviaGame
from .rps import RPSGame
from .hangman import HangmanGame
from .guess_number import GuessNumberGame

__all__ = ["TriviaGame", "RPSGame", "HangmanGame", "GuessNumberGame"]
