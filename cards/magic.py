MAGIC_CARDS_DATA = {
    1: {
        "name": "bubble tea",
        "effect": {
            "timing": "instant",
            "type": "heal",
            "data": {"user": 1}
        }
    },

    2: {
        "name": "sanshoku dango",
        "effect": {
            "timing": "instant",
            "type": "heal",
            "data": {"user": 3}
        }
    },

    3: {
        "name": "wine",
        "effect": {
            "timing": "instant",
            "type": "heal_dual",
            "data": {"user": 2, "opponent": 1}
        }
    },

    4: {
        "name": "beep",
        "effect": {
            "timing": "next_turn",
            "type": "table_status_change",
            "data": {"bomb": 1, "empty": -1}
        }
    },

    5: {
        "name": "beep boom",
        "effect": {
            "timing": "next_turn",
            "type": "table_status_change",
            "data": {"bomb": 2, "empty": -2}
        }
    },

    6: {
        "name": "let's be nice",
        "effect": {
            "timing": "next_turn",
            "type": "table_status_change",
            "data": {"bomb": -1, "empty": 1}
        }
    },

    7: {
        "name": "peace!",
        "effect": {
            "timing": "next_turn",
            "type": "table_status_change",
            "data": {"bomb": -2, "empty": 2}
        }
    },

    8: {
        "name": "one more please",
        "effect": {
            "timing": "next_turn",
            "type": "table_status_change",
            "data": {"magic": 1, "empty": -1}
        }
    },

    9: {
        "name": "becoming tricky!",
        "effect": {
            "timing": "next_turn",
            "type": "table_status_change",
            "data": {"magic": 2, "empty": -2}
        }
    },

    10: {
        "name": "\"CARD\"iovascular",
        "effects": [
            {
                "timing": "next_turn",
                "type": "table_status_change",
                "data": {"magic": -2, "empty": 2}
            },
            {
                "timing": "instant",
                "type": "heal",
                "data": {"user": 2}
            }
        ]
    },

    11: {
        "name": "Ribbit! Ribbit! Ribbit!",
        "effect": {
            "timing": "next_turn",
            "type": "table_status_change",
            "data": {"frog": 3, "empty": -3}
        }
    },

    12: {
        "name": "THE NUKE",
        "effect": {
            "timing": "next_turn",
            "type": "replace_all",
            "data": {"from": "empty", "to": "bomb"}
        }
    },

    13: {
        "name": "It's raining FROGS and FROGS",
        "effect": {
            "timing": "next_turn",
            "type": "replace_all",
            "data": {"from": "empty", "to": "frog"}
        }
    },

    14: {
        "name": "Who is this?",
        "effect": {
            "timing": "next_turn",
            "type": "replace_all",
            "data": {"from": "empty", "to": "figure"}
        }
    },

    15: {
        "name": "HarRy PotTEr?",
        "effect": {
            "timing": "next_turn",
            "type": "replace_all",
            "data": {"from": "empty", "to": "magic"}
        }
    },

    16: {
        "name": "Shuffle!",
        "effect": {
            "timing": "instant",
            "type": "shuffle"
        }
    },

    17: {
        "name": "Take a LooK",
        "effect": {
            "timing": "instant",
            "type": "reveal",
            "data": {"count": 1}
        }
    },

    18: {
        "name": "Take a and b and c LooK",
        "effect": {
            "timing": "instant",
            "type": "reveal",
            "data": {"count": 3}
        }
    },

    19: {
        "name": "the birth of BOB",
        "effect": {
            "timing": "instant",
            "type": "figure_change",
            "data": {"target": "opponent", "figure_id": 200}
        }
    },

    20: {
        "name": "const FIGURE",
        "effect": {
            "timing": "duration",
            "type": "lock_figure",
            "data": {"turns": 12}
        }
    },

    21: {
        "name": "shredder",
        "effect": {
            "timing": "instant",
            "type": "discard_hand",
            "data": {"user": 1, "opponent": 1}
        }
    },

    22: {
        "name": "REVEAL!",
        "effect": {
            "timing": "instant",
            "type": "reveal",
            "data": {"count": 25}
        }
    },

    24: {
        "name": "Frog bomb",
        "effect": {
            "timing": "next_turn",
            "type": "combo_trigger",
            "data": {"trigger": "frog", "also": "bomb"}
        }
    },

    25: {
        "name": "SWAP!",
        "effect": {
            "timing": "instant",
            "type": "swap_hand"
        }
    }
}