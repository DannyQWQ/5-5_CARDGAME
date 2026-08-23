import random
import unittest

from board import Cell, Visibility
from game import Game


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.game = Game("A", "B", rng=random.Random(8))

    def test_turn_has_three_steps_per_player(self):
        self.game.start_turn()
        self.assertEqual(3, self.game.steps_order.count(self.game.p1))
        self.assertEqual(3, self.game.steps_order.count(self.game.p2))

    def test_politician_inverts_board_at_turn_start(self):
        self.game.p1.figure_id = 219
        self.game.start_turn()
        self.assertTrue(all(c.visibility is Visibility.REVEALED for c in self.game.board.cells))

    def test_two_politicians_cancel_each_other(self):
        self.game.p1.figure_id = self.game.p2.figure_id = 219
        self.game.start_turn()
        self.assertTrue(all(c.visibility is Visibility.FACE_DOWN for c in self.game.board.cells))

    def test_two_witches_deal_simultaneous_damage(self):
        self.game.p1.figure_id = self.game.p2.figure_id = 208
        self.game.p1.hp = self.game.p2.hp = 1
        self.game.start_turn()
        self.assertEqual("draw", self.game.game_result())
        self.assertEqual([], self.game.steps_order)

    def test_foreteller_then_tic_tac_toer_step_start(self):
        self.game.p1.figure_id = 206
        self.game.p2.figure_id = 209
        messages = self.game.begin_step(
            self.game.p1,
            foreteller_indices=(0, 1, 2),
            barrier_indices={self.game.p2: 3},
        )
        self.assertTrue(all(self.game.board.cells[i].visibility is Visibility.REVEALED for i in (0, 1, 2)))
        self.assertTrue(self.game.board.cells[3].barrier)
        self.assertEqual(2, len(messages))

    def test_invalid_barrier_does_not_partially_apply_foreteller(self):
        self.game.p1.figure_id = 206
        self.game.p2.figure_id = 209
        self.game.board.cells[3].visibility = Visibility.OPENED
        with self.assertRaises(ValueError):
            self.game.begin_step(
                self.game.p1,
                foreteller_indices=(0, 1, 2),
                barrier_indices={self.game.p2: 3},
            )
        self.assertTrue(all(self.game.board.cells[i].visibility is Visibility.FACE_DOWN for i in (0, 1, 2)))

    def test_alcoholic_ignores_requested_index(self):
        self.game.p1.figure_id = 211
        self.game.board.cells[0] = Cell("empty", 0, visibility=Visibility.OPENED)
        selected = self.game.choose_open_index(self.game.p1, 0)
        self.assertNotEqual(0, selected)

    def test_numerical_modification_precedes_conversion(self):
        self.game.pending_board_effects = [7, 12]
        self.assertEqual(
            {"bomb": 13, "frog": 5, "empty": 0, "magic": 5, "figure": 2},
            self.game.resolve_next_distribution(),
        )

    def test_pawn_evolves_at_turn_start_and_const_figure_blocks_it(self):
        class CertainEvolution:
            @staticmethod
            def random():
                return 0.0

            @staticmethod
            def choice(values):
                return values[0]

            @staticmethod
            def shuffle(values):
                return None

        self.game.rng = CertainEvolution()
        self.game.p1.figure_id = 201
        self.game.p1.figure_lock_turns = 2
        self.game.start_turn()
        self.assertEqual(201, self.game.p1.figure_id)
        self.game.p1.figure_lock_turns = 0
        self.game.start_turn()
        self.assertEqual(202, self.game.p1.figure_id)

    def test_const_figure_counts_cast_turn_as_first_turn(self):
        self.game.turn_number = 1
        self.game.p1.figure_lock_turns = 3
        self.game.start_turn()
        self.assertEqual(2, self.game.p1.figure_lock_turns)
        self.game.start_turn()
        self.assertEqual(1, self.game.p1.figure_lock_turns)
        self.game.start_turn()
        self.assertEqual(0, self.game.p1.figure_lock_turns)


if __name__ == "__main__":
    unittest.main()
