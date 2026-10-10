"""Run all statistical models (plus the two reference baselines) through the shared harness."""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
np.random.seed(0)

import harness  # noqa: E402
import models  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    out = HERE / "results"
    s = harness.evaluate({**harness.BASELINES, **models.MODELS}, out)
    fb = [dict(model=k, target=a, metric=b, reason=c) for k, v in models.FALLBACKS.items() for a, b, c in v]
    pd.DataFrame(fb, columns=["model", "target", "metric", "reason"]).drop_duplicates().to_csv(
        out / "fallbacks.csv", index=False)
    pd.DataFrame(models.SELECTIONS).drop_duplicates().to_csv(out / "damped_auto_selections.csv", index=False)
    pd.set_option("display.width", 250)
    print(s.round(4).to_string(index=False))
    print(f"runtime {time.time() - t0:.1f}s")
