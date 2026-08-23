import unittest

from player import HandCard, Player


class PlayerTests(unittest.TestCase):
    def test_full_hand_must_discard_exactly_two(self):
        player = Player("A")
        player.hand = [HandCard(1), HandCard(2), HandCard(3)]
        with self.assertRaises(ValueError):
            player.receive_magic(4)
        discarded = player.receive_magic(4, (0, 2))
        self.assertEqual([1, 3], [card.card_id for card in discarded])
        self.assertEqual([2, 4], player.hand_ids)

    def test_cursed_card_cannot_pay_full_hand_discard(self):
        player = Player("A")
        player.hand = [HandCard(1, cursed=True), HandCard(2), HandCard(3)]
        with self.assertRaises(ValueError):
            player.receive_magic(4, (0, 1))
        self.assertEqual([1, 2, 3], player.hand_ids)

    def test_figure_lock_blocks_change(self):
        player = Player("A")
        player.figure_lock_turns = 2
        self.assertFalse(player.change_figure(208))
        self.assertEqual(200, player.figure_id)


if __name__ == "__main__":
    unittest.main()
