"""Shared-screen terminal interface for the card game."""

from board import Visibility
from cards import FIGURE_CARDS, MAGIC_CARDS
from game import Game


class TerminalGame:
    def __init__(self, game=None):
        self.game = game or Game()

    def run(self):
        print("VIRTUAL TABLETOP CARD GAME")
        print("Each step: play one Magic Card or Open one board card.\n")
        while self.game.game_result() is None:
            self._print_messages(self.game.start_turn())
            if self.game.game_result() is not None:
                break
            order = " -> ".join(player.name for player in self.game.steps_order)
            print(f"\nTURN {self.game.turn_number}\nStep order: {order}")
            for player in self.game.steps_order:
                if self.game.game_result() is not None:
                    break
                self._run_step(player)
            if self.game.game_result() is None and input("Continue to next turn? (y/n): ").strip().lower() != "y":
                print("Game ended by player")
                return
        result = self.game.game_result()
        print("GAME OVER: draw" if result == "draw" else f"GAME OVER: {result} wins")

    def _run_step(self, player):
        print(f"\n--- {player.name}'s step ---")
        self.show_state()
        while True:
            try:
                foreteller = self._choose_foreteller(player)
                barriers = self._choose_barriers(player)
                self._print_messages(self.game.begin_step(player, foreteller_indices=foreteller, barrier_indices=barriers))
                break
            except (IndexError, ValueError) as error:
                print(f"Invalid step-start choice: {error}")
        forced_index = self.game.forced_magic_index(player)
        if forced_index is not None:
            card = MAGIC_CARDS[player.hand[forced_index].card_id]
            print(f"CURSE: {player.name} must play {card.name}")
            if not self.game.can_resolve_forced_magic(player, forced_index):
                self._print_messages(self.game.fizzle_forced_magic(player, forced_index))
                self.game.complete_step(player)
                return
            while True:
                try:
                    choices = self._magic_choices(player, forced_index)
                    self._print_messages(self.game.play_magic(player, forced_index, choices, forced=True))
                    break
                except (IndexError, ValueError) as error:
                    print(f"Invalid forced-card choice: {error}")
            self.game.complete_step(player)
            return

        while True:
            try:
                action = self._choose_action(player)
                if action == "magic":
                    index = self._choose_hand_card(player)
                    self._print_messages(self.game.play_magic(player, index, self._magic_choices(player, index)))
                elif action == "figure":
                    self._print_messages(self.game.activate_figure(player))
                else:
                    self._open_action(player)
                self.game.complete_step(player)
                return
            except (IndexError, ValueError) as error:
                print(f"Invalid action: {error}")

    def _choose_action(self, player):
        options = [("open", "Open a board card")]
        if any(not card.cursed for card in player.hand):
            options.insert(0, ("magic", "Play a Magic Card"))
        if player.figure_id == 216 and 216 not in player.used_figure_abilities:
            options.append(("figure", "Use Magician Shuffle"))
        for number, (_, label) in enumerate(options, 1):
            print(f"{number}. {label}")
        raw = int(input("Choose action: ")) - 1
        if not 0 <= raw < len(options):
            raise ValueError("invalid action number")
        return options[raw][0]

    def _open_action(self, player):
        requested = None if player.figure_id == 211 else int(input("Board index (0-24): "))
        index = self.game.choose_open_index(player, requested)
        if player.figure_id == 211:
            print(f"Alcoholic randomly chooses #{index}")
        cell = self.game.board._require_cell(index)
        discards = ()
        if cell.card_type == "magic" and len(player.hand) == player.HAND_LIMIT:
            print(f"Revealed Magic: {MAGIC_CARDS[cell.card_id].name}")
            self._show_hand(player)
            discards = self._read_indices("Choose exactly 2 hand indices to discard: ")
        self._print_messages(self.game.open_card(player, index, discard_indices=discards))

    def _choose_hand_card(self, player):
        self._show_hand(player)
        index = int(input("Magic Card index: "))
        if player.hand_card_at(index).cursed:
            raise ValueError("that card is cursed")
        return index

    def _magic_choices(self, player, hand_index):
        card = MAGIC_CARDS[player.hand_card_at(hand_index).card_id]
        choices = {}
        if card.effect_type == "reveal":
            choices["indices"] = self._read_indices(f"Choose exactly {card.effect_data['count']} Face-down board indices: ")
        elif card.effect_type in {"change_figure", "protect_figure"}:
            choices["target"] = self._choose_player(player)
        elif card.effect_type == "discard":
            self._show_hand(player)
            choices["own_index"] = int(input("Your other card to discard: "))
            opponent = self.game.get_other_player(player)
            self._show_hand(opponent)
            choices["opponent_index"] = int(input("Opponent card to discard: "))
        elif card.effect_type == "curse":
            opponent = self.game.get_other_player(player)
            self._show_hand(opponent)
            choices["opponent_index"] = int(input("Opponent card to curse: "))
        return choices

    def _choose_player(self, active):
        raw = input("Target self or opponent? (s/o): ").strip().lower()
        if raw == "s":
            return active
        if raw == "o":
            return self.game.get_other_player(active)
        raise ValueError("target must be 's' or 'o'")

    def _choose_foreteller(self, player):
        if player.steps_taken_this_turn or player.figure_id != 206:
            return ()
        count = min(3, sum(c.visibility is Visibility.FACE_DOWN for c in self.game.board.cells))
        return () if count == 0 else self._read_indices(f"Foreteller: choose exactly {count} cards to Reveal: ")

    def _choose_barriers(self, active):
        choices = {}
        for owner in (active, self.game.get_other_player(active)):
            if owner.figure_id == 209:
                raw = input(f"{owner.name}: place X index, or Enter to skip: ").strip()
                choices[owner] = None if not raw else int(raw)
        return choices

    def show_state(self):
        self.game.board.display_player_view()
        for player in self.game.players:
            print(f"{player.name}: HP {player.hp:.1f}/{player.max_hp:.1f}, Figure {FIGURE_CARDS[player.figure_id].name}")
            self._show_hand(player)

    @staticmethod
    def _show_hand(player):
        if not player.hand:
            print(f"{player.name} hand: empty")
            return
        rendered = [f"{i}: {MAGIC_CARDS[c.card_id].name}{' [CURSED]' if c.cursed else ''}" for i, c in enumerate(player.hand)]
        print(f"{player.name} hand: " + " | ".join(rendered))

    @staticmethod
    def _read_indices(prompt):
        return tuple(int(value) for value in input(prompt).replace(",", " ").split())

    @staticmethod
    def _print_messages(messages):
        for message in messages:
            print(message)
