import random
from board import Board
from player import Player
from cards import MAGIC_CARDS, FIGURE_CARDS, FIGURE_EFFECTS


class Game:
    """Main game controller for a virtual tabletop card game"""
    def __init__(self, p1_name="Player 1", p2_name="Player 2"):
        self.p1 = Player(p1_name, hp=5, figure_id=200)
        self.p2 = Player(p2_name, hp=5, figure_id=200)
        self.board = Board()
        self.current_player = None
        self.other_player = None
        self.turn_number = 0
        self.current_step = 0
        self.steps_order = []

    def get_other_player(self, player):
        """Get opponent player"""
        return self.p2 if player == self.p1 else self.p1

    def get_figure_name(self, figure_id):
        """Get figure name from ID"""
        return FIGURE_CARDS[figure_id].name if figure_id in FIGURE_CARDS else "Unknown"

    def generate_turn_order(self):
        """Generate random turn order: 3 P1 steps + 3 P2 steps shuffled"""
        self.steps_order = [self.p1, self.p1, self.p1, self.p2, self.p2, self.p2]
        random.shuffle(self.steps_order)
        return self.steps_order

    def display_game_state(self):
        """Display the full game state (like a real tabletop)"""
        print("\n" + "="*80)
        print("📋 GAME STATE")
        print("="*80)

        # Show current board
        print("\n🎴 BOARD (Current State):")
        self.board.display_player_view()

        # Show player info
        print("\n👥 PLAYERS:")
        p1_figure = self.get_figure_name(self.p1.figure_id)
        p2_figure = self.get_figure_name(self.p2.figure_id)

        print(f"\n  {self.p1.name}:")
        print(f"    ❤️  HP: {self.p1.hp}/{self.p1.max_hp}")
        print(f"    👤 Figure: {p1_figure} (#{self.p1.figure_id})")
        print(f"    🎴 Hand: {len(self.p1.hand)} cards", end="")
        if self.p1.hand:
            hand_names = ", ".join([MAGIC_CARDS[sid].name for sid in self.p1.hand])
            print(f" → {hand_names}")
        else:
            print()

        print(f"\n  {self.p2.name}:")
        print(f"    ❤️  HP: {self.p2.hp}/{self.p2.max_hp}")
        print(f"    👤 Figure: {p2_figure} (#{self.p2.figure_id})")
        print(f"    🎴 Hand: {len(self.p2.hand)} cards", end="")
        if self.p2.hand:
            hand_names = ", ".join([MAGIC_CARDS[sid].name for sid in self.p2.hand])
            print(f" → {hand_names}")
        else:
            print()

        print("\n" + "="*80)

    def apply_turn_start_effects(self):
        """Apply effects that trigger at turn start"""
        # Witch (208): opponent -1 HP at turn start
        if self.p1.figure_id == 208:
            self.p2.take_damage(1)
            witch_name = self.get_figure_name(208)
            print(f"👻 {self.p1.name}'s {witch_name} ability: {self.p2.name} takes 1 damage!")

        if self.p2.figure_id == 208:
            self.p1.take_damage(1)
            witch_name = self.get_figure_name(208)
            print(f"👻 {self.p2.name}'s {witch_name} ability: {self.p1.name} takes 1 damage!")

    def start_turn(self):
        """Start a new turn"""
        self.turn_number += 1
        self.current_step = 0
        self.generate_turn_order()

        print(f"\n{'#'*80}")
        print(f"# TURN {self.turn_number}")
        print(f"{'#'*80}")
        print(f"Step order: {' → '.join([p.name[0] for p in self.steps_order])}")

        self.display_game_state()
        self.apply_turn_start_effects()

    def apply_spell_effect(self, spell_id, player):
        """Apply magic spell effect"""
        opponent = self.get_other_player(player)
        spell = MAGIC_CARDS[spell_id]
        spell_type = spell.effect_type

        if spell_type == "self_heal":
            amount = spell.effect_data
            player.heal(amount)
            print(f"    ✨ {player.name} heals {amount} HP!")

        elif spell_type == "mixed_heal":
            opponent.heal(spell.effect_data["opponent"])
            player.heal(spell.effect_data["self"])
            print(f"    ✨ {opponent.name} heals {spell.effect_data['opponent']} HP")
            print(f"    ✨ {player.name} heals {spell.effect_data['self']} HP")

        elif spell_type == "shuffle":
            self.table_refresh()
            print(f"    🔄 {player.name} shuffled the table!")

        elif spell_type == "swap_hand":
            player.hand, opponent.hand = opponent.hand, player.hand
            print(f"    🔄 {player.name} swapped hands with {opponent.name}!")

        elif spell_type == "board_modify":
            print(f"    ⚠️  {spell.name} effect: (TODO: Board modification - affects next turn)")

        elif spell_type == "reveal":
            count = spell.effect_data
            print(f"    👁️  {player.name} can see {count} cards (TODO: Implement)")

        elif spell_type == "reveal_all":
            print(f"    👁️  {player.name} reveals all magic cards (TODO: Implement)")

        elif spell_type == "change_figure":
            player.change_figure(200)  # Change to bob
            print(f"    👤 {player.name}'s figure changed to bob!")

        elif spell_type == "protect_figure":
            print(f"    🛡️  {player.name} is protected from figure changes for {spell.effect_data} turns (TODO: Implement)")

        elif spell_type == "discard":
            print(f"    🗑️  (TODO: Implement discard logic)")

        elif spell_type == "mixed":
            if "self_heal" in spell.effect_data:
                player.heal(spell.effect_data["self_heal"])
                print(f"    ✨ {player.name} heals {spell.effect_data['self_heal']} HP!")
            print(f"    ⚠️  Board modifications: (TODO)")

        else:
            print(f"    ✨ Spell effect: {spell.effect} (TODO: Implement)")

        """Apply card effect based on player's figure"""
        opponent = self.get_other_player(player)
        figure_id = player.figure_id
        figure_effects = FIGURE_EFFECTS.get(figure_id, {})

        if cell.type == "empty":
            print(f"    → Empty! Nothing happens.")

        elif cell.type == "bomb":
            damage = figure_effects.get("bomb_damage", -1)
            player.take_damage(abs(damage))
            print(f"    → 💣 BOMB! {player.name} takes {abs(damage)} damage!")

        elif cell.type == "frog":
            if "frog_effect" in figure_effects:
                if figure_effects["frog_effect"] == "opponent_damage_1":
                    opponent.take_damage(1)
                    gambler_name = self.get_figure_name(214)
                    print(f"    → 🐸 FROG! {opponent.name} takes 1 damage! ({player.name}'s {gambler_name})")
            else:
                player.heal(0.5)
                print(f"    → 🐸 FROG! {player.name} gains 0.5 HP!")

        elif cell.type == "magic":
            magic_id = random.choice(list(MAGIC_CARDS.keys()))
            magic = MAGIC_CARDS[magic_id]
            player.add_spell_to_hand(magic_id)
            print(f"    → ✨ MAGIC CARD: {magic.name}")
            print(f"       (Added to {player.name}'s hand)")

        elif cell.type == "figure":
            figure_id = random.choice([200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 211, 212, 213, 214, 215, 216, 217, 218, 219])
            figure_name = self.get_figure_name(figure_id)
            player.change_figure(figure_id)
            print(f"    → 👤 FIGURE: {figure_name}")
            print(f"       ({player.name}'s character changed!)")

    def execute_step(self):
        """Execute one player step"""
        self.current_step += 1
        self.current_player = self.steps_order[self.current_step - 1]
        self.other_player = self.get_other_player(self.current_player)

        figure_name = self.get_figure_name(self.current_player.figure_id)

        print(f"\n{'-'*80}")
        print(f"STEP {self.current_step} - {self.current_player.name}'s Turn ({figure_name})")
        print(f"{'-'*80}")

        # Loop for this step - can use multiple spells before opening card
        while True:
            print(f"\n{self.current_player.name}'s options:")

            if self.current_player.hand:
                print("  1. Use a magic card")
                print("  2. Open a card")
                print("  3. View all cards (god mode)")
            else:
                print("  1. Open a card")
                print("  2. View all cards (god mode)")

            choice = input("\nChoose: ").strip()

            if choice == "1" and self.current_player.hand:
                # Use magic card
                print(f"\n  {self.current_player.name}'s hand:")
                for i, spell_id in enumerate(self.current_player.hand):
                    spell_name = MAGIC_CARDS[spell_id].name
                    print(f"    {i}: {spell_name}")

                spell_choice = input("  Choose card (or 'c' to cancel): ").strip()

                if spell_choice.lower() == 'c':
                    continue

                try:
                    spell_idx = int(spell_choice)
                    spell_id = self.current_player.hand[spell_idx]
                    spell_name = MAGIC_CARDS[spell_id].name
                    self.current_player.use_spell(spell_id)
                    print(f"\n  ✨ Used: {spell_name}")
                    self.apply_spell_effect(spell_id, self.current_player)
                    print(f"  ← Continue step...")
                    # Does NOT end step - continue loop

                except (ValueError, IndexError):
                    print("  ❌ Invalid choice")

            elif choice == "1" and not self.current_player.hand:
                # Open a card (no hand)
                board_input = input("  Enter card index (0-24): ").strip()
                try:
                    card_idx = int(board_input)
                    if 0 <= card_idx < 25:
                        cell = self.board.open_cell(card_idx)
                        if cell is False:
                            print("  ❌ That card is already open!")
                        elif cell:
                            print(f"\n  🎴 Opened card #{card_idx}")
                            self.apply_card_effect(cell, self.current_player)
                            print(f"\n  📋 Board updated:")
                            self.board.display_player_view()
                            print(f"\n  ✓ Step ended!")
                            return True
                        else:
                            print("  ❌ Invalid card")
                    else:
                        print("  ❌ Index must be 0-24")
                except ValueError:
                    print("  ❌ Invalid index")

            elif choice == "2" and self.current_player.hand:
                # Open a card (has hand)
                board_input = input("  Enter card index (0-24): ").strip()
                try:
                    card_idx = int(board_input)
                    if 0 <= card_idx < 25:
                        cell = self.board.open_cell(card_idx)
                        if cell is False:
                            print("  ❌ That card is already open!")
                        elif cell:
                            print(f"\n  🎴 Opened card #{card_idx}")
                            self.apply_card_effect(cell, self.current_player)
                            print(f"\n  📋 Board updated:")
                            self.board.display_player_view()
                            print(f"\n  ✓ Step ended!")
                            return True
                        else:
                            print("  ❌ Invalid card")
                    else:
                        print("  ❌ Index must be 0-24")
                except ValueError:
                    print("  ❌ Invalid index")

            elif choice == "3" and self.current_player.hand:
                # God mode (has hand)
                print("\n  --- ALL CARDS (Testing) ---")
                self.board.display_debug_view()

            elif choice == "2" and not self.current_player.hand:
                # God mode (no hand)
                print("\n  --- ALL CARDS (Testing) ---")
                self.board.display_debug_view()

            else:
                print("  ❌ Invalid choice")

    def table_refresh(self):
        """Refresh board with new 25 cards"""
        print(f"\n{'*'*80}")
        print("🔄 TABLE REFRESH - Reshuffling new 25 cards!")
        print(f"{'*'*80}")
        self.board = Board()

    def check_game_over(self):
        """Check if game has ended"""
        if not self.p1.is_alive():
            print(f"\n{'='*80}")
            print(f"🎉 GAME OVER! {self.p2.name} WINS!")
            print(f"{self.p1.name} reached 0 HP")
            print(f"{'='*80}")
            return True

        if not self.p2.is_alive():
            print(f"\n{'='*80}")
            print(f"🎉 GAME OVER! {self.p1.name} WINS!")
            print(f"{self.p2.name} reached 0 HP")
            print(f"{'='*80}")
            return True

        return False

    def run(self):
        """Main game loop"""
        print("\n" + "="*80)
        print("🎴 VIRTUAL TABLETOP CARD GAME 🎴")
        print("="*80)
        print(f"{self.p1.name} vs {self.p2.name}")
        print("Starting HP: 5 each")
        print("="*80)

        while True:
            self.start_turn()

            # Execute 6 steps
            for step in range(6):
                if self.check_game_over():
                    return

                self.execute_step()

                if self.check_game_over():
                    return

            # After 6 steps, table refresh
            self.table_refresh()

            self.display_game_state()

            cont = input("Continue to next turn? (y/n): ").strip().lower()
            if cont != 'y':
                print("Game ended by player")
                break
