import unittest

from cards import DRAWABLE_FIGURE_IDS, FIGURE_CARDS, MAGIC_CARDS


class CardDataTests(unittest.TestCase):
    def test_all_magic_ids_exist_except_intentionally_unused_legacy_gap(self):
        self.assertEqual(set(range(1, 26)), set(MAGIC_CARDS))

    def test_evolved_pawn_figures_are_not_drawable(self):
        self.assertTrue({202, 203, 204, 205}.isdisjoint(DRAWABLE_FIGURE_IDS))

    def test_catalog_keys_match_embedded_ids(self):
        self.assertTrue(all(key == card.card_id for key, card in MAGIC_CARDS.items()))
        self.assertTrue(all(key == card.card_id for key, card in FIGURE_CARDS.items()))


if __name__ == "__main__":
    unittest.main()
