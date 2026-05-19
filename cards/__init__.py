"""
Card system for the game
"""

# =========================
# Figure Effects Modifiers
# =========================
# Some figures modify card effects when the player opens them
FIGURE_EFFECTS = {
    # Gambler (214): bomb damage -2, frog makes opponent -1 HP
    214: {
        "bomb_damage": -2,  # instead of -1
        "frog_effect": "opponent_damage_1",  # opponent -1 HP instead of self +0.5 HP
    },
    # Psychopath (215): bomb damage -3
    215: {
        "bomb_damage": -3,  # instead of -1
    },
    # Princess (207): open frog +0.5 HP (standard frog effect)
    # Witch (208): at turn start, opponent -1 HP (handled separately)
}

# =========================
# 🎴 Magic Card (Spell)
# =========================
class MagicCard:
    """Spell card with effects"""
    def __init__(self, card_id, name, effect="", effect_type=None, effect_data=None):
        self.card_id = card_id
        self.name = name
        self.effect = effect
        self.type = "magic"
        self.effect_type = effect_type  # "self_heal", "opponent_damage", etc.
        self.effect_data = effect_data  # Additional data for the effect

    def __repr__(self):
        return f"MagicCard(#{self.card_id} {self.name})"


# =========================
# 🧍 Figure Card (Character)
# =========================
class FigureCard:
    """Character/figure card that affects gameplay"""
    def __init__(self, card_id, name, effect="", board_pattern=None):
        self.card_id = card_id
        self.name = name
        self.effect = effect
        self.type = "figure"
        self.board_pattern = board_pattern  # 5x5 board effect pattern (None if not applicable)

    def __repr__(self):
        return f"FigureCard(#{self.card_id} {self.name})"


# =========================
# 🎴 Magic Card Catalog
# =========================
MAGIC_CARDS = {
    1: MagicCard(1, "bubble tea", "+1 HP", "self_heal", 1),
    2: MagicCard(2, "sanshoku dango", "+3 HP", "self_heal", 3),
    3: MagicCard(3, "wine", "opponent +1 HP, self +2 HP", "mixed_heal", {"opponent": 1, "self": 2}),
    4: MagicCard(4, "beep", "bomb +1, empty -1 next turn", "board_modify", {"bomb": 1, "empty": -1}),
    5: MagicCard(5, "beep boom", "bomb +2, empty -2 next turn", "board_modify", {"bomb": 2, "empty": -2}),
    6: MagicCard(6, "let's be nice", "bomb -1, empty +1 next turn", "board_modify", {"bomb": -1, "empty": 1}),
    7: MagicCard(7, "peace!", "bomb -2, empty +2 next turn", "board_modify", {"bomb": -2, "empty": 2}),
    8: MagicCard(8, "one more please", "card +1, empty -1 next turn", "board_modify", {"card": 1, "empty": -1}),
    9: MagicCard(9, "becoming tricky!", "card +2, empty -2 next turn", "board_modify", {"card": 2, "empty": -2}),
    10: MagicCard(10, "CARD iovascular", "card -2, empty +2 next turn, HP +2 now", "mixed", {"board": {"card": -2, "empty": 2}, "self_heal": 2}),
    11: MagicCard(11, "Ribbit! Ribbit! Ribbit!", "frogs +3, empty -3", "board_modify", {"frog": 3, "empty": -3}),
    12: MagicCard(12, "THE NUKE", "all empty turn to bomb next turn", "board_modify", {"empty_to": "bomb"}),
    13: MagicCard(13, "IT'S RAINING FROGS AND FROGS", "all empty turn to frog next turn", "board_modify", {"empty_to": "frog"}),
    14: MagicCard(14, "WHO ARE YOU?", "all empty turn to figure next turn", "board_modify", {"empty_to": "figure"}),
    15: MagicCard(15, "THAT'S FUN!", "all empty turn to magic next turn", "board_modify", {"empty_to": "magic"}),
    16: MagicCard(16, "Shuffle!", "shuffle the table", "shuffle", None),
    17: MagicCard(17, "Take a look!", "reveal 1 card", "reveal", 1),
    18: MagicCard(18, "Take abc looks!", "reveal 3 cards", "reveal", 3),
    19: MagicCard(19, "the birth of BOB", "change your or opponent's figure into bob", "change_figure", 200),
    20: MagicCard(20, "const figure", "can't change figure in three turns", "protect_figure", 3),
    21: MagicCard(21, "shredder", "throw away your card and opponent's card", "discard", None),
    22: MagicCard(22, "REVEAL!", "reveal all magic cards this turn", "reveal_all", None),
    24: MagicCard(24, "Frog bomb", "change a frog into bomb next turn", "board_modify", {"frog_to": "bomb"}),
    25: MagicCard(25, "Swap", "swap yours and opponent's hand", "swap_hand", None),
}

# =========================
# 🧍 Figure Card Catalog
# =========================
FIGURE_CARDS = {
    200: FigureCard(
        200, "bob",
        "Just a bob"
    ),
    201: FigureCard(
        201, "pawn",
        "Each turn has 10% chance to evolve into queen/rook/bishop/knight"
    ),
    # Evolved forms from Pawn (won't be able to draw on table)
    202: FigureCard(
        202, "queen",
        "Opponent picks on W: -1 HP once per turn | You pick on W: +1 HP once per turn",
        board_pattern=[
            "W O W O W",
            "O W W W O",
            "W W Q W W",
            "O W W W O",
            "W O W O W"
        ]
    ),
    203: FigureCard(
        203, "bishop",
        "Opponent picks on W: -0.5 HP | You pick on W: +0.5 HP",
        board_pattern=[
            "W O O O W",
            "O W O W O",
            "O O B O O",
            "O W O W O",
            "W O O O W"
        ]
    ),
    204: FigureCard(
        204, "knight",
        "Opponent picks on W: -0.5 HP | You pick on W: +0.5 HP",
        board_pattern=[
            "O W O W O",
            "W O O O W",
            "O O K O O",
            "W O O O W",
            "O W O W O"
        ]
    ),
    205: FigureCard(
        205, "rook",
        "Opponent picks on W: -0.5 HP | You pick on W: +0.5 HP",
        board_pattern=[
            "O O W O O",
            "O O W O O",
            "W W W W W",
            "O O W O O",
            "O O W O O"
        ]
    ),
    # Special Figures
    206: FigureCard(
        206, "foreteller",
        "Reveal 3 cards at your first step of that turn"
    ),
    207: FigureCard(
        207, "princess",
        "Open a frog and gain +0.5 HP each turn"
    ),
    208: FigureCard(
        208, "witch",
        "Opponent takes -1 HP each turn"
    ),
    209: FigureCard(
        209, "tic-tac-toeR",
        "Set a barrier X on a card before each step (both players' steps) | Cannot pick that card this turn | Barrier disappears after turn | Shuffle breaks X"
    ),
    211: FigureCard(
        211, "alcholic",
        "Randomly pick a card, player can't choose"
    ),
    212: FigureCard(
        212, "copy cat",
        "Copy opponent's figure"
    ),
    213: FigureCard(
        213, "abusive lover",
        "HP +/- will now affect both players"
    ),
    214: FigureCard(
        214, "gambler",
        "Open a bomb: -2 HP | Open a frog: opponent -1 HP"
    ),
    215: FigureCard(
        215, "psychopath",
        "Bomb damage = -3 HP now"
    ),
    216: FigureCard(
        216, "magician",
        "Shuffle the table once per turn"
    ),
    217: FigureCard(
        217, "lucky bob",
        "30% chance to avoid damage"
    ),
    218: FigureCard(
        218, "unlucky bob",
        "30% chance to double damage"
    ),
    219: FigureCard(
        219, "Politician",
        "At turn start: revealed cards become closed, closed cards become revealed"
    ),
}
