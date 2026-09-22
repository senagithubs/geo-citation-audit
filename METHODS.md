# Study protocol and measurement definitions

## Question and scope

Does the presence of a citation imply that a sentence is supported by its cited
passages? How often does the published automatic support assessment disagree
with the published human assessment?

This is an original secondary analysis of an existing benchmark, not a new
live-engine experiment. The analysis uses all eight available ALCE human-evaluation
configurations, with 100 answers each: four on ASQA and four on ELI5. Each task
shares 100 question IDs across its four configurations. No results are excluded
because they contradict an expected finding. The upstream `overall_results`
summary objects are not observations and are excluded from flattening.

The source includes 22 empty answers. They remain in the answer inventory with
status `empty_answer`, and have no sentence-level observations. The 778 non-empty
answers contribute 2,604 sentences. Sentence rates and answer-weighted support
means exclude empty answers; this is not an overall answer-success measure.
All 200 task/question pairs retain at least one non-empty configuration.

## Measures

- **Citation presence:** at least one citation in the annotated `citations` list.
  This counts valid annotated citation references, not every bracket in raw text.
- **Human support:** `sentence_recall_score == 1`, meaning the cited passages
  collectively support the sentence according to the source human annotation.
- **Automatic support:** the aligned `automatic_recall_scores` label. The original
  evaluator is not rerun in this project.
- **Unsupported share of cited sentences:** cited sentences labelled unsupported
  divided by all cited sentences. A zero denominator is missing, not zero.
- **Agreement:** compare automatic and human binary support labels with an explicit
  confusion matrix. Human labels are a reference assessment, not infallible truth.

The primary aggregates are sentence-weighted: longer answers contribute more
sentences. `configurations.csv` also includes an answer-weighted mean support rate
so readers can distinguish the two estimands. Citation mention counts are not
unique domains, unique documents or source visibility shares.

## Uncertainty and integrity

95% percentile intervals use 2,000 bootstrap replications (seed 20260922).
Question IDs are resampled within each task, retaining all configurations and
sentences for each sampled question. This preserves within-question dependence
and fixed task composition. It does not model annotation error or generalisation
to the population of all search queries. No significance test or causal claim is
made. Dataset bytes are SHA256-checked before analysis; alignment errors and
nonbinary support labels stop the run.

## Interpretation limits

The historical ALCE study concerns citation-grounded answer generation, not today's
commercial search rankings. ASQA and ELI5 differ in question and answer style;
configuration comparisons also differ in retrieval method and document count.
These are descriptive contrasts, not controlled estimates of a model effect.
The analysis does not establish SEO uplift, German language proficiency, real
client results, or the effectiveness of adding citations to a website.

Human annotations, prompts, answers and evidence passages belong to the original
research release. This project contributes its analysis question, validation,
derived tables, uncertainty estimates, visualisations and interpretation.
