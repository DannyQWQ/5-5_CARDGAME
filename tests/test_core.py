import random
import unittest

from board import Board, Cell
from game import Game
from player import Player


class BoardTests(unittest.TestCase):
    def test_default_board_has_25_cards_and_assigned_identities(self):
        board = Board(rng=random.Random(1))
        self.assertEqual(25, len(board.cells))
        self.assertTrue(all(c.card_id is not None for c in board.cells if c.card_type in {"magic", "figure"}))

    def test_invalid_distribution_is_rejected(self):
        with self.assertRaises(ValueError):
            Board({"bomb": 1, "frog": 1, "empty": 1, "magic": 1, "figure": 1})

    def test_shuffle_closes_and_preserves_the_same_cards(self):
        board = Board(rng=random.Random(2))
        board.open_cell(0)
        board.cells[1].barrier = True
        before = sorted((c.card_type, c.card_id) for c in board.cells)
        board.shuffle()
        after = sorted((c.card_type, c.card_id) for c in board.cells)
        self.assertEqual(before, after)
        self.assertFalse(any(c.is_open or c.barrier for c in board.cells))


class PlayerTests(unittest.TestCase):
    def test_full_hand_must_discard_exactly_two_to_receive_magic(self):
        player = Player("A")
        player.hand = [1, 2, 3]
        with self.assertRaises(ValueError):
            player.receive_magic(4)
        discarded = player.receive_magic(4, (0, 2))
        self.assertEqual([1, 3], discarded)
        self.assertEqual([2, 4], player.hand)


class GameTests(unittest.TestCase):
    def setUp(self):
        self.game = Game("A", "B", rng=random.Random(3))

    def test_magic_identity_is_not_rerolled_when_opened(self):
        self.game.board.cells[0] = Cell("magic", 0, card_id=17)
        self.game.open_card(self.game.p1, 0)
        self.assertEqual([17], self.game.p1.hand)

    def test_full_hand_validation_happens_before_card_is_opened(self):
        self.game.p1.hand = [1, 2, 3]
        self.game.board.cells[0] = Cell("magic", 0, card_id=4)
        with self.assertRaises(ValueError):
            self.game.open_card(self.game.p1, 0)
        self.assertFalse(self.game.board.cells[0].is_open)

    def test_shuffle_magic_preserves_physical_cards(self):
        self.game.p1.hand = [16]
        before = sorted((c.card_type, c.card_id) for c in self.game.board.cells)
        self.game.play_magic(self.game.p1, 0)
        after = sorted((c.card_type, c.card_id) for c in self.game.board.cells)
        self.assertEqual(before, after)
        self.assertEqual([], self.game.p1.hand)

    def test_numerical_modification_happens_before_whole_conversion(self):
        self.game.pending_board_effects = [7, 12]
        distribution = self.game.resolve_next_distribution()
        self.assertEqual({"bomb": 13, "frog": 5, "empty": 0, "magic": 5, "figure": 2}, distribution)

    def test_numerical_transfer_cannot_make_a_count_negative(self):
        self.game.pending_board_effects = [10, 10, 10]
        distribution = self.game.resolve_next_distribution()
        self.assertEqual(0, distribution["magic"])
        self.assertEqual(13, distribution["empty"])
        self.assertEqual(25, sum(distribution.values()))

    def test_whole_conversions_follow_play_order(self):
        self.game.pending_board_effects = [12, 14]
        distribution = self.game.resolve_next_distribution()
        self.assertEqual(13, distribution["bomb"])
        self.assertEqual(2, distribution["figure"])
        self.assertEqual(0, distribution["empty"])

    def test_const_figure_blocks_change_but_card_stays_open(self):
        self.game.p1.figure_lock_turns = 3
        self.game.board.cells[0] = Cell("figure", 0, card_id=208)
        self.game.open_card(self.game.p1, 0)
        self.assertEqual(200, self.game.p1.figure_id)
        self.assertTrue(self.game.board.cells[0].is_open)

    def test_copy_cat_copies_once(self):
        self.game.p2.figure_id = 208
        self.game.board.cells[0] = Cell("figure", 0, card_id=212)
        self.game.open_card(self.game.p1, 0)
        self.game.p2.figure_id = 214
        self.assertEqual(208, self.game.p1.figure_id)

    def test_simultaneous_death_is_draw(self):
        self.game.p1.take_damage(5)
        self.game.p2.take_damage(5)
        self.assertEqual("draw", self.game.game_result())

    def test_unsupported_magic_is_not_consumed(self):
        self.game.p1.hand = [17]
        with self.assertRaises(NotImplementedError):
            self.game.play_magic(self.game.p1, 0)
        self.assertEqual([17], self.game.p1.hand)


if __name__ == "__main__":
    unittest.main()
