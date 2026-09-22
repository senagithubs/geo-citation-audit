import copy
import tempfile
import unittest
from pathlib import Path
from citation_audit import flatten, metrics, bootstrap, run


def fixture():
    return {"asqa": {"config": {"q1": {"id": "q1", "sentences": [
        {"citations": [{"title": "A"}], "sentence_recall_score": 1},
        {"citations": [{"title": "B"}], "sentence_recall_score": 0},
        {"citations": [], "sentence_recall_score": 0},
        {"citations": [{"title": "C"}], "sentence_recall_score": 1},
    ], "automatic_recall_scores": [1, 1, 0, 0]}, "overall_results": {"ignored": True}}}}


class AuditTests(unittest.TestCase):
    def test_known_confusion_and_denominators(self):
        m = metrics(flatten(fixture()))
        self.assertEqual(m["confusion_matrix"], dict(true_positive=1, false_positive=1, false_negative=1, true_negative=1))
        self.assertEqual(m["unsupported_share_of_cited_sentences"], 1/3)
        self.assertEqual(m["human_support_rate"], .5)
        self.assertEqual(m["citation_presence_rate"], .75)
        self.assertEqual(m["answers"], 1)

    def test_mismatched_sentence_alignment_fails(self):
        data = fixture(); data["asqa"]["config"]["q1"]["automatic_recall_scores"].pop()
        with self.assertRaises(ValueError): flatten(data)

    def test_invalid_annotation_fails(self):
        data = fixture(); data["asqa"]["config"]["q1"]["sentences"][0]["sentence_recall_score"] = 2
        with self.assertRaises(ValueError): flatten(data)

    def test_zero_denominators_are_missing_not_zero(self):
        row = flatten(fixture())[2]
        m = metrics([row])
        self.assertIsNone(m["unsupported_share_of_cited_sentences"])
        self.assertIsNone(m["automatic_precision_vs_human"])
        self.assertIsNone(bootstrap([row], 20)["unsupported_share_of_cited_sentences"]["lower"])

    def test_task_identity_and_bootstrap_clusters(self):
        data = fixture(); data["eli5"] = copy.deepcopy(data["asqa"])
        rows = flatten(data)
        self.assertEqual(metrics(rows)["questions"], 2)
        self.assertEqual(metrics(rows)["answers"], 2)
        b = bootstrap(rows, 40)
        self.assertEqual(b["human_support_rate"]["lower"], .5)
        self.assertEqual(b["human_support_rate"]["upper"], .5)
        self.assertEqual(b, bootstrap(rows, 40))

    def test_changed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "data.json"; source.write_text("{}")
            with self.assertRaisesRegex(ValueError, "SHA256"):
                run(source, Path(directory) / "reports")

    def test_all_published_configurations(self):
        import json
        source = Path("data/human_eval_citations_completed.json")
        if not source.exists(): self.skipTest("Run download_data.py for the source integration test")
        rows = flatten(json.loads(source.read_text()))
        m = metrics(rows)
        self.assertEqual((m["answers"], m["questions"], m["sentences"]), (778, 200, 2604))
        self.assertEqual(len({(r["dataset"], r["configuration"]) for r in rows}), 8)

    def test_empty_answer_is_not_a_sentence(self):
        data = fixture()
        data["asqa"]["config"]["empty"] = {"id": "empty", "sentences": [], "automatic_recall_scores": []}
        self.assertEqual(len(flatten(data)), 4)


if __name__ == "__main__": unittest.main()
