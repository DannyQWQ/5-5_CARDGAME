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
- Const Figure and Copy Cat basics;
- simultaneous defeat resulting in a draw.

## Terminal prototype

```powershell
python main.py
```

The terminal interface exercises the implemented core rules. Some cards requiring additional private choices or temporary visibility are intentionally rejected with a clear `NotImplementedError` until their interaction rules are finalized.

## Deterministic rule experiments

Inject a seeded random-number generator when reproducing a scenario:

```python
import random
from game import Game

game = Game("Alice", "Bob", rng=random.Random(42))
```

Using the same seed produces the same initial board and step shuffle, which makes bugs reproducible.
