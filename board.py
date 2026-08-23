"""Physical board state. No HP, hand, or turn rules belong here."""

from dataclasses import dataclass
from enum import Enum
import random

from cards import DRAWABLE_FIGURE_IDS, MAGIC_CARDS


CARD_TYPES = ("bomb", "frog", "empty", "magic", "figure")
BOARD_SIZE = 25


class Visibility(str, Enum):
    FACE_DOWN = "face_down"
    REVEALED = "revealed"
    OPENED = "opened"


@dataclass(slots=True)
class Cell:
    card_type: str
    cell_id: int
    card_id: int | None = None
    visibility: Visibility = Visibility.FACE_DOWN
    barrier: bool = False
    temporary_reveal: bool = False

    @property
    def type(self):
        return self.card_type

    @property
    def is_open(self):
        return self.visibility is Visibility.OPENED


class Board:
    DEFAULT_DISTRIBUTION = {
        "bomb": 5, "frog": 5, "empty": 8, "magic": 5, "figure": 2,
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
        if any(type(value) is not int or value < 0 for value in distribution.values()):
            raise ValueError("all distribution counts must be non-negative integers")
        if sum(distribution.values()) != BOARD_SIZE:
            raise ValueError(f"distribution must contain exactly {BOARD_SIZE} cards")

    def _build_board(self):
        types = [kind for kind in CARD_TYPES for _ in range(self.distribution[kind])]
        self.rng.shuffle(types)
        cells = []
        for index, kind in enumerate(types):
            identity = None
            if kind == "magic":
                identity = self.rng.choice(tuple(MAGIC_CARDS))
            elif kind == "figure":
                identity = self.rng.choice(DRAWABLE_FIGURE_IDS)
            cells.append(Cell(kind, index, identity))
        return cells

    def get_cell(self, index):
        return self.cells[index] if 0 <= index < len(self.cells) else None

    def get_cell_by_coords(self, row, col):
        return self.get_cell(row * 5 + col) if 0 <= row < 5 and 0 <= col < 5 else None

    def selectable_indices(self):
        return tuple(
            cell.cell_id for cell in self.cells
            if cell.visibility is not Visibility.OPENED and not cell.barrier
        )

    def open_cell(self, index):
        cell = self._require_cell(index)
        if cell.barrier:
            raise ValueError("that card is protected by an X barrier")
        if cell.visibility is Visibility.OPENED:
            raise ValueError("that card is already Opened")
        cell.visibility = Visibility.OPENED
        cell.temporary_reveal = False
        return cell

    def reveal(self, indices, *, temporary=True):
        indices = tuple(indices)
        if len(set(indices)) != len(indices):
            raise ValueError("Reveal targets must be different")
        cells = [self._require_cell(index) for index in indices]
        if any(cell.visibility is Visibility.OPENED for cell in cells):
            raise ValueError("an Opened card cannot be Revealed")
        for cell in cells:
            cell.visibility = Visibility.REVEALED
            cell.temporary_reveal = temporary
        return tuple(cells)

    def reveal_all_magic(self):
        targets = [c.cell_id for c in self.cells if c.card_type == "magic" and not c.is_open]
        return self.reveal(targets, temporary=True)

    def clear_temporary_reveals(self):
        for cell in self.cells:
            if cell.visibility is Visibility.REVEALED and cell.temporary_reveal:
                cell.visibility = Visibility.FACE_DOWN
                cell.temporary_reveal = False

    def invert_visibility(self):
        for cell in self.cells:
            cell.visibility = (
                Visibility.REVEALED
                if cell.visibility is Visibility.FACE_DOWN
                else Visibility.FACE_DOWN
            )
            cell.temporary_reveal = False

    def place_barrier(self, index):
        cell = self._require_cell(index)
        if cell.visibility is Visibility.OPENED:
            raise ValueError("cannot place X on an Opened card")
        if cell.barrier:
            raise ValueError("that card already has X")
        cell.barrier = True
        return cell

    def clear_barriers(self):
        for cell in self.cells:
            cell.barrier = False

    def shuffle(self):
        before = sorted((cell.card_type, cell.card_id) for cell in self.cells)
        self.rng.shuffle(self.cells)
        for index, cell in enumerate(self.cells):
            cell.cell_id = index
            cell.visibility = Visibility.FACE_DOWN
            cell.barrier = False
            cell.temporary_reveal = False
        assert before == sorted((cell.card_type, cell.card_id) for cell in self.cells)

    def _require_cell(self, index):
        cell = self.get_cell(index)
        if cell is None:
            raise IndexError("card index must be between 0 and 24")
        return cell

    def display_player_view(self):
        symbols = {"bomb": "B", "frog": "F", "empty": "O", "magic": "M", "figure": "C"}
        for row in range(5):
            output = []
            for col in range(5):
                cell = self.cells[row * 5 + col]
                if cell.visibility is Visibility.FACE_DOWN:
                    label = f"[{cell.cell_id:02d}]"
                else:
                    suffix = f"{cell.card_id}" if cell.card_id is not None else ""
                    marker = "R" if cell.visibility is Visibility.REVEALED else "O"
                    label = f"{symbols[cell.card_type]}{suffix}:{marker}"
                output.append(label + ("X" if cell.barrier else " "))
            print(" ".join(f"{item:7}" for item in output))

    def display_debug_view(self):
        for cell in self.cells:
            print(cell)
