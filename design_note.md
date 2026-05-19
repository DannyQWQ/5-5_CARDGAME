# Card Game Design

## 🎮 Core Game Rules

### Objective
- Two-player turn-based card game
- Each player starts with **5 HP**
- First player to reach 0 HP loses

### Board
- **5x5 grid** (25 cards total, all face-down)
- Cards are revealed/opened during gameplay

### Turn Structure
Each turn consists of **6 steps total**:
- 3 steps for Player 1
- 3 steps for Player 2
- **Order is randomized** (shown to players at turn start)


(so the display would be like this)

turn P1 P2 P2 P2 P1 P1
     X  O  O  O  O  O
X means current step

P1 hand(cards) ? ? ? ? ?, 5hp

[] [] [] [] []
[] [] [] [] []
[] [] [] [] []
[] [] [] [] []
[] [] [] [] []

P2 hand(cards) ? ? ? ? ?, 5hp

### Step Actions
On each step, a player:
1. **Optionally** choose and use a spell/magic card from their hand (choosing ends the step)
2. **Open a card** from the board
3. Apply the card's effects

### Winning Condition
- Reduce opponent's HP to 0 or below

---

## 🎴 Magic Cards（魔法卡）
（ID 從 1 開始）

(1) bubble tea
<self +1hp>

(2) sanshoku dango
<self +3hp>

(3) wine
<opponent +1hp> <self +2hp>

(4) beep
<bomb +1 empty -1 next turn>

(5) beep boom
<bomb +2 empty -2 next turn>

(6) let's be nice
<bomb -1 empty +1 next turn>

(7) peace!
<bomb -2 empty +2 next turn>

(8) one more please
<card +1 empty -1 next turn>

(9) becoming tricky!
<card +2 empty -2 next turn>

(10) "CARD"iovascular
<card -2 empty +2 next turn hp +2 (now)>

(11) Ribbit! Ribbit! Ribbit!
<frogs +3 empty -3>

(12) THE NUKE
<all empty turn to bomb next turn>

(13) IT'S RAINING FROGS AND FROGS
<all empty turn to frog next turn>

(14) WHO ARE YOU?
<all empty turn to figure next turn>

(15) THAT'S FUN!
<all empty turn to magic next turn>

(16) Shuffle!
<shuffle the table>

(17) Take a look!
<reveal 1 card>

(18) Take abc looks!
<reveal 3 cards>

(19) the birth of BOB
<change your's or opponent's figure into bob>

(20) const figure
<can't change figure in three turn>

(21) shredder
<you throw a card in your hand away and you choose your opponent one card in her hand to throw away>

(22) REVEAL!
<reveal all the magic cards this turn>

(23) This is curse!
<choose one magic card on both yours and opponent's to use as your magic in the next turn at first(can't choose this card)>

(24) Frog bomb
<change a frog into bomb next turn>

(25) Swap
<swap yours and opponent's hand>

🧍‍♂️ Figures（角色）
（ID 從 200 開始）

(200) bob
<just a bob>

(201) pawn
<each turn has 10% to become a queen / rook / bishop / knight>

👑 Evolved from Pawn (won't be able to draw on table)

(202) queen

WOWOW
OWWWO
WWQWW
OWWWO
WOWOW
if opponent pick on W: -1hp once per turn
if you pick on W: +1hp once per turn

(203) bishop


WOOOW
OWOWO
OOWOO
OWOWO
WOOOW
opponent pick on W: -0.5hp
you pick on W: +0.5hp

(204) knight

OWOWO
WOOOW
OOWOO
WOOOW
OWOWO
opponent pick on W: -0.5hp
you pick on W: +0.5hp

(205) rook

OOWOO
OOWOO
WWWWW
OOWOO
OOWOO
opponent pick on W: -0.5hp
you pick on W: +0.5hp

🌟 Special Figures

(206) foreteller
<reveal 3 cards each turn> at your first step of that turn

(207) princess
<open out a frog +1hp a turn>

(208) witch
<opponent -1hp a turn>

(209) tic-tac-toeR
<set a barrier "X" on a card before each step (both players' steps)>
<cannot pick that card at that turn>
<barrier will be gone after a turn>
<shuffle will break "X"> 


(211) alcholic
<randomly pick a card, player can't choose>

(212) copy cat
<copy other's figure>

(213) abusive lover
<hp + or - will now affect both players>

(214) gambler
<open a bomb: -2hp | open a frog: opponent -1hp>

(215) psychopath
<bomb = -3hp now>

(216) magician
<shuffle one time a turn> #####################

(217) lucky bob
<30% chance to avoid damage>

(218) unlucky bob
<30% chance to double damage>

(219) Politician
<the cards on the table that are revealed will be closed and the cards on the table that are closed will be revealed when the turn starts>

📝 遊戲備註

shuffle 會破壞 "X"，同時把所有 revealed / opened 卡重新蓋住

打開 figure 卡時必須更換為該 figure，除了 const figure 效果


