"""Pool every agent's predictions and apply the pre-registered SELECTION_RULE.md."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from harness import summarize

HERE = Path(__file__).parent
NAIVE = "baselines:seasonal_naive"


def load_all() -> pd.DataFrame:
    frames = []
    for f in sorted(HERE.glob("*/results/predictions.csv")):
        agent = f.parent.parent.name
        d = pd.read_csv(f)
        d["model"] = agent + ":" + d["model"].astype(str)
        d["agent"] = agent
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["target_month"] = pd.to_datetime(d["target_month"]).dt.date
    return d.drop_duplicates(["protocol", "target_month", "metric", "model"])


def qualifies(row: pd.Series, naive: pd.Series, n_fail: int) -> bool:
    return (row.monthly_mape <= naive.monthly_mape - 0.01
            and row.aug_mape < naive.aug_mape
            and row.aug_mape_2024_25 <= naive.aug_mape_2024_25 + 0.015
            and n_fail == 0)


def main() -> None:
    pred = load_all()
    summ = summarize(pred)
    fails = (pred.assign(f=pred["prediction"].isna())
             .groupby(["metric", "model"])["f"].sum())
    summ["n_fail"] = [int(fails.get((m, k), 0)) for m, k in zip(summ.metric, summ.model)]
    summ["agent"] = summ["model"].str.split(":").str[0]

    decisions, combos = [], []
    for metric, g in summ.groupby("metric"):
        naive = g[g.model == NAIVE].iloc[0]
        g = g.assign(qualifies=[qualifies(r, naive, r.n_fail) for r in g.itertuples()])
        summ.loc[g.index, "qualifies"] = g["qualifies"]
        q = g[g.qualifies].sort_values("monthly_mape")
        top = q.drop_duplicates("agent").head(3)["model"].tolist()
        choice, why = NAIVE, "no challenger qualified"
        if top:
            sub = pred[(pred.metric == metric) & pred.model.isin(top)]
            comb = (sub.groupby(["protocol", "target_month", "metric"], as_index=False)
                    .agg(prediction=("prediction", "mean"), actual=("actual", "first")))
            comb["model"] = "combo:" + "+".join(top)
            comb["ape"] = (comb.prediction / comb.actual - 1).abs()
            combos.append(comb)
            cs = summarize(comb).iloc[0]
            if len(top) > 1 and qualifies(cs, naive, 0):
                choice, why = cs.model, f"equal-weight combination of {len(top)} qualifying models"
            else:
                choice, why = top[0], "best single qualifying model (combination did not qualify or only one model qualified)"
        decisions.append(dict(metric=metric, selected=choice, reason=why))

    allpred = pd.concat([pred] + combos, ignore_index=True)
    full = summarize(allpred)
    full.to_csv(HERE / "leaderboard_all.csv", index=False)
    summ.to_csv(HERE / "leaderboard_candidates.csv", index=False)
    dec = pd.DataFrame(decisions)
    dec["forecast_aug_2026"] = [full[(full.metric == r.metric) & (full.model == r.selected)]
                                ["forecast_aug_2026"].iloc[0] for r in dec.itertuples()]
    dec.to_csv(HERE / "final_selection.csv", index=False)
    pd.set_option("display.width", 250, "display.max_colwidth", 90)
    print(dec.to_string(index=False))


if __name__ == "__main__":
    main()
