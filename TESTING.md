"""
Card Game - Terminal Testing Guide
"""

# 🎮 如何在 Python 終端中運行遊戲

## 方法 1：直接運行主程序
```bash
cd /home/zeta/Desktop/cardGAME
python main.py
```

## 方法 2：在 Python 互動式終端中運行
```bash
python3
```

```python
from game import Game

# 建立遊戲
game = Game(p1_name="Alice", p2_name="Bob")

# 開始遊戲
game.run()
```

## 方法 3：快速測試（不互動）
```python
from game import Game
from board import Board
from player import Player
from cards import MAGIC_CARDS, FIGURE_CARDS

# 建立單個組件進行測試
board = Board()
p1 = Player("Alice", hp=5)
p2 = Player("Bob", hp=5)

# 查看棋盤
print("玩家視角:")
board.display_player_view()

print("\n上帝模式（顯示所有卡牌）:")
board.display_debug_view()

# 翻卡
cell = board.open_cell(5)
print(f"卡牌類型: {cell.type}")

# 玩家受傷
p1.take_damage(2)
print(p1)  # Player(Alice, HP=3/5, Figure=#200, Hand=0 spells)
```

---

## 🎯 遊戲流程說明

### 每回合
1. **生成步驟順序** — 隨機排列 3 個 P1 步驟 + 3 個 P2 步驟
2. **顯示順序** — 告訴玩家這回合的步驟順序
3. **執行 6 個步驟**

### 每個步驟
玩家可以：
- **選項 1**：查看棋盤（玩家視角 - 只看翻開的卡）
- **選項 2**：查看棋盤（上帝模式 - 看所有卡）
- **選項 3**：使用手牌中的魔法卡（結束步驟）
- **選項 4**：翻開一張卡（結束步驟）

### 卡牌類型
- **Empty** — 什麼都沒有
- **Bomb** — 玩家受 -1 傷害
- **Frog** — 玩家恢復 +0.5 HP
- **Magic** — 隨機抽一張魔法卡到手牌
- **Figure** — 改變玩家的角色

---

## 📝 當前實現

✅ 完整的遊戲循環
✅ 回合和步驟管理
✅ 棋盤翻卡邏輯
✅ 玩家視角 + 上帝模式
✅ 基本卡牌效果（bomb、frog、magic、figure）
✅ HP 追蹤和勝負判定

⚠️ 還需要實現
- 魔法卡效果系統（目前 "TODO: Apply spell effect"）
- 角色卡效果系統
- 更完善的數值平衡

---

## 🧪 測試卡牌信息

```python
from cards import MAGIC_CARDS, FIGURE_CARDS

# 查看魔法卡
magic = MAGIC_CARDS[1]
print(f"卡牌: {magic.name}")
print(f"效果: {magic.effect}")

# 查看角色卡
figure = FIGURE_CARDS[202]  # Queen
print(f"卡牌: {figure.name}")
print(f"效果: {figure.effect}")
print(f"棋盤圖案:")
for row in figure.board_pattern:
    print("  " + row)
```
