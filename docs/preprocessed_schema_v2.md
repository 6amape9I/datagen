# Stage 01 preprocessed schema v2

Stage 01 writes versioned records to `datasets/02_preprocessed/*.json`.

## Authority rules

- `tokens` is the authoritative raw UD layer.
- `units` is the authoritative normalized layer.
- `legacy_nodes` is optional compat export only.

## Top-level sentence fields

Every record contains:

- `preprocessed_schema_version`
- `sentence_id`
- `text`
- `language_code`
- `split`
- `source_file`
- `tokens`
- `units`

Optional fields:

- `legacy_nodes` when `PREPROCESSOR_EXPORT_MODE=canonical+legacy`

## `tokens`

`tokens` preserve near-lossless UD evidence.

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

- punctuation remains visible in `tokens`
- multiword tokens and empty nodes remain visible in `tokens`
- `feats` and `misc` preserve multi-valued UD attributes as lists

## `units`

`units` is the canonical downstream contract.

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

- function words are attached reversibly, not deleted
- `span_token_ids` lets you trace every unit back to raw tokens
- `introduced_by` stores introducer-like markers/adpositions
- `semantic_candidates_soft` is diagnostic and non-binding

## `legacy_nodes`

`legacy_nodes` is no longer required by the normal pipeline.

It exists only for:

- migration comparisons
- old dataset compatibility
- explicit debug export

Normal Stage 03/04 behavior must not depend on it.

## Downstream behavior

- `03_gemini_fix_errors/pipeline.py` builds model input from `units`
- `03_gemini_fix_errors/validator.py` validates against `units` and the shared ontology
- `04_postprocessor/prepare_final_dataset.py` builds final output from `units`
- `02_local_generation/pipeline.py` uses `units` for expected node count
