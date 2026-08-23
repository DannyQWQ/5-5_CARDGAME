import random
import unittest

from board import Board, Visibility


class BoardTests(unittest.TestCase):
    def test_default_board_has_assigned_card_identities(self):
        board = Board(rng=random.Random(1))
        self.assertEqual(25, len(board.cells))
        self.assertTrue(all(c.card_id is not None for c in board.cells if c.card_type in {"magic", "figure"}))

    def test_distribution_invariants_are_enforced(self):
        with self.assertRaises(ValueError):
            Board({"bomb": 1, "frog": 1, "empty": 1, "magic": 1, "figure": 1})

    def test_revealed_card_can_still_be_opened(self):
        board = Board(rng=random.Random(2))
        board.reveal((0,))
        self.assertEqual(Visibility.REVEALED, board.cells[0].visibility)
        board.open_cell(0)
        self.assertEqual(Visibility.OPENED, board.cells[0].visibility)

    def test_temporary_reveal_closes_but_politician_reveal_persists(self):
        board = Board(rng=random.Random(3))
        board.reveal((0,), temporary=True)
        board.reveal((1,), temporary=False)
        board.clear_temporary_reveals()
        self.assertEqual(Visibility.FACE_DOWN, board.cells[0].visibility)
        self.assertEqual(Visibility.REVEALED, board.cells[1].visibility)

    def test_politician_inverts_all_visibility_without_opening(self):
        board = Board(rng=random.Random(4))
        board.open_cell(0)
        board.reveal((1,))
        board.invert_visibility()
        self.assertEqual(Visibility.FACE_DOWN, board.cells[0].visibility)
        self.assertEqual(Visibility.FACE_DOWN, board.cells[1].visibility)
        self.assertEqual(Visibility.REVEALED, board.cells[2].visibility)

    def test_barrier_blocks_open_but_not_reveal(self):
        board = Board(rng=random.Random(5))
        board.place_barrier(0)
        board.reveal((0,))
        with self.assertRaises(ValueError):
            board.open_cell(0)

    def test_shuffle_preserves_cards_and_clears_runtime_state(self):
        board = Board(rng=random.Random(6))
        board.open_cell(0)
        board.place_barrier(1)
        before = sorted((c.card_type, c.card_id) for c in board.cells)
        board.shuffle()
        self.assertEqual(before, sorted((c.card_type, c.card_id) for c in board.cells))
        self.assertTrue(all(c.visibility is Visibility.FACE_DOWN and not c.barrier for c in board.cells))


if __name__ == "__main__":
    unittest.main()
