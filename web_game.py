"""Stateful adapter between the pure game core and local web clients."""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass

from board import Visibility
from cards import FIGURE_CARDS, MAGIC_CARDS
from game import Game


class WebGameError(ValueError):
    """A user-correctable web action error with machine-readable details."""

    def __init__(self, message, *, code="invalid_action", details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


@dataclass(slots=True)
class StepStartRequirement:
    foreteller_count: int = 0
    barrier_player_ids: tuple[str, ...] = ()


class WebGameSession:
    """Own one local shared-screen match and expose JSON-friendly state."""

    def __init__(self, p1_name="Player 1", p2_name="Player 2", *, seed=None):
        self.log: list[str] = []
        self.phase = "setup"
        self.step_start = StepStartRequirement()
        self.game = None
        self.new_game(p1_name, p2_name, seed=seed)

    def new_game(self, p1_name="Player 1", p2_name="Player 2", *, seed=None):
        rng = random.Random(seed)
        self.game = Game(p1_name or "Player 1", p2_name or "Player 2", rng=rng)
        self.log = ["A new game begins."]
        self._record(self.game.start_turn())
        self._prepare_current_step()
        return self.state()

    def _player_id(self, player):
        return "p1" if player is self.game.p1 else "p2"

    def _player_by_id(self, player_id):
        if player_id == "p1":
            return self.game.p1
        if player_id == "p2":
            return self.game.p2
        raise WebGameError("target player must be p1 or p2")

    @property
    def current_player(self):
        if self.game.game_result() is not None or not self.game.steps_order or self.game.current_step >= len(self.game.steps_order):
            return None
        return self.game.steps_order[self.game.current_step]

    def _record(self, messages):
        self.log.extend(messages)
        self.log = self.log[-40:]

    def _prepare_current_step(self):
        result = self.game.game_result()
        if result is not None:
            self.phase = "game_over"
            self.step_start = StepStartRequirement()
            return

        player = self.current_player
        face_down = sum(cell.visibility is Visibility.FACE_DOWN for cell in self.game.board.cells)
        foreteller_count = min(3, face_down) if player.steps_taken_this_turn == 0 and player.figure_id == 206 else 0
        barrier_players = tuple(
            self._player_id(owner)
            for owner in (player, self.game.get_other_player(player))
            if owner.figure_id == 209
        )
        self.step_start = StepStartRequirement(foreteller_count, barrier_players)
        if foreteller_count or barrier_players:
            self.phase = "step_start"
            return

        self._record(self.game.begin_step(player))
        self.phase = "action"
        self._resolve_impossible_curse()

    def _resolve_impossible_curse(self):
        player = self.current_player
        forced_index = self.game.forced_magic_index(player)
        if forced_index is None or self.game.can_resolve_forced_magic(player, forced_index):
            return
        self._record(self.game.fizzle_forced_magic(player, forced_index))
        self._finish_step(player)

    def begin_step(self, *, foreteller_indices=(), barrier_indices=None):
        if self.phase != "step_start":
            raise WebGameError("the current step has already started")
        player = self.current_player
        indices = tuple(foreteller_indices)
        barriers = {
            self._player_by_id(owner_id): index
            for owner_id, index in (barrier_indices or {}).items()
            if index is not None
        }
        try:
            self._record(self.game.begin_step(player, foreteller_indices=indices, barrier_indices=barriers))
        except (IndexError, ValueError) as error:
            raise WebGameError(str(error)) from error
        self.phase = "action"
        self.step_start = StepStartRequirement()
        self._resolve_impossible_curse()
        return self.state()

    def open_card(self, index, *, discard_indices=()):
        self._require_action_phase()
        player = self.current_player
        forced_index = self.game.forced_magic_index(player)
        if forced_index is not None:
            raise WebGameError("this step is cursed; the marked Magic Card must be played")
        try:
            chosen = self.game.choose_open_index(player, index)
            cell = self.game.board._require_cell(chosen)
            if cell.card_type == "magic" and len(player.hand) == player.HAND_LIMIT and not discard_indices:
                legal = [i for i, card in enumerate(player.hand) if not card.cursed]
                raise WebGameError(
                    "Your hand is full. Choose exactly two cards to discard.",
                    code="discard_required",
                    details={"hand_indices": legal, "board_index": chosen},
                )
            self._record(self.game.open_card(player, chosen, discard_indices=tuple(discard_indices)))
        except WebGameError:
            raise
        except (IndexError, ValueError) as error:
            raise WebGameError(str(error)) from error
        self._finish_step(player)
        return self.state()

    def play_magic(self, hand_index, choices=None):
        self._require_action_phase()
        player = self.current_player
        forced_index = self.game.forced_magic_index(player)
        forced = forced_index is not None
        if forced and hand_index != forced_index:
            raise WebGameError("the cursed card is the only legal action this step")
        normalized = dict(choices or {})
        if "target" in normalized:
            normalized["target"] = self._player_by_id(normalized["target"])
        try:
            self._record(self.game.play_magic(player, hand_index, normalized, forced=forced))
        except (IndexError, ValueError, TypeError) as error:
            raise WebGameError(str(error)) from error
        self._finish_step(player)
        return self.state()

    def activate_figure(self):
        self._require_action_phase()
        player = self.current_player
        if self.game.forced_magic_index(player) is not None:
            raise WebGameError("a cursed Magic Card must resolve first")
        try:
            self._record(self.game.activate_figure(player))
        except ValueError as error:
            raise WebGameError(str(error)) from error
        self._finish_step(player)
        return self.state()

    def continue_turn(self):
        if self.phase != "turn_end":
            raise WebGameError("the current turn is not waiting to continue")
        self._record(self.game.start_turn())
        self._prepare_current_step()
        return self.state()

    def _require_action_phase(self):
        if self.phase != "action" or self.current_player is None:
            raise WebGameError("the game is not waiting for a main action")

    def _finish_step(self, player):
        self.game.complete_step(player)
        result = self.game.game_result()
        if result is not None:
            self.phase = "game_over"
            self.log.append("The game ends in a draw." if result == "draw" else f"{result} wins.")
            return
        if self.game.current_step >= len(self.game.steps_order):
            self.phase = "turn_end"
            self.step_start = StepStartRequirement()
            self.log.append(f"Turn {self.game.turn_number} is complete. Review the final board before continuing.")
            return
        self._prepare_current_step()

    def state(self):
        current = self.current_player
        forced_index = self.game.forced_magic_index(current) if current and self.phase == "action" else None
        current_distribution = Counter(cell.card_type for cell in self.game.board.cells)
        return {
            "phase": self.phase,
            "turn": self.game.turn_number,
            "step": self.game.current_step,
            "step_order": [self._player_id(player) for player in self.game.steps_order],
            "current_player_id": self._player_id(current) if current else None,
            "forced_hand_index": forced_index,
            "result": self.game.game_result(),
            "step_start": {
                "foreteller_count": self.step_start.foreteller_count,
                "barrier_player_ids": list(self.step_start.barrier_player_ids),
            },
            "players": [self._serialize_player(player) for player in self.game.players],
            "board_distribution": {
                "current": dict(current_distribution),
                "next": self.game.resolve_next_distribution(),
            },
            "board": [self._serialize_cell(cell) for cell in self.game.board.cells],
            "selectable_indices": list(self.game.board.selectable_indices()),
            "log": list(self.log),
        }

    def _serialize_player(self, player):
        figure = FIGURE_CARDS[player.figure_id]
        return {
            "id": self._player_id(player),
            "name": player.name,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "figure": {
                "id": figure.card_id,
                "name": figure.name,
                "description": figure.description,
                "used": figure.card_id in player.used_figure_abilities,
            },
            "hand": [
                {
                    "index": index,
                    "id": card.card_id,
                    "name": MAGIC_CARDS[card.card_id].name,
                    "description": MAGIC_CARDS[card.card_id].description,
                    "effect_type": MAGIC_CARDS[card.card_id].effect_type,
                    "effect_data": dict(MAGIC_CARDS[card.card_id].effect_data),
                    "cursed": card.cursed,
                }
                for index, card in enumerate(player.hand)
            ],
        }

    @staticmethod
    def _serialize_cell(cell):
        visible = cell.visibility is not Visibility.FACE_DOWN
        data = {
            "index": cell.cell_id,
            "visibility": cell.visibility.value,
            "barrier": cell.barrier,
            "kind": cell.card_type if visible else None,
            "id": cell.card_id if visible else None,
            "name": "Unknown card",
            "description": "This card is face-down. Open it to reveal and resolve it.",
        }
        if not visible:
            return data
        if cell.card_type == "magic":
            card = MAGIC_CARDS[cell.card_id]
            data.update(name=card.name, description=card.description, effect_type=card.effect_type)
        elif cell.card_type == "figure":
            card = FIGURE_CARDS[cell.card_id]
            data.update(name=card.name, description=card.description)
        else:
            descriptions = {
                "bomb": "Take 1 damage before figure modifiers.",
                "frog": "No base effect; some figures change what Frog does.",
                "empty": "No base effect.",
            }
            data.update(name=cell.card_type.title(), description=descriptions[cell.card_type])
        return data
