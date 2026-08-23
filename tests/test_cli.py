import io
import random
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from board import Cell
from cli import TerminalGame
from game import Game


class TerminalTests(unittest.TestCase):
    def test_scripted_six_step_turn_runs_to_user_exit(self):
        game = Game("A", "B", rng=random.Random(9))
        game.board.cells = [Cell("empty", index) for index in range(25)]
        responses = []
        for index in range(6):
            responses.extend(("1", str(index)))
        responses.append("n")
        with patch("builtins.input", side_effect=responses), redirect_stdout(io.StringIO()) as output:
            TerminalGame(game).run()
        self.assertIn("Game ended by player", output.getvalue())
        self.assertEqual(6, game.current_step)


if __name__ == "__main__":
    unittest.main()
