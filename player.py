"""Player-owned state and invariants."""

from dataclasses import dataclass


@dataclass(slots=True, eq=False)
class HandCard:
    card_id: int
    cursed: bool = False


class Player:
    HAND_LIMIT = 3

    def __init__(self, name, hp=5.0, figure_id=200):
        self.name = name
        self.hp = float(hp)
        self.max_hp = float(hp)
        self.hand: list[HandCard] = []
        self.figure_id = figure_id
        self.figure_lock_turns = 0
        self.used_figure_abilities: set[int] = set()
        self.steps_taken_this_turn = 0

    @property
    def hand_ids(self):
        return [card.card_id for card in self.hand]

    @property
    def cursed_card(self):
        return next((card for card in self.hand if card.cursed), None)

    def take_damage(self, amount):
        if amount < 0:
            raise ValueError("damage cannot be negative")
        before = self.hp
        self.hp = max(0.0, self.hp - amount)
        return before - self.hp

    def heal(self, amount):
        if amount < 0:
            raise ValueError("healing cannot be negative")
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def receive_magic(self, card_id, discard_indices=()):
        if len(self.hand) < self.HAND_LIMIT:
            if discard_indices:
                raise ValueError("discarding is only allowed when the hand is full")
            self.hand.append(HandCard(card_id))
            return []

        indices = tuple(discard_indices)
        if len(indices) != 2 or len(set(indices)) != 2:
            raise ValueError("a full hand must discard exactly two different cards")
        if any(index < 0 or index >= len(self.hand) for index in indices):
            raise IndexError("discard index is outside the hand")
        selected = [self.hand[index] for index in indices]
        if any(card.cursed for card in selected):
            raise ValueError("a cursed card cannot be discarded")
        for card in selected:
            self.hand.remove(card)
        self.hand.append(HandCard(card_id))
        return selected

    def hand_card_at(self, index):
        if type(index) is not int or not 0 <= index < len(self.hand):
            raise IndexError("magic card index is outside the hand")
        return self.hand[index]

    def remove_hand_card(self, card):
        self.hand.remove(card)
        return card

    def change_figure(self, new_figure_id):
        if self.figure_lock_turns > 0:
            return False
        self.figure_id = new_figure_id
        return True

    def reset_for_turn(self):
        self.used_figure_abilities.clear()
        self.steps_taken_this_turn = 0
        if self.figure_lock_turns > 0:
            self.figure_lock_turns -= 1

    def is_alive(self):
        return self.hp > 0

    def __repr__(self):
        return f"Player({self.name}, HP={self.hp:.1f}/{self.max_hp:.1f}, Figure=#{self.figure_id}, Hand={len(self.hand)})"
