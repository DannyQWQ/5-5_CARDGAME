# Testing Guide

## Automated tests

Run the core rule suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

The tests currently cover:

- valid 25-card board generation;
- pre-assigned Magic and Figure identities;
- shuffling the same physical cards;
- the 3-card hand limit and mandatory two-card discard;
- safe failure before mutating board or hand state;
- numerical modifications before conversions;
- conversion ordering;
- three-state visibility, Reveal, Open, Politician, and X barriers;
- Shredder, Curse, Swap restrictions, Const Figure, and Copy Cat;
- W-patterns and abusive lover HP mirroring;
- turn-start and step-start ordering;
- simultaneous defeat resulting in a draw.

## Terminal prototype

```powershell
python main.py
```

The shared-screen Terminal interface supports public hands and public Reveal information. It prompts for all targets needed by Magic Cards, Foreteller, and tic-tac-toeR, and automatically resolves cursed actions on the affected player's next step.

## Deterministic rule experiments

Inject a seeded random-number generator when reproducing a scenario:

```python
import random
from game import Game

game = Game("Alice", "Bob", rng=random.Random(42))
```

Using the same seed produces the same initial board and step shuffle, which makes bugs reproducible.
