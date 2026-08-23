"""Rule effect engine. All HP and card effects pass through this module."""

from collections import Counter

from board import Board, CARD_TYPES, Visibility
from cards import FIGURE_CARDS, MAGIC_CARDS


class EffectEngine:
    def __init__(self, game):
        self.game = game

    @property
    def rng(self):
        return self.game.rng

    def other(self, player):
        return self.game.get_other_player(player)

    def abusive_active(self):
        return any(player.figure_id == 213 for player in self.game.players)

    def heal(self, player, amount):
        actual = min(amount, player.max_hp - player.hp)
        changes = {player: actual}
        if self.abusive_active():
            changes[self.other(player)] = min(actual, self.other(player).max_hp - self.other(player).hp)
        for target, value in changes.items():
            target.hp += value
        return changes

    def _modified_damage(self, player, amount):
        if player.figure_id == 217 and self.rng.random() < 0.30:
            return 0.0
        if player.figure_id == 218 and self.rng.random() < 0.30:
            return amount * 2
        return amount

    def damage(self, player, amount):
        return self.damage_batch({player: amount})

    def damage_batch(self, requested):
        """Apply simultaneous damage, including one non-recursive abusive mirror."""
        original = {
            player: min(player.hp, self._modified_damage(player, amount))
            for player, amount in requested.items() if amount > 0
        }
        losses = Counter(original)
        if self.abusive_active():
            for player, actual in original.items():
                losses[self.other(player)] += actual
        applied = {player: min(player.hp, amount) for player, amount in losses.items()}
        for player, amount in applied.items():
            player.hp -= amount
        return applied

    def open_card(self, player, index, *, discard_indices=()):
        preview = self.game.board._require_cell(index)
        if preview.card_type == "magic" and len(player.hand) == player.HAND_LIMIT:
            self._validate_full_hand_discard(player, discard_indices)

        cell = self.game.board.open_cell(index)
        opponent = self.other(player)
        messages = [f"Opened {cell.card_type} at #{index}"]

        self._apply_w_pattern(player, index, messages)

        if cell.card_type == "bomb":
            amount = 2 if player.figure_id == 214 else 3 if player.figure_id == 215 else 1
            losses = self.damage(player, amount)
            messages.append(self._format_changes(losses, "damage"))
        elif cell.card_type == "frog":
            if player.figure_id == 214:
                messages.append(self._format_changes(self.damage(opponent, 1), "damage"))
            elif player.figure_id == 207 and 207 not in player.used_figure_abilities:
                player.used_figure_abilities.add(207)
                messages.append(self._format_changes(self.heal(player, 1), "healing"))
        elif cell.card_type == "magic":
            discarded = player.receive_magic(cell.card_id, discard_indices)
            messages.append(f"{player.name} receives {MAGIC_CARDS[cell.card_id].name}")
            if discarded:
                messages.append("Discarded: " + ", ".join(MAGIC_CARDS[c.card_id].name for c in discarded))
        elif cell.card_type == "figure":
            old_id = player.figure_id
            new_id = opponent.figure_id if cell.card_id == 212 else cell.card_id
            if player.change_figure(new_id):
                messages.append(f"{FIGURE_CARDS[old_id].name} changed to {FIGURE_CARDS[new_id].name}")
            else:
                messages.append("Figure change blocked by Const Figure")
        return messages

    def _apply_w_pattern(self, player, index, messages):
        figure = FIGURE_CARDS[player.figure_id]
        if not figure.board_pattern or player.figure_id in player.used_figure_abilities:
            return
        row, col = divmod(index, 5)
        if figure.board_pattern[row][col] != "W":
            return
        player.used_figure_abilities.add(player.figure_id)
        amount = 1 if player.figure_id == 202 else 0.5
        messages.append(self._format_changes(self.heal(player, amount), "healing"))
        messages.append(self._format_changes(self.damage(self.other(player), amount), "damage"))

    @staticmethod
    def _validate_full_hand_discard(player, indices):
        indices = tuple(indices)
        if len(indices) != 2 or len(set(indices)) != 2:
            raise ValueError("opening Magic with a full hand requires two discard indices")
        selected = [player.hand_card_at(index) for index in indices]
        if any(card.cursed for card in selected):
            raise ValueError("a cursed card cannot be discarded")

    def validate_magic(self, player, hand_index, choices=None, *, forced=False):
        choices = choices or {}
        hand_card = player.hand_card_at(hand_index)
        if hand_card.cursed and not forced:
            raise ValueError("a cursed card cannot be played voluntarily")
        card = MAGIC_CARDS[hand_card.card_id]
        opponent = self.other(player)

        if card.effect_type == "reveal":
            indices = tuple(choices.get("indices", ()))
            if len(indices) != card.effect_data["count"]:
                raise ValueError(f"{card.name} requires exactly {card.effect_data['count']} targets")
            if len(set(indices)) != len(indices):
                raise ValueError("Reveal targets must be different")
            for index in indices:
                if self.game.board._require_cell(index).visibility is not Visibility.FACE_DOWN:
                    raise ValueError("Reveal targets must be Face-down")
        elif card.effect_type in {"change_figure", "protect_figure"}:
            if choices.get("target") not in self.game.players:
                raise ValueError("this card requires a valid target player")
        elif card.effect_type == "discard":
            own = choices.get("own_index")
            theirs = choices.get("opponent_index")
            own_card = player.hand_card_at(own)
            opponent_card = opponent.hand_card_at(theirs)
            if own_card is hand_card or own_card.cursed or opponent_card.cursed:
                raise ValueError("Shredder requires one other non-cursed card from each player")
        elif card.effect_type == "curse":
            if opponent.cursed_card is not None:
                raise ValueError("opponent already has a cursed card")
            target = opponent.hand_card_at(choices.get("opponent_index"))
            if target.cursed or target.card_id == 23:
                raise ValueError("This is curse! cannot target that card")
        elif card.effect_type == "swap_hand":
            player_has_other_curse = any(c.cursed and c is not hand_card for c in player.hand)
            if player_has_other_curse or opponent.cursed_card:
                raise ValueError("Swap cannot be played while either hand contains a cursed card")
        return hand_card, card

    def can_resolve_magic(self, player, hand_index, *, forced=False):
        """Check whether at least one legal choice set exists without mutation."""
        hand_card = player.hand_card_at(hand_index)
        if hand_card.cursed and not forced:
            return False
        card = MAGIC_CARDS[hand_card.card_id]
        opponent = self.other(player)
        if card.effect_type == "reveal":
            available = sum(c.visibility is Visibility.FACE_DOWN for c in self.game.board.cells)
            return available >= card.effect_data["count"]
        if card.effect_type == "discard":
            own = any(c is not hand_card and not c.cursed for c in player.hand)
            theirs = any(not c.cursed for c in opponent.hand)
            return own and theirs
        if card.effect_type == "curse":
            return opponent.cursed_card is None and any(not c.cursed and c.card_id != 23 for c in opponent.hand)
        if card.effect_type == "swap_hand":
            return not any(c.cursed and c is not hand_card for c in player.hand) and opponent.cursed_card is None
        return True

    def play_magic(self, player, hand_index, choices=None, *, forced=False):
        choices = choices or {}
        hand_card, card = self.validate_magic(player, hand_index, choices, forced=forced)
        opponent = self.other(player)

        own_discard = opponent_discard = curse_target = None
        if card.effect_type == "discard":
            own_discard = player.hand_card_at(choices["own_index"])
            opponent_discard = opponent.hand_card_at(choices["opponent_index"])
        elif card.effect_type == "curse":
            curse_target = opponent.hand_card_at(choices["opponent_index"])

        player.remove_hand_card(hand_card)
        data = card.effect_data
        messages = [f"{player.name} plays {card.name}"]

        if card.effect_type == "heal":
            messages.append(self._format_changes(self.heal(player, data["user"]), "healing"))
        elif card.effect_type == "heal_dual":
            messages.append(self._format_changes(self.heal(player, data["user"]), "healing"))
            messages.append(self._format_changes(self.heal(opponent, data["opponent"]), "healing"))
        elif card.effect_type == "heal_and_board_delta":
            messages.append(self._format_changes(self.heal(player, data["user"]), "healing"))
            self.game.pending_board_effects.append(card.card_id)
        elif card.effect_type in {"board_delta", "convert_all", "convert_one"}:
            self.game.pending_board_effects.append(card.card_id)
        elif card.effect_type == "shuffle":
            self.game.board.shuffle()
        elif card.effect_type == "reveal":
            self.game.board.reveal(choices["indices"])
        elif card.effect_type == "reveal_all_magic":
            self.game.board.reveal_all_magic()
        elif card.effect_type == "change_figure":
            choices["target"].change_figure(data["figure_id"])
        elif card.effect_type == "protect_figure":
            choices["target"].figure_lock_turns = data["turns"]
        elif card.effect_type == "discard":
            player.remove_hand_card(own_discard)
            opponent.remove_hand_card(opponent_discard)
        elif card.effect_type == "curse":
            curse_target.cursed = True
        elif card.effect_type == "swap_hand":
            player.hand, opponent.hand = opponent.hand, player.hand
        return messages

    def activate_magician(self, player):
        if player.figure_id != 216:
            raise ValueError("player is not Magician")
        if 216 in player.used_figure_abilities:
            raise ValueError("Magician already shuffled this turn")
        player.used_figure_abilities.add(216)
        self.game.board.shuffle()
        return [f"{player.name} uses Magician Shuffle"]

    def resolve_turn_start_figures(self):
        messages = []
        for player in self.game.players:
            if player.figure_id == 201 and self.rng.random() < 0.10:
                new_id = self.rng.choice((202, 203, 204, 205))
                if player.change_figure(new_id):
                    messages.append(f"{player.name}'s Pawn evolves into {FIGURE_CARDS[new_id].name}")
        for player in self.game.players:
            if player.figure_id == 219:
                self.game.board.invert_visibility()
                messages.append(f"{player.name}'s Politician inverts the board")
        witch_damage = {}
        for player in self.game.players:
            if player.figure_id == 208:
                target = self.other(player)
                witch_damage[target] = witch_damage.get(target, 0) + 1
        if witch_damage:
            messages.append(self._format_changes(self.damage_batch(witch_damage), "damage"))
        return messages

    def resolve_next_distribution(self):
        distribution = dict(Board.DEFAULT_DISTRIBUTION)
        cards = [MAGIC_CARDS[card_id] for card_id in self.game.pending_board_effects]
        numerical = [c for c in cards if c.effect_type in {"board_delta", "heal_and_board_delta"}]
        conversions = [c for c in cards if c.effect_type in {"convert_all", "convert_one"}]
        totals = Counter()
        for card in numerical:
            totals.update({key: value for key, value in card.effect_data.items() if key in CARD_TYPES})
        removals = {kind: min(distribution[kind], -value) for kind, value in totals.items() if value < 0}
        additions = {kind: value for kind, value in totals.items() if value > 0}
        available = sum(removals.values())
        requested = sum(additions.values())
        for kind, amount in removals.items():
            distribution[kind] -= amount
        remaining = available
        for position, (kind, amount) in enumerate(additions.items()):
            granted = remaining if position == len(additions) - 1 else min(amount, available * amount // requested)
            distribution[kind] += granted
            remaining -= granted
        for card in conversions:
            source, target = card.effect_data["source"], card.effect_data["target"]
            amount = distribution[source] if card.effect_type == "convert_all" else min(1, distribution[source])
            distribution[source] -= amount
            distribution[target] += amount
        Board._validate_distribution(distribution)
        return distribution

    @staticmethod
    def _format_changes(changes, kind):
        if not changes:
            return f"No {kind}"
        return ", ".join(f"{player.name}: {amount:g} {kind}" for player, amount in changes.items())
