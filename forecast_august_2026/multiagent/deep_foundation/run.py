"""Run all deep-learning / foundation candidates through the shared harness.

python run.py   ->  results/{predictions,summary}.csv, cutoff_check.txt
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import harness  # noqa: E402
import models  # noqa: E402


def zs_ensemble(ctx):
    """A-priori equal-weight mix: Chronos-2 statewide(log) + Chronos-2 county + Bolt-base statewide."""
    return float(np.mean([models.ZERO_SHOT[k](ctx) for k in
                          ("chronos2_state_log", "chronos2_county", "bolt_base_state")]))


def dl_ensemble(ctx):
    """A-priori mix of the zero-shot ensemble and the three global neural nets."""
    return float(np.mean([zs_ensemble(ctx)] + [f(ctx) for f in models.NEURAL.values()]))


if __name__ == "__main__":
    t0 = time.time()
    all_models = {**models.ZERO_SHOT, **models.NEURAL,
                  "zs_ensemble": zs_ensemble, "dl_ensemble": dl_ensemble}
    summ = harness.evaluate(all_models, HERE / "results")
    pd.set_option("display.width", 250)
    print(summ.round(4).to_string(index=False))
    print(f"total runtime {time.time() - t0:.0f}s")
