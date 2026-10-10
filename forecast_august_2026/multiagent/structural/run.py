"""Run all structural models through the shared harness (Protocols A, B, final)."""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))   # harness
sys.path.insert(0, str(HERE))

import harness  # noqa: E402
from models import MODELS  # noqa: E402

if __name__ == "__main__":
    models = dict(harness.BASELINES)
    models.update(MODELS)
    s = harness.evaluate(models, HERE / "results")
    pd.set_option("display.width", 250)
    print(s.round(4).to_string(index=False))
