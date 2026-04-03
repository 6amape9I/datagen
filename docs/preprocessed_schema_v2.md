# Stage 01 preprocessed schema v2

Stage 01 now writes a versioned sentence structure in `datasets/02_preprocessed/*.json`.

## Authority rules

- `tokens` is the authoritative raw UD layer.
- `units` is the authoritative normalized layer.
- `legacy_nodes` is transitional compatibility output for downstream stages.

## Top-level sentence fields

Each sentence record contains:

- `preprocessed_schema_version`
- `sentence_id`
- `text`
- `language_code`
- `split`
- `source_file`
- `tokens`
- `units`
- `legacy_nodes`

## `tokens`

`tokens` preserve near-lossless UD evidence for debugging and future model packaging.

Each raw token stores:

- `token_id`
- `form`
- `lemma`
- `upos`
- `xpos`
- `feats`
- `head_token_id`
- `deprel`
- `misc`
- `deps`
- `token_index`
- `is_integer_id`

Notes:

- multiword tokens and empty nodes remain visible in `tokens`;
- punctuation remains visible in `tokens`;
- `feats` and `misc` preserve multi-valued UD attributes as lists.

## `units`

`units` are the normalized semantic units used by Stage 03.

Each unit stores:

- `unit_id`
- `head_token_id`
- `span_token_ids`
- `surface`
- `core_lemma`
- `upos`
- `xpos`
- `features`
- `syntactic_link_target_id`
- `original_deprel`
- `attached_tokens`
- `introduced_by`
- `function_parts`
- `ud_semantic_hints`
- `semantic_candidates_soft`

Notes:

- function words are attached reversibly, not deleted;
- `span_token_ids` lets you trace every unit back to raw UD tokens;
- `introduced_by` is for adpositions and clause introducers;
- `semantic_candidates_soft` is heuristic and non-binding.

## `legacy_nodes`

`legacy_nodes` keeps Stage 03 validator and Stage 04 postprocessor compatible while the migration is in progress.

It preserves the old node shape:

- `id`
- `name`
- `lemma`
- `pos_universal`
- `pos_specific`
- `features`
- `syntactic_link_candidates`
- `syntactic_link_target_id`
- `original_deprel`
- optional `link_introduction_info`
- optional `function_parts`

## Downstream behavior

- `03_gemini_fix_errors/pipeline.py` prefers `units` for model input.
- `03_gemini_fix_errors/validator.py` validates against `legacy_nodes`.
- `04_postprocessor/prepare_final_dataset.py` reads `legacy_nodes`.
- `02_local_generation/pipeline.py` uses `legacy_nodes` only to compare expected node counts.
