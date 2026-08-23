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

### Turn-Start Resolution Order
Resolve the start of every turn in this fixed order:

1. Remove temporary Reveals and all `X` barriers left by the previous turn.
2. Reset all once-per-turn ability usage records.
3. Update the remaining duration of `Const Figure` protection.
4. Each Pawn makes its 10% evolution roll.
5. Each Politician resolves its visibility inversion. Two Politicians therefore invert the board twice and restore its original visibility.
6. All Witch turn-start damage resolves simultaneously.
7. Check for a winner or draw. If the game has ended, do not create any steps.
8. Randomize and announce the six-step order.
9. Begin the first step.

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
- An Opened card cannot be selected again while it remains Opened.
- A card's normal open effect triggers only when it changes from Face-down or Revealed to Opened.

### Step-Start Resolution Order
Resolve every step in this fixed order:

1. Identify the active player.
2. If this is that player's first step of the turn, resolve Foreteller.
3. Resolve tic-tac-toeR placement opportunities: the active player first, then the opponent.
4. Check whether the active player has a cursed card.
5. If cursed, the player must resolve that card and the step ends.
6. Otherwise, the player chooses one normal main action.
7. If an alcoholic chooses to Open, the game randomly selects one legal card instead of allowing a manual choice.
8. Resolve the action completely and check for a winner or draw.

After the sixth step, keep the final board and action result visible. The players explicitly continue only after they have reviewed that state; the next turn's board generation must not immediately cover the sixth step's outcome.

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

### Card Visibility States
Every board card is in exactly one of these states:

- **Face-down**: Its identity is hidden. It may be selected and Opened.
- **Revealed**: Its full identity is public to both players, but its effect has not triggered. It may still be selected and Opened.
- **Opened**: Its identity is public and its effect has already triggered. It cannot be selected again while it remains Opened.

`Reveal` is public information; there is no private `Peek` action because both players share the same game screen.

- Revealing a card never triggers its normal open effect.
- Opening a Revealed card changes it from Revealed to Opened and resolves its effect normally.
- Unless an effect says otherwise, cards Revealed by a temporary effect return to Face-down at the end of the current turn.

### Hand Rules
- Both players begin the game with an empty hand.
- The hand limit is **3 Magic Cards**.
- If a player opens a Magic Card while already holding 3 cards, they **must discard any 2 cards from their hand**, then take the newly revealed Magic Card.
- The player sees the identity of the newly revealed Magic Card before choosing which 2 cards to discard.
- This replacement is mandatory; the player cannot discard the newly revealed card instead.

### Shuffle
- `Shuffle!` uses the current 25 cards; it does not generate a new board.
- All Revealed and Opened cards are turned Face-down, then all 25 cards are randomly rearranged.
- Each card keeps its exact identity. For example, Magic Card #17 remains Magic Card #17 after the shuffle.
- All `X` barriers are removed.
- Because revealed cards become face-down again, they may later be opened and trigger their effects again.

### Special Rules
- **Modifications**: Cards with `(type) ± (amount) next turn` modify the distribution of the *next* turn's board only.
- **Determinism**: Magic and Figure cards are assigned to specific cells when the board is generated, not randomized upon opening.
- **W-Patterns**: When the active player Opens a card, check only that player's current figure pattern. The opponent's figure pattern does not react to the active player's action. Reveal never triggers a W-pattern.

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
17. **Take a look!**: Choose 1 row or 1 column. Reveal every Face-down card in that line until the end of the current turn. Cards already Revealed or Opened remain unchanged. This is public and does not trigger any card.
18. **Take 3 looks!**: Reveal 3 different chosen cards until the end of the current turn. This is public and does not trigger those cards.
19. **the birth of BOB**: Change any player's figure to 'Bob'.
20. **const figure**: Prevents a player's figure from changing for 3 turns. The turn in which this card is played counts as the first protected turn, even if it is played during the final step of that turn. Protection expires at the start of the turn after the third protected turn.
21. **shredder**: May be played only if you have at least 1 other Magic Card in hand and the opponent also has at least 1 Magic Card in hand. After playing Shredder, choose and discard 1 of your remaining cards, then choose and discard 1 card from the opponent's hand. If either player lacks a required card before Shredder is played, the action is invalid and Shredder remains in hand.
22. **REVEAL!**: Reveal the full identities of all Magic Cards that have not been Opened until the end of the current turn. They may still be selected and Opened normally.
23. **This is curse!**: Choose 1 Magic Card in the opponent's hand and mark it as cursed. The next time that opponent receives a step, they lose their normal action and must play the cursed card instead.
    - The trigger is the cursed player's next **step**, regardless of turn boundaries. It may trigger later in the current turn if that player still has an upcoming step.
    - The player who played `This is curse!` chooses only which opposing card is cursed.
    - When the curse triggers, the cursed player is the card's user and makes all of its target and option choices at that time.
    - All relative terms use the cursed player's perspective: `Self` means the cursed player and `Opponent` means the player who originally played `This is curse!`.
    - Example: A curses B's `the birth of BOB`. On B's next step, B must play that card, but B decides which player becomes Bob.
    - The forced card consumes B's entire step.
    - A cursed card remains in its owner's hand but cannot be voluntarily played, discarded, or used to pay another cost before the curse triggers.
    - If the cursed card has no legal resolution when the forced step begins, it is discarded without effect and the cursed player still loses that step.
    - `This is curse!` cannot target another copy of `This is curse!`.
    - A player may have at most 1 cursed card at a time. A new `This is curse!` cannot target a player who already has one; the attempted action is invalid and the card remains in its user's hand.
    - `Swap` cannot be played while either player's hand contains a cursed card.
24. **Frog bomb**: `Next turn: Change 1 'Frog' to 'Bomb'`
25. **Swap**: Swap hands with your opponent.

---

## 🧍 Figures
*(IDs start from 200)*

- **200: bob**: No special ability.
- **201: pawn**: At the start of each turn, roll once for a 10% chance to evolve permanently into Queen, Bishop, Knight, or Rook, chosen with equal probability.
  - The evolved figure becomes active immediately during that turn.
  - Pawn still rolls while protected by `Const Figure`, but a successful evolution is blocked and not saved for later. It rolls normally again next turn.

### 👑 Evolved Figures (Pawn only)

**202: queen**
```text
W O W O W
O W W W O
W W Q W W
O W W W O
W O W O W
```
- When you Open a 'W': you gain 1 HP and the opponent loses 1 HP.
- This combined effect may trigger once per turn.

**203: bishop**
```text
W O O O W
O W O W O
O O B O O
O W O W O
W O O O W
```
- When you Open a 'W': you gain 0.5 HP and the opponent loses 0.5 HP.
- This combined effect may trigger once per turn.

**204: knight**
```text
O W O W O
W O O O W
O O K O O
W O O O W
O W O W O
```
- When you Open a 'W': you gain 0.5 HP and the opponent loses 0.5 HP.
- This combined effect may trigger once per turn.

**205: rook**
```text
O O W O O
O O W O O
W W R W W
O O W O O
O O W O O
```
- When you Open a 'W': you gain 0.5 HP and the opponent loses 0.5 HP.
- This combined effect may trigger once per turn.

### 🌟 Special Figures

- **206: foreteller**: At the start of your first step each turn, Reveal 3 different cards until the end of that turn. This does not use the main action or trigger those cards.
- **207: princess**: When *you* open a 'Frog', gain +1 HP (Once/turn).
- **208: witch**: Opponent loses 1 HP at the start of each turn.
- **209: tic-tac-toeR**: Before every step, each player currently using tic-tac-toeR may optionally place 1 new `X` barrier. Barriers accumulate until the end of the turn, and a card with `X` cannot be Opened.
  - `X` may be placed on a Face-down or Revealed card, but not an Opened card or a card that already has `X`.
  - `X` prevents Open but does not prevent Reveal.
  - All `X` barriers are removed at the end of the turn or immediately by Shuffle.
  - Politician may change the visibility of a card without removing its `X`.
  - An existing `X` remains until its normal removal time even if its owner changes figure.
  - If both players are tic-tac-toeR, the active player receives the first placement opportunity, followed by the opponent.
- **211: alcoholic**: Random card is chosen for you during 'Open a card' step.
- **212: copy cat**: Copies the opponent's current figure once when Copy Cat takes effect. It does not continue following later changes to the opponent's figure.
- **213: abusive lover**: While at least one player is abusive lover, any HP change actually received by either player is mirrored once to the other player.
  - Mirrored HP changes never trigger another mirror, so the effect cannot recurse.
  - If both players are abusive lover, the change is still mirrored only once; it is not doubled.
  - Mirror the amount that actually changed the original player's HP, not the amount printed on the card or ability.
  - The original and mirrored HP changes are simultaneous. If the mirrored damage reduces both players to 0 HP or below, the game ends in a draw.
  - Example: if a `+3 HP` effect can restore only 0.5 HP because the original player is near maximum HP, the other player is also offered only +0.5 HP, subject to their own maximum HP.
  - For damage, resolve the original recipient's Lucky Bob or Unlucky Bob modifier first, then mirror the resulting actual HP loss.
  - The recipient of mirrored damage does not make another Lucky Bob or Unlucky Bob roll; the mirror must remain equal to the original actual loss.
- **214: gambler**: Open Bomb: -2 HP | Open Frog: Opponent -1 HP.
- **215: psychopath**: Opening a Bomb deals 3 damage instead of 1.
- **216: magician**: May 'Shuffle!' the board once per turn.
- **217: lucky bob**: Before each separate damage event is applied, independently roll for a 30% chance to reduce that event's damage to 0. Healing does not cause a roll.
- **218: unlucky bob**: Before each separate damage event is applied, independently roll for a 30% chance to double that event's damage. This applies to fractional damage as well.
- **219: Politician**: At turn start, invert the board's visible truth without triggering any card: every Face-down card becomes Revealed, while every Revealed or Opened card becomes Face-down. This intentionally represents saying black is white and white is black.
  - Cards Revealed by Politician remain Revealed until another effect changes their state; they are not automatically hidden at the end of the turn.
  - If both players are Politician, both abilities resolve once, so the board is inverted twice and returns to its original visibility state.

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
The design document is the source of truth. Code and card data must be changed to match this document, not the other way around.

1. **`design_note.md`**: Canonical game rules and card descriptions.
2. **`cards/magic.py`**: Immutable Magic Card definitions only; it does not execute effects.
3. **`cards/figures.py`**: Immutable Figure definitions and which figures may appear on the board.
4. **`cards/__init__.py`**: Public imports for the two canonical card catalogs; it contains no duplicate catalog.
5. **`player.py`**: Player-owned state and invariants, including HP, stateful hand cards, the 3-card hand limit, Curse, current figure, locks, and once-per-turn usage records.
6. **`board.py`**: The 25 physical board cards, their pre-assigned identities, three visibility states, barriers, Reveal, Open, and Shuffle. It never applies HP or hand effects.
7. **`effects.py`**: The single effect pipeline for HP changes, abusive lover mirroring, Magic effects, Figure effects, W-patterns, and next-turn board modifications.
8. **`game.py`**: Turn and step orchestration, forced actions, action timing, and win/draw resolution. It performs no terminal input or output.
9. **`cli.py`**: Shared-screen Terminal input, validation prompts, target selection, and rendering.
10. **`main.py`**: Minimal Terminal entry point.
11. **`tests/`**: Executable checks grouped by board, player, effects, and flow responsibilities.
