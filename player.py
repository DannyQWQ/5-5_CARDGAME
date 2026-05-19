# =========================
# 👤 Player
# =========================
class Player:
    def __init__(self, name, hp=5, figure_id=200):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.hand = []                   # Spell cards in hand
        self.figure_id = figure_id       # Current figure on board (default: bob #200)
        self.steps_remaining = 0         # Steps left in current turn

    def take_damage(self, damage):
        """Reduce HP"""
        self.hp = max(0, self.hp - damage)
        return self.hp

    def heal(self, amount):
        """Increase HP"""
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp

    def add_spell_to_hand(self, spell_id):
        """Add spell card to hand"""
        self.hand.append(spell_id)

    def use_spell(self, spell_id):
        """Use spell from hand (removes it)"""
        if spell_id in self.hand:
            self.hand.remove(spell_id)
            return True
        return False

    def change_figure(self, new_figure_id):
        """Change current figure"""
        self.figure_id = new_figure_id

    def is_alive(self):
        """Check if player is still alive"""
        return self.hp > 0

    def __repr__(self):
        return f"Player({self.name}, HP={self.hp}/{self.max_hp}, Figure=#{self.figure_id}, Hand={len(self.hand)} spells)"
