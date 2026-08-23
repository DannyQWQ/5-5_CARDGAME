"""Pure game-flow orchestration. Terminal input/output lives in ``cli.py``."""

import random

from board import Board, Visibility
from cards import MAGIC_CARDS
from effects import EffectEngine
from player import Player


class Game:
    STEPS_PER_PLAYER = 3

    def __init__(self, p1_name="Player 1", p2_name="Player 2", *, rng=None):
        self.rng = rng or random.Random()
        self.p1 = Player(p1_name)
        self.p2 = Player(p2_name)
        self.board = Board(rng=self.rng)
        self.effects = EffectEngine(self)
        self.turn_number = 0
        self.current_step = 0
        self.steps_order: list[Player] = []
        self.pending_board_effects: list[int] = []

    @property
    def players(self):
        return self.p1, self.p2

    def get_other_player(self, player):
        if player is self.p1:
            return self.p2
        if player is self.p2:
            return self.p1
        raise ValueError("player does not belong to this game")

    def generate_turn_order(self):
        order = [self.p1] * self.STEPS_PER_PLAYER + [self.p2] * self.STEPS_PER_PLAYER
        self.rng.shuffle(order)
        self.steps_order = order
        return tuple(order)

    def start_turn(self):
        self.board.clear_temporary_reveals()
        self.board.clear_barriers()
        if self.turn_number > 0:
            distribution = self.effects.resolve_next_distribution()
            self.board = Board(distribution, rng=self.rng)
            self.pending_board_effects.clear()

        self.turn_number += 1
        self.current_step = 0
        for player in self.players:
            player.reset_for_turn()
        messages = self.effects.resolve_turn_start_figures()
        if self.game_result() is None:
            self.generate_turn_order()
        else:
            self.steps_order = []
        return messages

    def begin_step(self, player, *, foreteller_indices=(), barrier_indices=None):
        """Resolve automatic step-start effects before the main/forced action."""
        if player not in self.players:
            raise ValueError("player does not belong to this game")
        messages = []
        if player.steps_taken_this_turn == 0 and player.figure_id == 206:
            eligible = [
                c.cell_id for c in self.board.cells
                if c.visibility is Visibility.FACE_DOWN
            ]
            required = min(3, len(eligible))
            indices = tuple(foreteller_indices)
            if len(indices) != required:
                raise ValueError(f"Foreteller must Reveal exactly {required} cards")
            if len(set(indices)) != len(indices) or any(index not in eligible for index in indices):
                raise ValueError("Foreteller targets must be different Face-down cards")

        barriers = barrier_indices or {}
        planned_barriers = []
        for owner in (player, self.get_other_player(player)):
            if owner.figure_id != 209:
                continue
            index = barriers.get(owner)
            if index is not None:
                cell = self.board._require_cell(index)
                if cell.visibility is Visibility.OPENED or cell.barrier or index in [i for _, i in planned_barriers]:
                    raise ValueError("X requires a different card that is not Opened or already blocked")
                planned_barriers.append((owner, index))

        if player.steps_taken_this_turn == 0 and player.figure_id == 206:
            self.board.reveal(foreteller_indices)
            messages.append(f"{player.name}'s Foreteller Reveals {len(tuple(foreteller_indices))} cards")
        for owner, index in planned_barriers:
            self.board.place_barrier(index)
            messages.append(f"{owner.name} places X on #{index}")
        return messages

    def forced_magic_index(self, player):
        cursed = player.cursed_card
        return player.hand.index(cursed) if cursed is not None else None

    def choose_open_index(self, player, requested_index=None):
        if player.figure_id == 211:
            choices = self.board.selectable_indices()
            if not choices:
                raise ValueError("there are no cards Alcoholic can Open")
            return self.rng.choice(choices)
        if requested_index is None:
            raise ValueError("a board index is required")
        return requested_index

    def open_card(self, player, index, *, discard_indices=()):
        return self.effects.open_card(player, index, discard_indices=discard_indices)

    def play_magic(self, player, hand_index, choices=None, *, forced=False):
        return self.effects.play_magic(player, hand_index, choices, forced=forced)

    def can_resolve_forced_magic(self, player, hand_index):
        return self.effects.can_resolve_magic(player, hand_index, forced=True)

    def fizzle_forced_magic(self, player, hand_index):
        card = player.hand_card_at(hand_index)
        if not card.cursed:
            raise ValueError("only a cursed card can fizzle as a forced action")
        player.remove_hand_card(card)
        return [f"Cursed {MAGIC_CARDS[card.card_id].name} has no legal resolution; it is discarded"]

    def activate_figure(self, player):
        return self.effects.activate_magician(player)

    def complete_step(self, player):
        player.steps_taken_this_turn += 1
        self.current_step += 1

    def resolve_next_distribution(self):
        return self.effects.resolve_next_distribution()

    def game_result(self):
        p1_dead, p2_dead = not self.p1.is_alive(), not self.p2.is_alive()
        if p1_dead and p2_dead:
            return "draw"
        if p1_dead:
            return self.p2.name
        if p2_dead:
            return self.p1.name
        return None
