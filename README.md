# snake-game-using-python-create-with-AI

Simple Snake game implemented in Python using `pygame`.

Run locally:

1. Create a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the game:

```bash
python3 snake_real.py
```

Controls: arrow keys or WASD. Press `R` to restart after game over, `Q` or `Esc` to quit.

Notes:
- The game displays a small watermark (`praveenkanth2805`) on the screen.
- Simple eat and game-over sounds are synthesized using `numpy` + `pygame`.
