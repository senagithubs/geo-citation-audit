# Provenance and attribution

- Source: Princeton NLP's ALCE release, `human_eval/human_eval_citations_completed.json`.
- Authors: Tianyu Gao, Howard Yen, Jiatong Yu and Danqi Chen.
- Paper: *Enabling Large Language Models to Generate Text with Citations* (EMNLP 2023).
- Pinned repository commit: `246c476a4edfc564266b7346b6e29ef4861ae937`.
- Retrieved: 2026-09-22. These are historical published observations, not observations collected on this date.
- Source SHA256: `cfed9293752413d7c7631f36524dd4ee9ef58b209cdf9c63f6fc1e280b43cca6`.
- Direct source: https://raw.githubusercontent.com/princeton-nlp/ALCE/246c476a4edfc564266b7346b6e29ef4861ae937/human_eval/human_eval_citations_completed.json
- Annotation documentation: https://github.com/princeton-nlp/ALCE/tree/246c476a4edfc564266b7346b6e29ef4861ae937/human_eval
- Upstream license: MIT, copyright 2023 Princeton Natural Language Processing; notice retained at `data/LICENSE`.

The derived CSVs retain IDs and annotation-derived numbers, not full answer or
passage text. `download_data.py` obtains the original file and checks its hash.
The upstream analysis script is not included or relabelled as project work.

`citation_audit.py`, tests, figures, methodology and report implement this project's
secondary analysis. No new human annotations or live search responses are claimed.
