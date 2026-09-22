"""Reproducible secondary analysis of ALCE's published human annotations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

SOURCE_SHA256 = "cfed9293752413d7c7631f36524dd4ee9ef58b209cdf9c63f6fc1e280b43cca6"
SOURCE_COMMIT = "246c476a4edfc564266b7346b6e29ef4861ae937"
SOURCE_URL = f"https://raw.githubusercontent.com/princeton-nlp/ALCE/{SOURCE_COMMIT}/human_eval/human_eval_citations_completed.json"
SEED = 20260922


def config_label(filename):
    if "vicuna" in filename:
        return "Vicuna 13B / 3 documents"
    if "rerank" in filename:
        return "GPT-3.5 / reranked samples"
    if "interact" in filename:
        return "GPT-3.5 / interactive retrieval"
    return "GPT-3.5 / 5 documents"


def flatten(data):
    """Validate nested records, preserving task/question/configuration identities."""
    rows = []
    for dataset, configurations in data.items():
        for configuration, answers in configurations.items():
            for question_id, answer in answers.items():
                if question_id == "overall_results":
                    continue
                sentences = answer["sentences"]
                automatic = answer["automatic_recall_scores"]
                if len(sentences) != len(automatic):
                    raise ValueError(f"Sentence alignment failure: {dataset}/{configuration}/{question_id}")
                if str(answer["id"]) != str(question_id):
                    raise ValueError("Question identity mismatch")
                for i, (sentence, auto) in enumerate(zip(sentences, automatic)):
                    human = sentence["sentence_recall_score"]
                    if human not in (0, 1) or auto not in (0, 1):
                        raise ValueError("Support labels must be binary")
                    citations = sentence["citations"]
                    if not isinstance(citations, list):
                        raise ValueError("Citations must be a list")
                    rows.append({
                        "dataset": dataset, "configuration": configuration,
                        "configuration_label": config_label(configuration),
                        "question_id": str(question_id), "sentence_index": i,
                        "citation_count": len(citations), "citation_present": int(bool(citations)),
                        "human_supported": int(human), "automatic_supported": int(auto),
                    })
    if not rows:
        raise ValueError("No annotated sentences")
    return rows


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def metrics(rows):
    n = len(rows)
    cited = sum(r["citation_present"] for r in rows)
    human = sum(r["human_supported"] for r in rows)
    auto = sum(r["automatic_supported"] for r in rows)
    tp = sum(r["human_supported"] == 1 and r["automatic_supported"] == 1 for r in rows)
    fp = sum(r["human_supported"] == 0 and r["automatic_supported"] == 1 for r in rows)
    fn = sum(r["human_supported"] == 1 and r["automatic_supported"] == 0 for r in rows)
    tn = n - tp - fp - fn
    unsupported_cited = sum(r["citation_present"] == 1 and r["human_supported"] == 0 for r in rows)
    return {
        "sentences": n, "answers": len({(r["dataset"], r["configuration"], r["question_id"]) for r in rows}),
        "questions": len({(r["dataset"], r["question_id"]) for r in rows}),
        "citation_mentions": sum(r["citation_count"] for r in rows),
        "cited_sentences": cited, "human_supported_sentences": human,
        "automatic_supported_sentences": auto, "unsupported_cited_sentences": unsupported_cited,
        "citation_presence_rate": ratio(cited, n), "human_support_rate": ratio(human, n),
        "automatic_support_rate": ratio(auto, n),
        "unsupported_share_of_cited_sentences": ratio(unsupported_cited, cited),
        "automatic_human_disagreement_rate": ratio(fp + fn, n),
        "automatic_precision_vs_human": ratio(tp, tp + fp),
        "automatic_recall_vs_human": ratio(tp, tp + fn),
        "confusion_matrix": {"true_positive": tp, "false_positive": fp, "false_negative": fn, "true_negative": tn},
    }


def bootstrap(rows, replications=2000, seed=SEED):
    """Task-stratified question-cluster percentile bootstrap, sentence-weighted."""
    if replications < 2:
        raise ValueError("At least two replications required")
    groups = defaultdict(lambda: defaultdict(lambda: np.zeros(5, dtype=float)))
    for r in rows:
        groups[r["dataset"]][r["question_id"]] += np.array([
            1, r["citation_present"], r["human_supported"],
            r["citation_present"] and not r["human_supported"],
            r["human_supported"] != r["automatic_supported"],
        ])
    if not groups:
        raise ValueError("No bootstrap observations")
    rng = np.random.default_rng(seed)
    totals = np.zeros((replications, 5))
    for dataset in sorted(groups):
        clusters = np.array([groups[dataset][k] for k in sorted(groups[dataset])])
        indices = rng.integers(0, len(clusters), size=(replications, len(clusters)))
        totals += clusters[indices].sum(axis=1)
    rates = {
        "citation_presence_rate": totals[:, 1] / totals[:, 0],
        "human_support_rate": totals[:, 2] / totals[:, 0],
        "automatic_human_disagreement_rate": totals[:, 4] / totals[:, 0],
    }
    with np.errstate(invalid="ignore", divide="ignore"):
        rates["unsupported_share_of_cited_sentences"] = totals[:, 3] / totals[:, 1]
    result = {}
    for name, samples in rates.items():
        valid = samples[np.isfinite(samples)]
        result[name] = {
            "lower": float(np.quantile(valid, .025)) if len(valid) else None,
            "upper": float(np.quantile(valid, .975)) if len(valid) else None,
            "valid_replications": len(valid),
        }
    return result


def write_csv(path, rows):
    if not rows:
        raise ValueError("Cannot write empty table")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(source, output, replications=2000):
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError("Input SHA256 differs from the pinned public dataset")
    data = json.loads(raw)
    rows = flatten(data)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "sentences.csv", rows)
    configuration_rows = []
    answer_groups = defaultdict(list)
    config_groups = defaultdict(list)
    for row in rows:
        answer_groups[(row["dataset"], row["configuration"], row["question_id"])].append(row)
        config_groups[(row["dataset"], row["configuration"])].append(row)
    answer_rows = []
    for dataset, configurations in data.items():
        for configuration, answers in configurations.items():
            for qid, answer in answers.items():
                if qid == "overall_results":
                    continue
                group = answer_groups[(dataset, configuration, str(qid))]
                m = metrics(group)
                answer_rows.append({"dataset": dataset, "configuration": configuration, "question_id": str(qid),
                                    "status": "annotated" if group else "empty_answer",
                                    "sentences": m["sentences"], "citation_presence_rate": m["citation_presence_rate"],
                                    "human_support_rate": m["human_support_rate"],
                                    "automatic_support_rate": m["automatic_support_rate"]})
    write_csv(output / "answers.csv", answer_rows)
    for (dataset, configuration), group in sorted(config_groups.items()):
        m = metrics(group)
        m.pop("confusion_matrix")
        m["macro_answer_human_support_rate"] = float(np.mean([
            a["human_support_rate"] for a in answer_rows
            if a["dataset"] == dataset and a["configuration"] == configuration and a["status"] == "annotated"
        ]))
        m["empty_answers"] = sum(a["dataset"] == dataset and a["configuration"] == configuration and a["status"] == "empty_answer" for a in answer_rows)
        configuration_rows.append({"dataset": dataset, "configuration": configuration,
                                   "configuration_label": config_label(configuration), **m})
    write_csv(output / "configurations.csv", configuration_rows)
    summary = {
        "study": "Citation presence and evidence support in ALCE human-evaluation data",
        "analysis_date": "2026-09-22", "source_commit": SOURCE_COMMIT,
        "source_url": SOURCE_URL, "source_sha256": digest,
        "inventory": {"answer_records": len(answer_rows), "empty_answers": sum(a["status"] == "empty_answer" for a in answer_rows),
                      "annotated_answers": sum(a["status"] == "annotated" for a in answer_rows), "configurations": len(config_groups)},
        "overall": metrics(rows),
        "datasets": {d: metrics([r for r in rows if r["dataset"] == d]) for d in sorted({r["dataset"] for r in rows})},
        "bootstrap": {"method": "Task-stratified question-cluster percentile bootstrap; sentence-weighted ratios",
                      "seed": SEED, "replications": replications, "confidence_level": .95,
                      "intervals": bootstrap(rows, replications)},
        "limitations": ["Secondary analysis of historical ALCE annotations; no new engine queries or human ratings.",
                        "22 empty answers are reported separately; sentence rates and answer means exclude these empty responses.",
                        "Support refers to the supplied cited passages, not independent factual truth.",
                        "Configurations vary in retrieval, document count and generation; comparisons are descriptive.",
                        "No inference of SEO uplift, present-day engine performance, German proficiency or causality.",
                        "Intervals describe variability across these questions, not annotation error or market-wide uncertainty."],
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/human_eval_citations_completed.json"))
    parser.add_argument("--output", type=Path, default=Path("reports"))
    args = parser.parse_args()
    result = run(args.input, args.output)
    print(json.dumps(result["overall"], indent=2))
