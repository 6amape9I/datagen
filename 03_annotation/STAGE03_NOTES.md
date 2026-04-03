# Stage 03 — Annotation

Stage 03 reads compact Stage 01 records from `datasets/02_preprocessed`, sends `text + nodes[]` to the model layer, validates the returned labels, and writes `datasets/04_fixed/*.jsonl`.

## Input contract

Each sentence contains:

- `text`
- `nodes[]`

Each node contains:

- `id`
- `name`
- `lemma`
- `pos_universal`
- `features`
- `syntactic_link_target_id`
- `original_deprel`
- optional `introduced_by`

## Validator rules

- output node IDs must match input IDs exactly
- duplicate or extra IDs fail
- `syntactic_link_name` must belong to the shared ontology
- `ROOT` is valid only when `syntactic_link_target_id` is `null`

## Commands

```bash
python 03_annotation/pipeline.py
python 03_annotation/scheduler.py
```
