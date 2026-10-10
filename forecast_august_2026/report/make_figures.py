"""Generate every figure used in forecasting_report.tex (run from MINNEMUDAC_2026)."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates  # noqa: E402
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FA = HERE.parent
sys.path.insert(0, str(FA / "multiagent"))
from harness import load_monthly, load_site  # noqa: E402

FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 200, "savefig.bbox": "tight"})
METRICS = {"visits": "Visits (HouseholdsReg)", "pounds": "Pounds distributed",
           "individuals": "Individuals served"}
AGENT_COLORS = {"baselines": "#555555", "stats": "#1f77b4", "panel_ml": "#2ca02c",
                "deep_foundation": "#9467bd", "structural": "#ff7f0e"}

monthly = load_monthly().set_index("month")
final = pd.read_csv(FA / "multiagent" / "final_forecast_aug_2026.csv").set_index("metric")


def fig_series():
    fig, axes = plt.subplots(3, 1, figsize=(7, 6.4), sharex=True)
    for ax, (m, label) in zip(axes, METRICS.items()):
        s = monthly[m]
        ax.plot(s.index, s.values, color="#1f77b4", lw=1.4)
        aug = s[s.index.month == 8]
        ax.scatter(aug.index, aug.values, color="#d62728", zorder=3, s=18, label="August actual")
        t = pd.Timestamp("2026-08-01")
        f = final.loc[m]
        ax.errorbar([t], [f.forecast], yerr=[[f.forecast - f.lo80], [f.hi80 - f.forecast]],
                    fmt="D", color="black", ms=5, capsize=3, label="Aug 2026 forecast (80% interval)")
        ax.axvline(pd.Timestamp("2026-07-31"), color="grey", ls=":", lw=1)
        ax.set_ylabel(label)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
            lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}k"))
    axes[0].legend(loc="lower right", fontsize=7, frameon=False)
    axes[0].text(pd.Timestamp("2026-07-15"), axes[0].get_ylim()[0], "cutoff ", ha="right",
                 va="bottom", fontsize=7, color="grey")
    fig.savefig(FIG / "statewide_series.pdf")
    plt.close(fig)


def fig_sites_and_ratio():
    site = load_site()
    n = site[site["reported"] == True].groupby("month")["site_id"].nunique()  # noqa: E712
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.6))
    a1.plot(n.index, n.values, color="#2ca02c")
    a1.set_title("Reporting sites per month")
    a1.tick_params(axis="x", rotation=30)
    yrs = [2022, 2023, 2024, 2025]
    w = 0.26
    for k, m in enumerate(METRICS):
        r = [monthly.loc[f"{y}-08-01", m] / monthly.loc[f"{y}-07-01", m] for y in yrs]
        a2.bar(np.arange(4) + (k - 1) * w, r, w, label=m)
    a2.axhline(1, color="black", lw=0.8)
    a2.set_xticks(range(4), yrs)
    a2.set_ylim(0.85, 1.2)
    a2.set_title("August / July ratio")
    a2.legend(fontsize=7, frameon=False, ncol=3, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "sites_and_ratio.pdf")
    plt.close(fig)


def fig_required_models():
    s = pd.read_csv(FA / "multiagent" / "baselines" / "results" / "summary.csv")
    order = ["seasonal_naive", "ytd_growth", "aug_jul_ratio", "trend_month_regression", "robust_ensemble"]
    labels = ["Naive", "YTD", "Ratio", "Trend", "Ens."]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.6), sharey=True)
    for ax, m in zip(axes, METRICS):
        g = s[s.metric == m].set_index("model").loc[order]
        x = np.arange(len(order))
        for k, (yr, c) in enumerate(zip([2023, 2024, 2025], ["#c6dbef", "#6baed6", "#08519c"])):
            ax.bar(x + (k - 1) * 0.27, 100 * g[f"aug_{yr}"], 0.27, color=c, label=str(yr))
        ax.set_xticks(x, labels, fontsize=6.5)
        ax.set_title(m)
    axes[0].set_ylabel("August APE (%)")
    axes[0].legend(title="Aug fold", fontsize=7, title_fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "required_models.pdf")
    plt.close(fig)


def fig_leaderboard():
    c = pd.read_csv(FA / "multiagent" / "leaderboard_candidates.csv")
    c = c[~c.model.str.contains(":damped_yoy_3m$|dyoy_w3_d0.5$")
          | c.model.eq("baselines:damped_yoy_3m")]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.8), sharey=True)
    for ax, m in zip(axes, METRICS):
        g = c[c.metric == m]
        for agent, col in AGENT_COLORS.items():
            h = g[g.agent == agent]
            ax.scatter(100 * h.monthly_mape, 100 * h.aug_mape_2024_25, s=12, color=col,
                       alpha=.8, label=agent)
        for name, mk in [("baselines:seasonal_naive", "s"), ("baselines:damped_yoy_3m", "^")]:
            r = g[g.model == name].iloc[0]
            ax.scatter(100 * r.monthly_mape, 100 * r.aug_mape_2024_25, marker=mk, s=60,
                       facecolor="none", edgecolor="black", lw=1.2)
        ax.set_xlim(3, 14)
        ax.set_ylim(0, 22)
        ax.set_title(m)
        ax.set_xlabel("Monthly MAPE, 31 origins (%)")
    axes[0].set_ylabel("Aug 2024--25 MAPE (%)".replace("--", "-"))
    axes[0].legend(fontsize=6, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "leaderboard.pdf")
    plt.close(fig)


def fig_honest():
    d = pd.read_csv(FA / "multiagent" / "honest_selection_detail.csv")
    g = d.groupby(["metric", "method"]).ape.mean().unstack(0) * 100
    order = ["seasonal_naive", "damped_yoy_3m", "online_top1", "online_top3", "online_top5"]
    g = g.loc[order, list(METRICS)]
    fig, ax = plt.subplots(figsize=(6.4, 2.4))
    x = np.arange(len(order))
    for k, m in enumerate(METRICS):
        ax.bar(x + (k - 1) * 0.27, g[m], 0.27, label=m)
    ax.set_xticks(x, ["Seasonal naive", "Damped YoY", "Online best-1", "Online best-3", "Online best-5"])
    ax.set_ylabel("MAPE, Jan 2025-Jul 2026 (%)")
    ax.legend(fontsize=7, frameon=False, ncol=3)
    fig.tight_layout()
    fig.savefig(FIG / "honest_selection.pdf")
    plt.close(fig)


def fig_county_backtest():
    d = pd.read_csv(FA / "submission" / "county_backtest_detail.csv", parse_dates=["target"])
    d = d[d.protocol == "monthly"]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.5), sharey=True)
    styles = {"blend": ("black", "-"), "mmf_select": ("#2ca02c", "--"),
              "damped_yoy_3m": ("#ff7f0e", ":"), "seasonal_naive": ("#7f7f7f", "-.")}
    for ax, m in zip(axes, METRICS):
        g = d[d.metric == m].pivot(index="target", columns="model", values="county_wape")
        g = g.rolling(3, min_periods=1).mean() * 100
        for model, (col, ls) in styles.items():
            ax.plot(g.index, g[model], color=col, ls=ls, lw=1.3, label=model)
        ax.set_title(m)
        ax.xaxis.set_major_locator(matplotlib.dates.YearLocator())
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
    axes[0].set_ylabel("County WAPE, 3-mo rolling (%)")
    axes[0].legend(fontsize=6.5, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "county_backtest.pdf")
    plt.close(fig)


def fig_top_counties():
    sub = pd.read_csv(FA / "submission" / "Undergraduate_Predictions_Submit.csv")
    site = load_site()
    last = site[site.month == "2025-08-01"].groupby(site.county.str.lower())["visits"].sum()
    sub["aug25"] = sub.County.str.lower().map(last).fillna(0)
    top = sub.nlargest(15, "HouseholdReg_Predicted").iloc[::-1]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    y = np.arange(len(top))
    ax.barh(y + 0.2, top.aug25, 0.4, color="#bdbdbd", label="Aug 2025 actual")
    ax.barh(y - 0.2, top.HouseholdReg_Predicted, 0.4, color="#1f77b4", label="Aug 2026 forecast")
    ax.set_yticks(y, top.County)
    ax.set_xlabel("Visits (HouseholdsReg)")
    ax.legend(fontsize=7, frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "top_counties.pdf")
    plt.close(fig)


if __name__ == "__main__":
    for f in (fig_series, fig_sites_and_ratio, fig_required_models, fig_leaderboard,
              fig_honest, fig_county_backtest, fig_top_counties):
        f()
        print("ok", f.__name__)
