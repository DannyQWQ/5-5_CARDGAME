"""Canonical Figure Card definitions; ability execution belongs to ``game.Game``."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FigureCard:
    card_id: int
    name: str
    description: str
    board_pattern: tuple[str, ...] = ()
    drawable: bool = True

    @property
    def type(self) -> str:
        return "figure"


FIGURE_CARDS = {
    200: FigureCard(200, "bob", "No special ability"),
    201: FigureCard(201, "pawn", "10% chance each turn to evolve"),
    202: FigureCard(202, "queen", "W-pattern: owner +1 HP; opponent -1 HP once per turn", ("WOWOW", "OWWWO", "WWQWW", "OWWWO", "WOWOW"), False),
    203: FigureCard(203, "bishop", "W-pattern: owner +0.5 HP; opponent -0.5 HP", ("WOOOW", "OWOWO", "OOBOO", "OWOWO", "WOOOW"), False),
    204: FigureCard(204, "knight", "W-pattern: owner +0.5 HP; opponent -0.5 HP", ("OWOWO", "WOOOW", "OOKOO", "WOOOW", "OWOWO"), False),
    205: FigureCard(205, "rook", "W-pattern: owner +0.5 HP; opponent -0.5 HP", ("OOWOO", "OOWOO", "WWRWW", "OOWOO", "OOWOO"), False),
    206: FigureCard(206, "foreteller", "Reveal 3 cards at the start of your first step"),
    207: FigureCard(207, "princess", "Open Frog: +1 HP once per turn"),
    208: FigureCard(208, "witch", "Opponent loses 1 HP at turn start"),
    209: FigureCard(209, "tic-tac-toeR", "May place an X barrier before each step"),
    211: FigureCard(211, "alcoholic", "Must open a random selectable card"),
    212: FigureCard(212, "copy cat", "Copy opponent's current figure once"),
    213: FigureCard(213, "abusive lover", "HP changes affect both players equally"),
    214: FigureCard(214, "gambler", "Bomb: self -2 HP; Frog: opponent -1 HP"),
    215: FigureCard(215, "psychopath", "Bomb damage becomes 3 HP"),
    216: FigureCard(216, "magician", "May shuffle once per turn"),
    217: FigureCard(217, "lucky bob", "30% chance to avoid damage"),
    218: FigureCard(218, "unlucky bob", "30% chance to double damage"),
    219: FigureCard(219, "Politician", "Invert revealed states at turn start"),
}

DRAWABLE_FIGURE_IDS = tuple(card_id for card_id, card in FIGURE_CARDS.items() if card.drawable)
