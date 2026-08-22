"""Board state and board-only operations.

The board knows which physical cards exist and whether they are revealed. It does
not apply damage, healing, hand rules, or figure abilities.
"""

from dataclasses import dataclass
import random

from cards import DRAWABLE_FIGURE_IDS, MAGIC_CARDS


CARD_TYPES = ("bomb", "frog", "empty", "magic", "figure")
BOARD_SIZE = 25


@dataclass(slots=True)
class Cell:
    card_type: str
    cell_id: int
    card_id: int | None = None
    is_open: bool = False
    barrier: bool = False

    @property
    def type(self) -> str:
        """Compatibility alias for older callers."""
        return self.card_type


class Board:
    DEFAULT_DISTRIBUTION = {
        "bomb": 5,
        "frog": 5,
        "empty": 8,
        "magic": 5,
        "figure": 2,
    }

    def __init__(self, distribution=None, *, rng=None):
        self.rng = rng or random.Random()
        self.distribution = dict(distribution or self.DEFAULT_DISTRIBUTION)
        self._validate_distribution(self.distribution)
        self.cells = self._build_board()

    @staticmethod
    def _validate_distribution(distribution):
        if set(distribution) != set(CARD_TYPES):
            raise ValueError(f"distribution must contain exactly: {', '.join(CARD_TYPES)}")
        if any(type(count) is not int or count < 0 for count in distribution.values()):
            raise ValueError("all distribution counts must be non-negative integers")
        if sum(distribution.values()) != BOARD_SIZE:
            raise ValueError(f"distribution must contain exactly {BOARD_SIZE} cards")

    def _build_board(self):
        cards = []
        for card_type in CARD_TYPES:
            cards.extend([card_type] * self.distribution[card_type])
        self.rng.shuffle(cards)

        cells = []
        for cell_id, card_type in enumerate(cards):
            card_id = None
            if card_type == "magic":
                card_id = self.rng.choice(tuple(MAGIC_CARDS))
            elif card_type == "figure":
                card_id = self.rng.choice(DRAWABLE_FIGURE_IDS)
            cells.append(Cell(card_type, cell_id, card_id))
        return cells

    def get_cell(self, index):
        return self.cells[index] if 0 <= index < len(self.cells) else None

    def get_cell_by_coords(self, row, col):
        if not (0 <= row < 5 and 0 <= col < 5):
            return None
        return self.cells[row * 5 + col]

    def open_cell(self, index):
        cell = self.get_cell(index)
        if cell is None:
            raise IndexError("card index must be between 0 and 24")
        if cell.barrier:
            raise ValueError("that card is protected by an X barrier")
        if cell.is_open:
            raise ValueError("that card is already open")
        cell.is_open = True
        return cell

    def peek_cell(self, index):
        cell = self.get_cell(index)
        if cell is None:
            raise IndexError("card index must be between 0 and 24")
        return cell

    def shuffle(self):
        """Close and rearrange the same physical cards and clear barriers."""
        before = sorted((cell.card_type, cell.card_id) for cell in self.cells)
        self.rng.shuffle(self.cells)
        for new_id, cell in enumerate(self.cells):
            cell.cell_id = new_id
            cell.is_open = False
            cell.barrier = False
        assert before == sorted((cell.card_type, cell.card_id) for cell in self.cells)

    def display_player_view(self):
        icons = {"bomb": "B", "frog": "F", "empty": "O", "magic": "M", "figure": "C"}
        for row in range(5):
            rendered = []
            for col in range(5):
                index = row * 5 + col
                cell = self.cells[index]
                rendered.append(f" {icons[cell.card_type]} " if cell.is_open else f"[{index:2d}]")
            print(" ".join(rendered))

    def display_debug_view(self):
        for row in range(5):
            rendered = []
            for col in range(5):
                cell = self.cells[row * 5 + col]
                identity = f"#{cell.card_id}" if cell.card_id is not None else ""
                state = "open" if cell.is_open else "closed"
                rendered.append(f"{cell.card_type}{identity}:{state}")
            print(" | ".join(rendered))
