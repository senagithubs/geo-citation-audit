"""Render charts from the audit's derived tables, without new measurements."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def render(report_dir=Path("reports")):
    summary = json.loads((report_dir / "summary.json").read_text())
    configs = list(csv.DictReader((report_dir / "configurations.csv").open()))
    target = report_dir / "figures"; target.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.spines.left": False})
    fig, ax = plt.subplots(figsize=(10, 4.2), layout="constrained")
    groups = [("All sentences", summary["overall"])] + [(d.upper(), m) for d, m in summary["datasets"].items()]
    y = np.arange(len(groups))
    for offset, key, label, color in [(-.18,"citation_presence_rate","Citation present", "#98b8cd"),
                                    (.18,"human_support_rate","Human-supported", "#087f83")]:
        values = [m[key] * 100 for _, m in groups]
        ax.barh(y + offset, values, height=.31, color=color, label=label)
        for yy, value in zip(y + offset, values): ax.text(value + 1, yy, f"{value:.1f}%", va="center", fontsize=11)
    ax.set(yticks=y, yticklabels=[f"{d} (n={m['sentences']:,})" for d,m in groups], xlim=(0,105),
           xlabel="Share of annotated sentences (%)")
    ax.invert_yaxis(); ax.legend(loc="lower right", frameon=False)
    ax.grid(axis="x", alpha=.15); ax.set_axisbelow(True)
    fig.savefig(target / "citation_vs_support.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    labels = [r["dataset"].upper() + " | " + r["configuration_label"] for r in configs]
    values = [100 * float(r["human_support_rate"]) for r in configs]
    ax.barh(np.arange(8), values, color=["#087f83" if r["dataset"]=="asqa" else "#376480" for r in configs])
    for i,v in enumerate(values): ax.text(v+1,i,f"{v:.1f}%",va="center")
    ax.set(yticks=np.arange(8), yticklabels=labels, xlim=(0,100), xlabel="Human-supported sentences (%)")
    ax.invert_yaxis(); ax.grid(axis="x", alpha=.15); ax.set_axisbelow(True)
    fig.savefig(target / "configuration_support.png", dpi=180); plt.close(fig)


if __name__ == "__main__": render()
