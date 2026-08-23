"""Canonical Magic Card definitions; effect execution belongs to ``game.Game``."""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MagicCard:
    card_id: int
    name: str
    description: str
    effect_type: str
    effect_data: Mapping[str, Any] = field(default_factory=dict)

    @property
    def type(self) -> str:
        return "magic"


def _card(card_id, name, description, effect_type, **effect_data):
    return MagicCard(card_id, name, description, effect_type, MappingProxyType(effect_data))


MAGIC_CARDS = {
    1: _card(1, "bubble tea", "Self: +1 HP", "heal", user=1),
    2: _card(2, "sanshoku dango", "Self: +3 HP", "heal", user=3),
    3: _card(3, "wine", "Opponent: +1 HP; self: +2 HP", "heal_dual", user=2, opponent=1),
    4: _card(4, "beep", "Next turn: Bomb +1, Empty -1", "board_delta", bomb=1, empty=-1),
    5: _card(5, "beep boom", "Next turn: Bomb +2, Empty -2", "board_delta", bomb=2, empty=-2),
    6: _card(6, "let's be nice", "Next turn: Bomb -1, Empty +1", "board_delta", bomb=-1, empty=1),
    7: _card(7, "peace!", "Next turn: Bomb -2, Empty +2", "board_delta", bomb=-2, empty=2),
    8: _card(8, "one more please", "Next turn: Magic +1, Empty -1", "board_delta", magic=1, empty=-1),
    9: _card(9, "becoming tricky!", "Next turn: Magic +2, Empty -2", "board_delta", magic=2, empty=-2),
    10: _card(10, '"CARD"iovascular', "Next turn: Magic -2, Empty +2; self: +2 HP", "heal_and_board_delta", user=2, magic=-2, empty=2),
    11: _card(11, "Ribbit! Ribbit! Ribbit!", "Next turn: Frog +3, Empty -3", "board_delta", frog=3, empty=-3),
    12: _card(12, "THE NUKE", "Next turn: all Empty become Bomb", "convert_all", source="empty", target="bomb"),
    13: _card(13, "IT'S RAINING FROGS AND FROGS", "Next turn: all Empty become Frog", "convert_all", source="empty", target="frog"),
    14: _card(14, "WHO ARE YOU?", "Next turn: all Empty become Figure", "convert_all", source="empty", target="figure"),
    15: _card(15, "THAT'S FUN!", "Next turn: all Empty become Magic", "convert_all", source="empty", target="magic"),
    16: _card(16, "Shuffle!", "Shuffle the same 25 cards", "shuffle"),
    17: _card(17, "Take a look!", "Choose 1 row or column; Reveal every face-down card in that line", "reveal_line"),
    18: _card(18, "Take 3 looks!", "Reveal 3 chosen cards", "reveal", count=3),
    19: _card(19, "the birth of BOB", "Change either player's figure to Bob", "change_figure", figure_id=200),
    20: _card(20, "const figure", "Prevent figure changes for 3 turns", "protect_figure", turns=3),
    21: _card(21, "shredder", "Requires another card in both hands; user chooses both discards", "discard"),
    22: _card(22, "REVEAL!", "Reveal all Magic Cards this turn", "reveal_all_magic"),
    23: _card(23, "This is curse!", "Force one chosen opponent card on their next step", "curse"),
    24: _card(24, "Frog bomb", "Next turn: change 1 Frog to Bomb", "convert_one", source="frog", target="bomb"),
    25: _card(25, "Swap", "Swap hands with opponent", "swap_hand"),
}
