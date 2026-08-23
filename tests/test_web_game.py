import unittest

from board import Cell
from player import HandCard
from web_game import WebGameError, WebGameSession


class WebGameSessionTests(unittest.TestCase):
    def setUp(self):
        self.session = WebGameSession("A", "B", seed=4)

    def test_state_hides_face_down_identity(self):
        state = self.session.state()
        hidden = next(cell for cell in state["board"] if cell["visibility"] == "face_down")
        self.assertIsNone(hidden["kind"])
        self.assertIsNone(hidden["id"])

    def test_open_card_advances_exactly_one_step(self):
        before = self.session.game.current_step
        index = self.session.game.board.selectable_indices()[0]
        self.session.open_card(index)
        self.assertEqual(before + 1, self.session.game.current_step)

    def test_simple_magic_uses_real_effect_engine(self):
        player = self.session.current_player
        player.hp = 3
        player.hand = [HandCard(1)]
        self.session.play_magic(0)
        self.assertEqual(4, player.hp)

    def test_full_hand_magic_open_requests_two_discards_without_mutation(self):
        player = self.session.current_player
        player.hand = [HandCard(1), HandCard(2), HandCard(3)]
        self.session.game.board.cells[0] = Cell("magic", 0, 4)
        with self.assertRaises(WebGameError) as raised:
            self.session.open_card(0)
        self.assertEqual("discard_required", raised.exception.code)
        self.assertFalse(self.session.game.board.cells[0].is_open)
        self.assertEqual(3, len(player.hand))

    def test_target_player_id_is_converted_for_figure_magic(self):
        player = self.session.current_player
        player.hand = [HandCard(19)]
        opponent = self.session.game.get_other_player(player)
        opponent.figure_id = 208
        self.session.play_magic(0, {"target": self.session._player_id(opponent)})
        self.assertEqual(200, opponent.figure_id)

    def test_sixth_step_waits_for_review_before_generating_next_board(self):
        self.session.game.board.cells = [Cell("empty", index) for index in range(25)]
        for _ in range(6):
            index = self.session.game.board.selectable_indices()[0]
            self.session.open_card(index)
        self.assertEqual("turn_end", self.session.phase)
        self.assertEqual(1, self.session.game.turn_number)
        self.assertEqual(6, self.session.game.current_step)
        opened_before = sum(cell.is_open for cell in self.session.game.board.cells)
        self.assertEqual(6, opened_before)

        self.session.continue_turn()
        self.assertEqual(2, self.session.game.turn_number)
        self.assertEqual(0, self.session.game.current_step)
        self.assertEqual(0, sum(cell.is_open for cell in self.session.game.board.cells))

    def test_lethal_action_enters_game_over_for_victory_overlay(self):
        loser = self.session.current_player
        winner = self.session.game.get_other_player(loser)
        loser.hp = 1
        self.session.game.board.cells[0] = Cell("bomb", 0)
        state = self.session.open_card(0)
        self.assertEqual("game_over", state["phase"])
        self.assertEqual(winner.name, state["result"])


if __name__ == "__main__":
    unittest.main()
