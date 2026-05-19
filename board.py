import random

# =========================
# 🧩 Cell (Individual card on board)
# =========================
class Cell:
    def __init__(self, card_type, cell_id):
        self.type = card_type          # "bomb", "frog", "empty", "magic", "figure"
        self.id = cell_id
        self.is_open = False            # Has this cell been revealed?
        self.owner = None               # Future: track who opened it
        self.effect = None              # Extra effects/buffs

    def __repr__(self):
        return f"Cell(type={self.type}, id={self.id}, open={self.is_open})"


# =========================
# 🧱 Board (5x5 grid)
# =========================
class Board:
    # Default card distribution
    DEFAULT_DISTRIBUTION = {
        "bomb": 5,
        "frog": 5,
        "empty": 8,
        "magic": 5,
        "figure": 2
    }

    def __init__(self, distribution=None):
        if distribution is None:
            distribution = self.DEFAULT_DISTRIBUTION

        self.distribution = distribution
        self.cells = self._build_board()

    def _build_board(self):
        """Create shuffled 5x5 board with cards"""
        # Create card list based on distribution
        cards = []
        for card_type, count in self.distribution.items():
            cards.extend([card_type] * count)

        random.shuffle(cards)

        # Create cells
        cells = []
        for i, card_type in enumerate(cards):
            cells.append(Cell(card_type, i))

        return cells

    def get_cell(self, index):
        """Get cell at index (0-24)"""
        if 0 <= index < 25:
            return self.cells[index]
        return None

    def get_cell_by_coords(self, row, col):
        """Get cell by row/col coordinates (0-4)"""
        if 0 <= row < 5 and 0 <= col < 5:
            index = row * 5 + col
            return self.cells[index]
        return None

    def open_cell(self, index):
        """Reveal a cell (returns None if already open)"""
        cell = self.get_cell(index)
        if not cell:
            return None
        if cell.is_open:
            return False  # Already opened
        cell.is_open = True
        return cell

    def shuffle(self):
        """Reshuffle the board (closes all cards)"""
        random.shuffle(self.cells)
        for cell in self.cells:
            cell.is_open = False

    def display_player_view(self):
        """Show board as player sees it (unopened = [], opened = type icon)"""
        type_icons = {
            "bomb": "💣",
            "frog": "🐸",
            "empty": "⭕",
            "magic": "✨",
            "figure": "👤"
        }

        for i in range(5):
            for j in range(5):
                index = i * 5 + j
                cell = self.cells[index]
                if not cell.is_open:
                    print(f"[{index:2d}]", end=" ")
                else:
                    icon = type_icons.get(cell.type, "?")
                    print(f" {icon} ", end=" ")
            print()

    def display_debug_view(self):
        """Show all cards (for debugging)"""
        for i in range(5):
            for j in range(5):
                cell = self.cells[i * 5 + j]
                status = "X" if cell.is_open else " "
                print(f"{cell.type[0]}{status}({cell.id})", end=" ")
            print()
