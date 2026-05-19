"""
Card Game - Main Entry Point
Run this file to start the game in terminal
"""

from game import Game


if __name__ == "__main__":
    # Create game with two players
    game = Game(p1_name="Player 1", p2_name="Player 2")

    # Start the game loop
    game.run()
