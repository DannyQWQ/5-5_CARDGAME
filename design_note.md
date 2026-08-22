# Card Game Design

## 🎮 Core Game Rules

### Objective
- **Two-player** turn-based card game.
- Each player starts with **5 HP**. HP can be fractional (e.g., 0.5 HP).
- HP is displayed in increments of `0.5` (for example, `5.0`, `4.5`, and `4.0`).
- The first player to reach **0 HP** or below loses immediately.
- If one indivisible effect reduces both players to 0 HP or below simultaneously, the game ends in a draw.
- If an effect resolves in a stated sequence, the first player to reach 0 HP loses before later parts of that sequence resolve.

### Board
- A **5x5 grid** (25 cards total, all face-down).
- Cards are revealed during gameplay.

### Turn Structure
Each turn consists of **6 steps** total:
- **3 steps** for Player 1.
- **3 steps** for Player 2.
- **Order is randomized** at the start of each turn.

**Turn Order Example:**
```text
Turn: P1 P2 P2 P2 P1 P1
Step: X  O  O  O  O  O
```
*(`X` is current step, `O` are upcoming steps)*

**Visual Layout:**
```text
P1 Hand: [?] [?] [?] | HP: 5.0

[ ] [ ] [ ] [ ] [ ]
[ ] [ ] [ ] [ ] [ ]
[ ] [ ] [ ] [ ] [ ]
[ ] [ ] [ ] [ ] [ ]
[ ] [ ] [ ] [ ] [ ]

P2 Hand: [?] [?] [?] | HP: 5.0
```

### Step Actions
On each step, the active player chooses exactly one main action:
1. **Play one Magic Card** from their hand. Resolve its effect, then end the step.
2. **Open one face-down card** from the board. Resolve its effect, then end the step.

- A player cannot play multiple Magic Cards during the same step unless a card effect explicitly says otherwise.
- A revealed card cannot be selected again while it remains revealed.
- A revealed card's normal open effect triggers only when it changes from face-down to revealed.

### Winning Condition
- Reduce the opponent's HP to 0 or below while keeping your own HP above 0.
- Simultaneous defeat caused by one indivisible effect is a draw.

---

## 📦 Card and Board Rules

### Board Generation
- A new 25-card board is generated each turn.
- The distribution varies based on game mode or magic effects.
- The exact identity of every Magic and Figure Card is assigned when the board is generated.
- Revealing a card does not randomly determine its identity at that moment.

**Default Distribution:**
- `Bomb`: 5
- `Frog`: 5
- `Empty`: 8
- `Magic`: 5
- `Figure`: 2

### Card Types
- **Bomb**: Deducts 1 HP from the player who opens it.
- **Frog**: No immediate effect (base rule).
- **Empty**: No effect.
- **Magic**: Adds the specific Magic Card assigned to that board position to the player's hand.
- **Figure**: Changes the player's current figure to the one opened.

### Hand Rules
- Both players begin the game with an empty hand.
- The hand limit is **3 Magic Cards**.
- If a player opens a Magic Card while already holding 3 cards, they **must discard any 2 cards from their hand**, then take the newly revealed Magic Card.
- The player sees the identity of the newly revealed Magic Card before choosing which 2 cards to discard.
- This replacement is mandatory; the player cannot discard the newly revealed card instead.

### Shuffle
- `Shuffle!` uses the current 25 cards; it does not generate a new board.
- All 25 cards are turned face-down and randomly rearranged.
- Each card keeps its exact identity. For example, Magic Card #17 remains Magic Card #17 after the shuffle.
- All `X` barriers are removed.
- Because revealed cards become face-down again, they may later be opened and trigger their effects again.

### Special Rules
- **Modifications**: Cards with `(type) ± (amount) next turn` modify the distribution of the *next* turn's board only.
- **Determinism**: Magic and Figure cards are assigned to specific cells when the board is generated, not randomized upon opening.
- **W-Patterns**: Evolved figures have a "W" pattern overlay. Effects trigger when any player opens a card in a "W" position.

### Resolving Next-Turn Board Modifications
When multiple effects modify the next board, resolve them in this order:

1. Start from the default distribution, unless the game mode specifies another base distribution.
2. Add together all numerical changes such as `Bomb +1` and `Empty -1`.
3. Apply all whole-type conversion effects, such as `All Empty become Bomb`, to the resulting distribution.
4. Apply single-card conversions, such as `Change 1 Frog to Bomb`.
5. Confirm that the final board contains exactly 25 cards and that no card type has a negative count.

Example: if `Peace!` gives `Bomb -2, Empty +2` and `THE NUKE` changes all Empty cards into Bomb cards, apply `Peace!` first and then convert all resulting Empty cards into Bomb cards.

#### Conflicting Whole-Type Conversions
- Multiple whole-type conversions resolve in the order their Magic Cards were played.
- Each conversion acts only on cards that still match its source type when that conversion resolves.
- Example: if `THE NUKE` (`Empty -> Bomb`) is played before `WHO ARE YOU?` (`Empty -> Figure`), `THE NUKE` converts all Empty cards first. `WHO ARE YOU?` then has no Empty cards left to convert.

#### Numerical Modification Limits
- A card type can never have fewer than 0 cards.
- A paired decrease and increase transfer only as many cards as can actually be removed from the source type.
- Example: if an effect says `Magic -2, Empty +2` but only 1 Magic Card remains, resolve it as `Magic -1, Empty +1`.
- Any part of a decrease that cannot be completed is ignored; it never creates additional cards elsewhere.
- These rules preserve a total of exactly 25 cards.

---

## 🎴 Magic Cards
*(IDs start from 1)*

1.  **bubble tea**: `Self: +1 HP`
2.  **sanshoku dango**: `Self: +3 HP`
3.  **wine**: `Opponent: +1 HP`, `Self: +2 HP`
4.  **beep**: `Next turn: Bomb +1, Empty -1`
5.  **beep boom**: `Next turn: Bomb +2, Empty -2`
6.  **let's be nice**: `Next turn: Bomb -1, Empty +1`
7.  **peace!**: `Next turn: Bomb -2, Empty +2`
8.  **one more please**: `Next turn: Magic +1, Empty -1`
9.  **becoming tricky!**: `Next turn: Magic +2, Empty -2`
10. **"CARD"iovascular**: `Next turn: Magic -2, Empty +2` | `Immediate: Self +2 HP`
11. **Ribbit! Ribbit! Ribbit!**: `Next turn: Frog +3, Empty -3`
12. **THE NUKE**: `Next turn: All 'Empty' become 'Bomb'`
13. **IT'S RAINING FROGS AND FROGS**: `Next turn: All 'Empty' become 'Frog'`
14. **WHO ARE YOU?**: `Next turn: All 'Empty' become 'Figure'`
15. **THAT'S FUN!**: `Next turn: All 'Empty' become 'Magic'`
16. **Shuffle!**: Turns all current cards face-down, clears all 'X' barriers, and rearranges the same 25 cards. Card identities do not change.
17. **Take a look!**: Reveal 1 chosen card.
18. **Take 3 looks!**: Reveal 3 chosen cards.
19. **the birth of BOB**: Change any player's figure to 'Bob'.
20. **const figure**: Prevents a player's figure from changing for 3 turns.
21. **shredder**: Discard 1 card from your hand, then choose 1 card for opponent to discard.
22. **REVEAL!**: Reveal all 'Magic' cards on the board for this turn.
23. **This is curse!**: Choose one magic card from each hand. They are played automatically as the first actions next turn.
24. **Frog bomb**: `Next turn: Change 1 'Frog' to 'Bomb'`
25. **Swap**: Swap hands with your opponent.

---

## 🧍 Figures
*(IDs start from 200)*

- **200: bob**: No special ability.
- **201: pawn**: 10% chance each turn to evolve into Queen, Rook, Bishop, or Knight.

### 👑 Evolved Figures (Pawn only)

**202: queen**
```text
W O W O W
O W W W O
W W Q W W
O W W W O
W O W O W
```
- Opponent picks 'W': -1 HP (Once/turn).
- You pick 'W': +1 HP (Once/turn).

**203: bishop**
```text
W O O O W
O W O W O
O O B O O
O W O W O
W O O O W
```
- Opponent picks 'W': -0.5 HP.
- You pick 'W': +0.5 HP.

**204: knight**
```text
O W O W O
W O O O W
O O K O O
W O O O W
O W O W O
```
- Opponent picks 'W': -0.5 HP.
- You pick 'W': +0.5 HP.

**205: rook**
```text
O O W O O
O O W O O
W W R W W
O O W O O
O O W O O
```
- Opponent picks 'W': -0.5 HP.
- You pick 'W': +0.5 HP.

### 🌟 Special Figures

- **206: foreteller**: Reveal 3 cards at the start of your first step each turn.
- **207: princess**: When *you* open a 'Frog', gain +1 HP (Once/turn).
- **208: witch**: Opponent loses 1 HP at the start of each turn.
- **209: tic-tac-toeR**: Set an 'X' barrier on a card before any step. It cannot be picked this turn.
- **211: alcoholic**: Random card is chosen for you during 'Open a card' step.
- **212: copy cat**: Copies the opponent's current figure once when Copy Cat takes effect. It does not continue following later changes to the opponent's figure.
- **213: abusive lover**: All HP changes affect both players equally.
- **214: gambler**: Open Bomb: -2 HP | Open Frog: Opponent -1 HP.
- **215: psychopath**: Opening a Bomb deals 3 damage instead of 1.
- **216: magician**: May 'Shuffle!' the board once per turn.
- **217: lucky bob**: 30% chance to avoid any damage.
- **218: unlucky bob**: 30% chance to double any damage taken.
- **219: Politician**: At turn start, revealed cards close and closed cards reveal.

---

## 📝 Game Notes
- 'Shuffle!' breaks all 'X' barriers.
- Opening a Figure Card normally replaces the player's current figure immediately.
- While `Const Figure` protection is active, **all figure changes fail**, regardless of their source.
- A Figure Card opened during this protection is still considered used and remains revealed, but the player's figure does not change.
- Evolved Pawn figures (Queen, Bishop, Knight, and Rook) cannot be generated as normal Figure Cards on the board.
- Copy Cat copies once rather than maintaining a live link to the opponent.

### Figure Change Timing
- The figure that opened a Figure Card remains responsible for resolving that card-opening event.
- After the Figure Card finishes resolving, the old figure's abilities stop and the new figure's abilities become active immediately.
- A newly acquired figure cannot retroactively affect the event that caused it to enter play.

### Once-Per-Turn Figure Abilities
- Once-per-turn usage is tracked separately for each figure identity and each player.
- Acquiring a different figure during a turn gives access to that figure's unused once-per-turn ability.
- Leaving a figure and returning to the same figure during the same turn does not reset that figure's ability.
- All once-per-turn figure usage records reset at the start of a new turn.

### Temporary Effects and Figure Changes
- Effects provided by the current figure end when that figure is replaced, unless the ability explicitly created an independent lasting effect.
- Temporary effects created by Magic Cards belong to the affected player or board and remain active after a figure change.
- `Const Figure` is a Magic Card effect and therefore does not disappear because of a figure change.

---

## 🛠️ Project Structure
1. **`design_note.md`**: Game rules and card effects.
2. **`cards/__init__.py`**: Definition of `MagicCard` and `FigureCard` classes and catalogs.
3. **`player.py`**: Player state (HP, hand, figure).
4. **`board.py`**: 5x5 grid management.
5. **`game.py`**: Game logic and turn orchestration.
6. **`main.py`**: Entry point.
