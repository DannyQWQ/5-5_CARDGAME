"""Game rules, turn orchestration, and terminal adapter.

``Game`` coordinates Board, Player, and card data. Those lower-level modules do
not know about turn order or resolve one another's effects.
"""

from collections import Counter
import random

from board import Board, CARD_TYPES
from cards import FIGURE_CARDS, MAGIC_CARDS
from player import Player


class Game:
    STEPS_PER_PLAYER = 3

    def __init__(self, p1_name="Player 1", p2_name="Player 2", *, rng=None):
        self.rng = rng or random.Random()
        self.p1 = Player(p1_name)
        self.p2 = Player(p2_name)
        self.board = Board(rng=self.rng)
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
        self.turn_number += 1
        self.current_step = 0
        for player in self.players:
            player.reset_turn_usage()
            player.advance_figure_lock()
        self.generate_turn_order()
        self._apply_turn_start_effects()

    def finish_turn(self):
        distribution = self.resolve_next_distribution()
        self.board = Board(distribution, rng=self.rng)
        self.pending_board_effects.clear()

    def _apply_turn_start_effects(self):
        # Turn-start damage is simultaneous, so two Witches can produce a draw.
        damage = {self.p1: 0, self.p2: 0}
        if self.p1.figure_id == 208:
            damage[self.p2] += 1
        if self.p2.figure_id == 208:
            damage[self.p1] += 1
        for player, amount in damage.items():
            player.take_damage(amount)

    def open_card(self, player, index, *, discard_indices=()):
        """Open one card and resolve it. This is one complete step action."""
        preview = self.board.peek_cell(index)
        if preview.card_type == "magic" and len(player.hand) == player.HAND_LIMIT:
            # Validate mandatory discards before mutating the board.
            indices = tuple(discard_indices)
            if len(indices) != 2 or len(set(indices)) != 2:
                raise ValueError("opening Magic with a full hand requires two discard indices")

        cell = self.board.open_cell(index)
        opponent = self.get_other_player(player)
        messages = [f"Opened {cell.card_type} at #{index}"]

        if cell.card_type == "bomb":
            damage = 1
            if player.figure_id == 214:
                damage = 2
            elif player.figure_id == 215:
                damage = 3
            elif player.figure_id == 217 and self.rng.random() < 0.30:
                damage = 0
            elif player.figure_id == 218 and self.rng.random() < 0.30:
                damage = 2
            player.take_damage(damage)
            messages.append(f"{player.name} takes {damage:g} damage")

        elif cell.card_type == "frog":
            if player.figure_id == 214:
                opponent.take_damage(1)
                messages.append(f"{opponent.name} takes 1 damage")
            elif player.figure_id == 207 and 207 not in player.used_figure_abilities:
                player.heal(1)
                player.used_figure_abilities.add(207)
                messages.append(f"{player.name} heals 1 HP")

        elif cell.card_type == "magic":
            discarded = player.receive_magic(cell.card_id, discard_indices)
            messages.append(f"{player.name} receives {MAGIC_CARDS[cell.card_id].name}")
            if discarded:
                names = ", ".join(MAGIC_CARDS[card_id].name for card_id in discarded)
                messages.append(f"Discarded: {names}")

        elif cell.card_type == "figure":
            old_figure = player.figure_id
            new_figure = opponent.figure_id if cell.card_id == 212 else cell.card_id
            changed = player.change_figure(new_figure)
            if changed:
                messages.append(
                    f"{FIGURE_CARDS[old_figure].name} changed to {FIGURE_CARDS[new_figure].name}"
                )
            else:
                messages.append("Figure change blocked by Const Figure")

        return messages

    def play_magic(self, player, hand_index, *, target_player=None):
        """Play one Magic Card and resolve it. Playing it ends the step."""
        if not 0 <= hand_index < len(player.hand):
            raise IndexError("magic card index is outside the hand")
        card_id = player.hand[hand_index]
        card = MAGIC_CARDS[card_id]
        target = target_player or player

        supported = {
            "heal", "heal_dual", "board_delta", "heal_and_board_delta",
            "convert_all", "convert_one", "shuffle", "change_figure",
            "protect_figure", "swap_hand",
        }
        if card.effect_type not in supported:
            raise NotImplementedError(f"{card.name} needs additional player choices")
        if target not in self.players:
            raise ValueError("target player does not belong to this game")

        player.use_magic_at(hand_index)
        data = card.effect_data
        opponent = self.get_other_player(player)

        if card.effect_type == "heal":
            player.heal(data["user"])
        elif card.effect_type == "heal_dual":
            player.heal(data["user"])
            opponent.heal(data["opponent"])
        elif card.effect_type == "heal_and_board_delta":
            player.heal(data["user"])
            self.pending_board_effects.append(card_id)
        elif card.effect_type in {"board_delta", "convert_all", "convert_one"}:
            self.pending_board_effects.append(card_id)
        elif card.effect_type == "shuffle":
            self.board.shuffle()
        elif card.effect_type == "change_figure":
            target.change_figure(data["figure_id"])
        elif card.effect_type == "protect_figure":
            target.figure_lock_turns = data["turns"]
        elif card.effect_type == "swap_hand":
            player.hand, opponent.hand = opponent.hand, player.hand

        return card

    def resolve_next_distribution(self):
        """Resolve numerical effects first, then conversions in play order."""
        distribution = dict(Board.DEFAULT_DISTRIBUTION)
        numerical = [MAGIC_CARDS[i] for i in self.pending_board_effects if MAGIC_CARDS[i].effect_type in {"board_delta", "heal_and_board_delta"}]
        conversions = [MAGIC_CARDS[i] for i in self.pending_board_effects if MAGIC_CARDS[i].effect_type in {"convert_all", "convert_one"}]

        totals = Counter()
        for card in numerical:
            totals.update({key: value for key, value in card.effect_data.items() if key in CARD_TYPES})

        # Every current numerical card transfers cards between types. Limit the
        # entire net transfer by what can actually be removed from each source.
        removals = {kind: min(distribution[kind], -change) for kind, change in totals.items() if change < 0}
        additions = {kind: change for kind, change in totals.items() if change > 0}
        removable = sum(removals.values())
        requested = sum(additions.values())
        for kind, amount in removals.items():
            distribution[kind] -= amount
        remaining = removable
        for position, (kind, amount) in enumerate(additions.items()):
            granted = remaining if position == len(additions) - 1 else min(amount, removable * amount // requested)
            distribution[kind] += granted
            remaining -= granted

        for card in conversions:
            source = card.effect_data["source"]
            target = card.effect_data["target"]
            amount = distribution[source] if card.effect_type == "convert_all" else min(1, distribution[source])
            distribution[source] -= amount
            distribution[target] += amount

        Board._validate_distribution(distribution)
        return distribution

    def game_result(self):
        p1_dead = not self.p1.is_alive()
        p2_dead = not self.p2.is_alive()
        if p1_dead and p2_dead:
            return "draw"
        if p1_dead:
            return self.p2.name
        if p2_dead:
            return self.p1.name
        return None

    def display_game_state(self):
        print("\nBOARD")
        self.board.display_player_view()
        for player in self.players:
            figure = FIGURE_CARDS[player.figure_id].name
            hand = ", ".join(MAGIC_CARDS[i].name for i in player.hand) or "empty"
            print(f"{player.name}: HP {player.hp:.1f}/{player.max_hp:.1f}, figure {figure}, hand [{hand}]")

    def execute_step(self, player):
        """Terminal input adapter; pure rule operations live in open_card/play_magic."""
        while True:
            self.display_game_state()
            has_hand = bool(player.hand)
            print("1. Play Magic Card" if has_hand else "1. Open a card")
            if has_hand:
                print("2. Open a card")
            choice = input(f"{player.name}, choose an action: ").strip()
            try:
                if has_hand and choice == "1":
                    for index, card_id in enumerate(player.hand):
                        print(f"{index}. {MAGIC_CARDS[card_id].name}")
                    hand_index = int(input("Choose Magic Card: "))
                    target = player
                    chosen_card = MAGIC_CARDS[player.hand[hand_index]]
                    if chosen_card.effect_type in {"change_figure", "protect_figure"}:
                        raw_target = input("Target self or opponent? (s/o): ").strip().lower()
                        if raw_target not in {"s", "o"}:
                            raise ValueError("target must be 's' or 'o'")
                        target = player if raw_target == "s" else self.get_other_player(player)
                    self.play_magic(player, hand_index, target_player=target)
                    return

                open_choice = "2" if has_hand else "1"
                if choice == open_choice:
                    index = int(input("Choose board index (0-24): "))
                    discard_indices = ()
                    cell = self.board.peek_cell(index)
                    if cell.card_type == "magic" and len(player.hand) == player.HAND_LIMIT:
                        for hand_index, card_id in enumerate(player.hand):
                            print(f"{hand_index}. {MAGIC_CARDS[card_id].name}")
                        raw = input("Hand full; choose exactly 2 indices to discard: ")
                        discard_indices = tuple(int(value) for value in raw.replace(",", " ").split())
                    for message in self.open_card(player, index, discard_indices=discard_indices):
                        print(message)
                    return
            except (IndexError, ValueError, NotImplementedError) as error:
                print(f"Invalid action: {error}")

    def run(self):
        print("VIRTUAL TABLETOP CARD GAME")
        while self.game_result() is None:
            self.start_turn()
            for player in self.steps_order:
                if self.game_result() is not None:
                    break
                self.current_step += 1
                self.execute_step(player)
            if self.game_result() is None:
                self.finish_turn()
                if input("Continue to next turn? (y/n): ").strip().lower() != "y":
                    print("Game ended by player")
                    return

        result = self.game_result()
        print("GAME OVER: draw" if result == "draw" else f"GAME OVER: {result} wins")
