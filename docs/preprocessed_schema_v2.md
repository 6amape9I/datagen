# Stage 01 Compact Preprocessed Schema

Stage 01 writes compact records to `datasets/02_preprocessed/*.json`.

## Sentence record

Each record contains:

- `sentence_id`
- `text`
- `language_code`
- `split`
- `source_file`
- `nodes`

There is no persisted raw token layer, no schema version switch, and no compatibility export in the normal path.

## Node record

Each node contains:

- `id`
- `name`
- `lemma`
- `pos_universal`
- `features`
- `syntactic_link_target_id`
- `original_deprel`

Optional:

- `introduced_by`

`introduced_by` is a compact list of marker/adposition forms, for example `["in"]` or `["В"]`.

## Example

```json
{
  "sentence_id": "arm_train_000001",
  "text": "В Армении число ИТ-специалистов составляло около десяти тысяч.",
  "language_code": "arm",
  "split": "train",
  "source_file": "arm_train.conllu",
  "nodes": [
    {
      "id": "w10",
      "name": "В Армении",
      "lemma": "Армения",
      "pos_universal": "PROPN",
      "features": {
        "Case": "Loc"
      },
      "syntactic_link_target_id": "w5",
      "original_deprel": "obl",
      "introduced_by": ["В"]
    }
  ]
}
```

## Downstream contract

- `02_local_generation/pipeline.py` reads `text` and `nodes`, and checks node-count parity by `nodes`
- `03_annotation/pipeline.py` builds model input from compact `nodes`
- `03_annotation/validator.py` validates ID parity and ontology correctness against compact `nodes`
- `04_postprocessor/prepare_final_dataset.py` joins Stage 01 nodes with Stage 03 labels by `id`

## Non-goals

The normal preprocessed artifact does not store:

- raw UD `tokens`
- normalized `units`
- `legacy_nodes`
- `syntactic_link_candidates`
- `semantic_candidates_soft`
- builder internals such as `span_token_ids`, `attached_tokens`, or `function_parts`
