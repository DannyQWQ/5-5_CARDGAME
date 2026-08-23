import random
import unittest

from board import Cell, Visibility
from game import Game
from player import HandCard


class EffectTests(unittest.TestCase):
    def setUp(self):
        self.game = Game("A", "B", rng=random.Random(7))

    def test_magic_identity_is_not_rerolled_when_opened(self):
        self.game.board.cells[0] = Cell("magic", 0, card_id=17)
        self.game.open_card(self.game.p1, 0)
        self.assertEqual([17], self.game.p1.hand_ids)

    def test_take_a_look_reveals_without_opening(self):
        self.game.p1.hand = [HandCard(17)]
        self.game.play_magic(self.game.p1, 0, {"indices": (0,)})
        self.assertEqual(Visibility.REVEALED, self.game.board.cells[0].visibility)
        self.game.open_card(self.game.p1, 0)
        self.assertEqual(Visibility.OPENED, self.game.board.cells[0].visibility)

    def test_reveal_all_magic_only_reveals_unopened_magic(self):
        self.game.p1.hand = [HandCard(22)]
        self.game.board.cells[0] = Cell("magic", 0, card_id=1)
        self.game.board.cells[1] = Cell("magic", 1, card_id=2, visibility=Visibility.OPENED)
        self.game.play_magic(self.game.p1, 0)
        self.assertEqual(Visibility.REVEALED, self.game.board.cells[0].visibility)
        self.assertEqual(Visibility.OPENED, self.game.board.cells[1].visibility)

    def test_shredder_requires_cards_on_both_sides_and_does_not_consume_on_failure(self):
        self.game.p1.hand = [HandCard(21), HandCard(1)]
        with self.assertRaises(IndexError):
            self.game.play_magic(self.game.p1, 0, {"own_index": 1, "opponent_index": 0})
        self.assertEqual([21, 1], self.game.p1.hand_ids)

    def test_shredder_discards_selected_cards(self):
        self.game.p1.hand = [HandCard(21), HandCard(1)]
        self.game.p2.hand = [HandCard(2)]
        self.game.play_magic(self.game.p1, 0, {"own_index": 1, "opponent_index": 0})
        self.assertEqual([], self.game.p1.hand)
        self.assertEqual([], self.game.p2.hand)

    def test_curse_forces_opponent_card_but_opponent_chooses_target(self):
        self.game.p1.figure_id = 208
        self.game.p1.hand = [HandCard(23)]
        self.game.p2.hand = [HandCard(19)]
        self.game.play_magic(self.game.p1, 0, {"opponent_index": 0})
        forced = self.game.forced_magic_index(self.game.p2)
        self.assertEqual(0, forced)
        self.game.play_magic(self.game.p2, forced, {"target": self.game.p1}, forced=True)
        self.assertEqual(200, self.game.p1.figure_id)
        self.assertEqual([], self.game.p2.hand)

    def test_swap_is_invalid_while_a_cursed_card_exists(self):
        self.game.p1.hand = [HandCard(25)]
        self.game.p2.hand = [HandCard(1, cursed=True)]
        with self.assertRaises(ValueError):
            self.game.play_magic(self.game.p1, 0)
        self.assertEqual([25], self.game.p1.hand_ids)

    def test_cursed_swap_can_resolve_because_it_removes_its_own_curse(self):
        self.game.p1.hand = [HandCard(25, cursed=True)]
        self.game.p2.hand = [HandCard(1)]
        self.game.play_magic(self.game.p1, 0, forced=True)
        self.assertEqual([1], self.game.p1.hand_ids)
        self.assertEqual([], self.game.p2.hand_ids)

    def test_impossible_cursed_shredder_fizzles_and_consumes_step_card(self):
        self.game.p1.hand = [HandCard(21, cursed=True)]
        self.assertFalse(self.game.can_resolve_forced_magic(self.game.p1, 0))
        self.game.fizzle_forced_magic(self.game.p1, 0)
        self.assertEqual([], self.game.p1.hand)

    def test_abusive_lover_mirrors_actual_healing_once(self):
        self.game.p1.figure_id = 213
        self.game.p1.hp = 4.5
        self.game.p2.hp = 4.0
        self.game.effects.heal(self.game.p1, 3)
        self.assertEqual(5.0, self.game.p1.hp)
        self.assertEqual(4.5, self.game.p2.hp)

    def test_abusive_lover_damage_can_make_a_draw(self):
        self.game.p1.figure_id = 213
        self.game.p1.hp = self.game.p2.hp = 1
        self.game.effects.damage(self.game.p1, 1)
        self.assertEqual("draw", self.game.game_result())

    def test_w_pattern_uses_only_active_players_figure_once(self):
        self.game.p1.figure_id = 202
        self.game.p2.figure_id = 203
        self.game.p1.hp = 4
        self.game.board.cells[0] = Cell("empty", 0)
        self.game.board.cells[2] = Cell("empty", 2)
        self.game.open_card(self.game.p1, 0)
        self.assertEqual(5, self.game.p1.hp)
        self.assertEqual(4, self.game.p2.hp)
        self.game.open_card(self.game.p1, 2)
        self.assertEqual(5, self.game.p1.hp)
        self.assertEqual(4, self.game.p2.hp)

    def test_princess_frog_heals_only_once_per_turn(self):
        self.game.p1.figure_id = 207
        self.game.p1.hp = 3
        self.game.board.cells[0] = Cell("frog", 0)
        self.game.board.cells[1] = Cell("frog", 1)
        self.game.open_card(self.game.p1, 0)
        self.game.open_card(self.game.p1, 1)
        self.assertEqual(4, self.game.p1.hp)

    def test_gambler_frog_damages_opponent(self):
        self.game.p1.figure_id = 214
        self.game.board.cells[0] = Cell("frog", 0)
        self.game.open_card(self.game.p1, 0)
        self.assertEqual(4, self.game.p2.hp)

    def test_magician_shuffle_is_once_per_turn(self):
        self.game.p1.figure_id = 216
        self.game.activate_figure(self.game.p1)
        with self.assertRaises(ValueError):
            self.game.activate_figure(self.game.p1)

    def test_lucky_bob_can_avoid_a_damage_event(self):
        self.game.p1.figure_id = 217
        self.game.rng.random = lambda: 0.0
        self.game.effects.damage(self.game.p1, 3)
        self.assertEqual(5, self.game.p1.hp)

    def test_unlucky_bob_doubles_before_abusive_mirror(self):
        self.game.p1.figure_id = 218
        self.game.p2.figure_id = 213
        self.game.rng.random = lambda: 0.0
        self.game.effects.damage(self.game.p1, 1)
        self.assertEqual(3, self.game.p1.hp)
        self.assertEqual(3, self.game.p2.hp)


if __name__ == "__main__":
    unittest.main()
