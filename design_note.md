# Card Game Design

## 🎮 Core Game Rules

### Objective
- Two-player turn-based card game
- Each player starts with **5 HP**. HP values can be fractional (e.g., 0.5 HP).
- The first player to reach 0 HP or below loses.

### Board
- A **5x5 grid** (25 cards total, all face-down).
- Cards are revealed/opened during gameplay.

### Turn Structure
Each turn consists of **6 steps total**:
- 3 steps for Player 1
- 3 steps for Player 2
- **Order is randomized** (shown to players at turn start).

(The display would be like this for turn order):

```
Turn: P1 P2 P2 P2 P1 P1
Step: X  O  O  O  O  O
```
('X' means current step, 'O' means upcoming steps for the current turn)

P1 hand (cards) ? ? ? ? ?, 5 HP

[] [] [] [] []
[] [] [] [] []
[] [] [] [] []
[] [] [] [] []
[] [] [] [] []

P2 hand (cards) ? ? ? ? ?, 5 HP

### Step Actions
On each step, a player:
1.  **Optionally** choose and use a magic card from their hand (choosing and using a card ends the step).
2.  **Open a card** from the board.
3.  Apply the card's effects.

### Winning Condition
- Reduce opponent's HP to 0 or below.

---

### Basic Card and Board Rules

- A new 25-card board is generated each turn.
- The distribution of card types (bomb, empty, frog, magic, figure) on the board may vary depending on game mode or specific magic abilities.

`DEFAULT_DISTRIBUTION` = {
        "bomb": 5,
        "frog": 5,
        "empty": 8,
        "magic": 5,
        "figure": 2
    }

Basically, when opening a card:
-   **Bomb**: Automatically deducts 1 HP from the player who opened it.
-   **Frog**: No immediate effect.
-   **Empty**: No immediate effect.
-   **Magic**: Adds the specific magic card (pre-determined for that cell when the board is generated) into the player's hand.
-   **Figure**: Automatically changes the player's current figure to the specific figure opened.

Note that some special abilities (e.g., certain Figures) can alter these basic effects. For instance, the 'Princess' Figure grants +1 HP when opening a 'frog' card.

Card effects denoted as `(type) ± (amount) next turn` modify the card distribution for the *next* turn's board generation. For example, 'THE NUKE' magic card changes all 'empty' cards to 'bomb' cards for the next turn, meaning the next board might contain 0 'empty' and 13 'bomb' cards.

Players have a hand limit of five magic cards. If a player opens a magic card while their hand is full, they cannot pick up the new magic card.

The specific magic card or figure card associated with a 'magic' or 'figure' cell is determined at the start of each turn when the board is generated. For instance, if cell ID 3 is a 'magic' card, it will always be a specific magic card for that entire turn, not randomly generated upon opening. This is important for cards that reveal hidden cells.

Both players start the game with an empty hand (no magic cards).

The 'W' pattern for Evolved Figures will be visually displayed as a 5x5 overlay on the game board. Its effects apply instantly when a card corresponding to a 'W' position (relative to the figure's pattern) is selected and opened by either player.

---

## 🎴 Magic Cards
(IDs start from 1)

(1) **bubble tea**
<self +1 HP>

(2) **sanshoku dango**
<self +3 HP>

(3) **wine**
<opponent +1 HP> <self +2 HP>

(4) **beep**
<Bomb (type) +1, Empty (type) -1 next turn>

(5) **beep boom**
<Bomb (type) +2, Empty (type) -2 next turn>

(6) **let's be nice**
<Bomb (type) -1, Empty (type) +1 next turn>

(7) **peace!**
<Bomb (type) -2, Empty (type) +2 next turn>

(8) **one more please**
<Magic Card (type) +1, Empty (type) -1 next turn>

(9) **becoming tricky!**
<Magic Card (type) +2, Empty (type) -2 next turn>

(10) **"CARD"iovascular**
<Magic Card (type) -2, Empty (type) +2 next turn | self +2 HP (now)>

(11) **Ribbit! Ribbit! Ribbit!**
<Frog (type) +3, Empty (type) -3 next turn>

(12) **THE NUKE**
<All 'empty' cells become 'bomb' cells next turn>

(13) **IT'S RAINING FROGS AND FROGS**
<All 'empty' cells become 'frog' cells next turn>

(14) **WHO ARE YOU?**
<All 'empty' cells become 'figure' cells next turn>

(15) **THAT'S FUN!**
<All 'empty' cells become 'magic' cells next turn>

(16) **Shuffle!**
<Shuffle the board (re-covers all cards and removes 'X' barriers)>

(17) **Take a look!**
<Reveal 1 chosen card on the board>

(18) **Take abc looks!**
<Reveal 3 chosen cards on the board>

(19) **the birth of BOB**
<Change your or opponent's current figure to 'Bob'>

(20) **const figure**
<Prevents a chosen player's figure from changing for 3 turns>

(21) **shredder**
<Discard one card from your hand, then choose one card for your opponent to discard from their hand>

(22) **REVEAL!**
<Reveal all 'magic' cards on the board this turn>

(23) **This is curse!**
<Choose one magic card from your hand and one from your opponent's. These two cards are automatically played as your first actions next turn (cannot choose 'This is Curse!' itself)>

(24) **Frog bomb**
<Change one 'frog' cell to a 'bomb' cell next turn>

(25) **Swap**
<Swap your hand with your opponent's hand>

---

## 🧍‍♂️ Figures
(IDs start from 200)

(200) **bob**
<No special ability>

(201) **pawn**
<Each turn, has a 10% chance to evolve into a Queen, Rook, Bishop, or Knight>

### 👑 Evolved from Pawn (Won't be drawn on the board directly)

(202) **queen**
The Queen's 'W' pattern on the 5x5 board is:
```
WOWOW
OWWWO
WWQWW
OWWWO
WOWOW
```
- If opponent picks a 'W' position: -1 HP (once per turn).
- If you pick a 'W' position: +1 HP (once per turn).

(203) **bishop**
The Bishop's 'W' pattern on the 5x5 board is:
```
WOOOW
OWOWO
OOWOO
OWOWO
WOOOW
```
- If opponent picks a 'W' position: -0.5 HP.
- If you pick a 'W' position: +0.5 HP.

(204) **knight**
The Knight's 'W' pattern on the 5x5 board is:
```
OWOWO
WOOOW
OOWOO
WOOOW
OWOWO
```
- If opponent picks a 'W' position: -0.5 HP.
- If you pick a 'W' position: +0.5 HP.

(205) **rook**
The Rook's 'W' pattern on the 5x5 board is:
```
OOWOO
OOWOO
WWWWW
OOWOO
OOWOO
```
- If opponent picks a 'W' position: -0.5 HP.
- If you pick a 'W' position: +0.5 HP.

### 🌟 Special Figures

(206) **foreteller**
<Reveal 3 chosen cards at the beginning of your first step each turn>

(207) **princess**
<When *you* open a 'frog' card, gain +1 HP (effect triggers once per turn)>

(208) **witch**
<Opponent loses 1 HP at the start of each turn>

(209) **tic-tac-toeR**
<Before each step (both players' steps), you may set an 'X' barrier on a board card. Neither player can pick that card for the rest of the current turn. The barrier disappears at the end of the turn. 'Shuffle!' magic breaks all 'X' barriers.>

(211) **alcholic**
<During your 'Open a card' step, a random card is chosen for you; you cannot choose manually>

(212) **copy cat**
<Copies your opponent's current figure>

(213) **abusive lover**
<All HP gains or losses now affect both players (e.g., if you gain 1 HP, opponent gains 1 HP; if opponent loses 1 HP, you lose 1 HP)>

(214) **gambler**
<When *you* open a 'bomb' card: lose 2 HP | When *you* open a 'frog' card: opponent loses 1 HP>

(215) **psychopath**
<When *any* 'bomb' card is opened: the player who opened it loses 3 HP instead of 1>

(216) **magician**
<You may 'Shuffle!' the board once per turn>

(217) **lucky bob**
<Has a 30% chance to avoid all damage when taking HP loss>

(218) **unlucky bob**
<Has a 30% chance to double all damage when taking HP loss>

(219) **Politician**
<At the start of each turn, all revealed cards on the board are closed, and all closed cards are revealed>

---

## 📝 Game Notes

-   'Shuffle!' breaks all 'X' barriers and re-covers all revealed/opened cards on the board.
-   Opening a 'figure' card *must* result in changing to that figure, unless 'Const Figure' is active.


### AI instruction about how to read this file
Okay, I can definitely help you with a structured way to read through these files to understand your game design and implementation. It's great you're reorganizing for clarity!

Here's a recommended reading order, moving from high-level concepts to detailed implementation:

1.  **`design_note.md`**
    *   **Why**: This is your single source of truth for the game's rules, mechanics, and card effects. Start here to understand *what* the game is, *how* it's played, and *what each card does* before diving into the code. This document lays the conceptual foundation.

2.  **`cards/__init__.py`**
    *   **Why**: This file defines the fundamental Python classes for `MagicCard` and `FigureCard`, and importantly, it contains the `MAGIC_CARDS` and `FIGURE_CARDS` dictionaries that act as your game's card catalog. It also defines `FIGURE_EFFECTS` which shows how certain figures modify basic card interactions. Understanding these data structures is crucial before seeing them used in `player.py` or `game.py`.

3.  **`cards/magic.py`**
    *   **Why**: This file (though currently a separate, unlinked definition) is intended to hold the detailed data for your magic cards, including their effects, timings, and specific data. It's a more structured way to define the actual mechanics that `MAGIC_CARDS` in `cards/__init__.py` would eventually point to or use. Reading this will give you a deeper understanding of how each spell is supposed to function.
    *   *(Note: Currently, `cards/__init__.py` defines `MAGIC_CARDS` directly with effects. If you intend `cards/magic.py` to be the primary source for magic card data, you'll need to integrate it into `cards/__init__.py` by importing `MAGIC_CARDS_DATA` and constructing `MagicCard` objects from it.)*

4.  **`cards/figures.py`**
    *   **Why**: This file is currently empty, but conceptually, it would mirror `cards/magic.py` by holding detailed data for your figures if you were to separate it from `cards/__init__.py`. For now, all figure data is in `cards/__init__.py`.

5.  **`player.py`**
    *   **Why**: This file defines the `Player` class. Once you understand the game rules and what "cards" are, you'll want to see how a `Player` is represented: their HP, hand, current figure, and basic actions like taking damage, healing, or using spells.

6.  **`board.py`**
    *   **Why**: This file defines the `Cell` and `Board` classes. It represents the physical play area of your game. You'll learn how individual card slots (`Cell`) are structured and how the entire 5x5 grid (`Board`) is managed, built, and displayed.

7.  **`game.py`**
    *   **Why**: This is the central orchestrator. After understanding the individual components (cards, players, board), this file brings them all together. It manages the game flow, turns, steps, applying card effects, checking win conditions, and displaying the overall state. This is where the rules from `design_note.md` are translated into high-level game logic.

8.  **`main.py`**
    *   **Why**: This is the simplest file – it's just the entry point that initializes and runs your `Game`. It's typically read last as it just kicks off the entire process.

This order should help you build your understanding layer by layer, from abstract game concepts to concrete code implementation. Good luck with rebuilding your game!