# Ancre pytest à la racine du dépôt, et rend importable le sous-projet
# ``playground/`` (distribution urban-workflow-playground) sans installation.

import sys
from pathlib import Path

_playground = Path(__file__).parent / "playground"
if str(_playground) not in sys.path:
    sys.path.insert(0, str(_playground))
