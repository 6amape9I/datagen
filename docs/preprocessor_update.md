# Preprocessor rebuild plan for `6amape9I/datagen`

## Purpose

Rebuild Stage 01 so that it stops acting like a fragile, Russian-centric semantic classifier and becomes a robust, multilingual **UD normalizer + unit builder + model input packager**.

The end result must preserve the project’s core goal:

> convert Universal Dependencies corpora into the project’s internal sentence representation and prepare high-quality input for the model that assigns `syntactic_link_name`.

This document is written for a Codex execution agent. Treat it as an implementation brief, not as a brainstorming note.

---

## Executive summary

The current preprocessor is doing too many jobs at once:

1. reads `.conllu`
2. deletes / merges tokens destructively
3. tries to infer semantic candidates using a large heuristic ruleset
4. exports a compact format for the LLM stage

That design was acceptable while the pipeline was Russian-first and the heuristic logic roughly matched the data. It becomes brittle after adding typologically different languages, because:

- merge logic is not language-agnostic
- function words are inconsistently treated across languages
- important UD evidence is lost before the model sees it
- heuristic candidate generation is overemphasized even though the model is more trusted than the rules
- the exported format is not reversible and is hard to debug

The new preprocessor must therefore be rebuilt around these principles:

- **preserve original UD evidence**
- **build reversible semantic units** instead of destructive merges
- **prepare better model input** instead of pretending to know the final semantic label
- **support multilingual corpora by design**
- **keep backward compatibility long enough to avoid breaking downstream stages while the migration is in progress**

---

## What must change conceptually

### Old meaning of Stage 01

Stage 01 currently behaves like a hybrid of:

- parser
- cleaner
- semantic guesser
- exporter

### New meaning of Stage 01

Stage 01 must become:

- **UD reader**
- **token normalizer**
- **semantic unit builder**
- **feature packager for LLM annotation**
- **soft hint generator**
- **compatibility exporter**

It must **not** be responsible for hard semantic decisions.

The preprocessor may produce soft hints, structural annotations, and optional candidate suggestions, but it must stop acting as if it is the source of truth for `syntactic_link_name`.

---

## Core design decisions

### 1. Preserve two levels of representation

The rebuilt stage must preserve both:

#### A. Raw UD tokens
Each sentence must keep a near-lossless token layer.

Each raw token record should contain at least:

- `token_id`
- `form`
- `lemma`
- `upos`
- `xpos`
- `feats`
- `head_token_id`
- `deprel`
- `misc`
- `deps` if available
- original token order / position

#### B. Normalized semantic units
The stage must also build a second layer of units that are more convenient for the model.

Each unit should contain at least:

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
- optional `semantic_candidates_soft`

This dual representation is mandatory.

**Reason:** destructive merge-only output is not debuggable, not reversible, and fails badly across languages.

---

### 2. Replace destructive merges with reversible attachment

The system must no longer delete function tokens as the only source of truth.

Instead:

- preserve raw tokens in the sentence record
- optionally attach some tokens to units for model convenience
- keep explicit metadata describing what was attached and why

#### Examples

Instead of only producing:

- `in_America`
- `of_discrimination`
- `В_период`

also preserve that the unit was built from:

- head token
- introducing marker(s)
- attached function tokens
- token span

This is especially important for determiners, adpositions, markers, particles, auxiliaries, and language-specific function words.

---

### 3. Stop using hard semantic candidates as the main value of Stage 01

Current candidate generation based on rules must be demoted.

#### Required new behavior

The new Stage 01 must output:

- **structural evidence** for the model
- **soft hints** derived from UD
- optionally **soft candidate suggestions**

It must not assume that a hand-written rule list is the main mechanism for semantic disambiguation.

#### New distinction

- `ud_semantic_hints`: descriptive and non-binding
- `semantic_candidates_soft`: optional shortlist, non-binding
- `syntactic_link_name`: never assigned in Stage 01

#### Constraint

Any remaining candidate generator must be:

- optional
- clearly marked as heuristic
- easily disabled
- never treated as the sole validation boundary for model output during this rebuild

---

### 4. Make multilingual handling explicit

The preprocessor must be designed for the following language mix, not only Russian:

- Germanic
- Slavic
- Romance
- Uralic
- Chinese / Classical Chinese
- Japanese
- Korean
- Hebrew
- Armenian

This means the architecture must avoid assumptions like:

- articles always behave like Russian determiners
- case morphology is always present and informative
- markers always precede the head
- `amod`, `nmod`, `obl`, `case`, `det` can be collapsed the same way everywhere

The design must prefer:

- universal UD evidence first
- language-family-sensitive attachment policies second
- language-specific exceptions only when unavoidable

---

## Non-goals

The Codex agent must **not** attempt the following inside this task unless a change is strictly required by the rebuild:

1. redesign the role ontology
2. rewrite Stage 03 inference behavior from scratch
3. replace the whole LLM stack
4. re-annotate existing datasets
5. hand-tune per-language semantic mapping rules for all supported languages
6. optimize throughput at the cost of correctness and clarity
7. silently remove existing outputs or compatibility paths

This task is about **rebuilding preprocessing**, not refactoring the whole repository into a new product.

---

## Mandatory implementation goals

### Goal A — introduce a versioned preprocessed schema

Add a formal schema version for Stage 01 output.

Use a field such as:

- `preprocessed_schema_version: 2`

The schema must clearly separate:

- sentence metadata
- raw token layer
- normalized unit layer
- optional soft hints
- optional compatibility export

### Goal B — preserve sentence-level metadata

Each sentence record must contain at least:

- `sentence_id`
- `text`
- `language_code`
- `split`
- `source_file`
- `preprocessed_schema_version`

### Goal C — keep compatibility with downstream code during migration

Do **not** break the pipeline abruptly.

Implement one of these options:

1. Stage 01 writes the new v2 structure and additionally exports a legacy-compatible node array for Stage 03 to consume temporarily
2. or Stage 03 converter is updated in the same work package to read v2 units directly

Preferred outcome: **do both**.

That means:

- new schema becomes the primary source of truth
- legacy node export remains available until migration is complete

---

## Required target file structure

The exact names may vary slightly if needed, but the structure must become close to this.

```text
01_preprocessor/
├── main.py
├── reader.py
├── schemas.py
├── sentence_builder.py
├── token_normalizer.py
├── unit_builder.py
├── attachment_policy.py
├── hints.py
├── exporter.py
├── legacy_export.py
├── report.py
└── tests/
    ├── test_reader.py
    ├── test_unit_builder.py
    ├── test_attachment_policy.py
    ├── test_hints.py
    └── test_legacy_export.py
```

If the agent proposes slightly different filenames, that is acceptable, but the responsibilities must still be split into these conceptual modules.

---

## Required output schema (v2)

Below is the target shape. The implementation may add fields, but it must not collapse everything back into a flat opaque node list.

```json
{
  "preprocessed_schema_version": 2,
  "sentence_id": "eng_en_gum-ud-train.conllu_1",
  "text": "The prevalence of discrimination across racial groups in contemporary America:",
  "language_code": "eng",
  "split": "train",
  "source_file": "eng_en_gum-ud-train.conllu",
  "tokens": [
    {
      "token_id": "1",
      "form": "The",
      "lemma": "the",
      "upos": "DET",
      "xpos": "DT",
      "feats": {"Definite": "Def", "PronType": "Art"},
      "head_token_id": "2",
      "deprel": "det",
      "misc": {}
    }
  ],
  "units": [
    {
      "unit_id": "w2",
      "head_token_id": "2",
      "span_token_ids": ["1", "2"],
      "surface": "The prevalence",
      "core_lemma": "prevalence",
      "upos": "NOUN",
      "xpos": "NN",
      "features": {"Number": "Sing"},
      "syntactic_link_target_id": null,
      "original_deprel": "root",
      "attached_tokens": [
        {
          "token_id": "1",
          "relation": "det",
          "attachment_type": "determiner"
        }
      ],
      "introduced_by": [],
      "function_parts": [],
      "ud_semantic_hints": ["nominal_head", "has_determiner"],
      "semantic_candidates_soft": []
    }
  ],
  "legacy_nodes": [
    {
      "id": "w2",
      "name": "The_prevalence",
      "lemma": "prevalence",
      "pos_universal": "NOUN",
      "pos_specific": "NN",
      "features": {"Number": "Sing"},
      "syntactic_link_target_id": null,
      "original_deprel": "root",
      "syntactic_link_candidates": []
    }
  ]
}
```

Important:

- `legacy_nodes` is transitional
- `units` is the new authoritative layer
- `tokens` must remain available for debugging and future model input improvements

---

## Attachment policy redesign

### Problem

The current code merges several dependency types destructively and inconsistently. That may work for some Russian patterns, but it does not scale well to English determiners, Romance articles, Uralic morphology, East Asian function markers, or Semitic constructions.

### Required solution

Introduce a formal **attachment policy** with three classes:

### Class 1 — generally safe attachment
These are usually attached to the semantic unit but preserved in raw tokens:

- `case`
- `mark`
- `fixed`
- some `det`
- some `compound:prt`
- some `flat`

### Class 2 — contextual attachment
These may be attached depending on POS, language profile, and local structure:

- `cc`
- `cop`
- `aux`
- `clf`
- `compound`
- `flat:name`
- particles
- selected symbols

### Class 3 — preserve as independent structure
These must normally remain their own units or their own structural evidence:

- clause heads
- content words
- numerals with independent semantics
- coordinated main units
- appositional structures with real semantic content

### Hard requirement

The policy must be data-driven enough to be readable and testable.

Do **not** scatter implicit merge decisions across the codebase.

---

## Soft hints redesign

Implement a new module that derives **soft semantic hints** from UD evidence.

Examples of acceptable hints:

- `temporal_oblique`
- `locative_phrase`
- `nominal_modifier`
- `genitive_modifier`
- `determiner_attached`
- `adpositional_introducer`
- `clausal_subordinator`
- `numeric_modifier`
- `root_predicate`
- `coordination_member`

Hints must be:

- descriptive
- low-risk
- language-neutral where possible
- useful to the model
- non-binding

Avoid inventing hints that are secretly just semantic role labels under different names.

---

## What to do with heuristic candidate generation

### Decision

Do not delete candidate generation immediately, but demote it and isolate it.

### Required behavior

1. move any remaining heuristic relation shortlist logic into a separate module
2. rename it so it is obviously heuristic, for example:
   - `heuristic_candidates.py`
   - `semantic_candidates_soft.py`
3. make it optional
4. default it to conservative mode
5. never let it contaminate the core unit-building logic

### Temporary compatibility

If downstream validation still depends on candidates, provide them in `legacy_nodes`, but keep them clearly separated from the new `units` contract.

---

## Stage 03 migration requirements

The work package must also update the preprocessing-to-LLM handoff.

### Current weakness

The model currently sees too little information.

### Required change

Update the conversion step used before inference so that the model can consume richer unit-level evidence.

The new LLM input adapter should be able to include:

- `surface`
- `core_lemma`
- `upos`
- `xpos`
- `features`
- `syntactic_link_target_id`
- `original_deprel`
- `introduced_by`
- `attached_tokens`
- `ud_semantic_hints`
- optional `head_surface` / `head_lemma`

This does **not** mean the model prompt must expose every field immediately. It means the pipeline must make them available cleanly.

---

## Implementation phases

The agent must execute the rebuild in the following order.

---

### Phase 0 — repository audit and freeze point

Tasks:

- inspect the current Stage 01 files and note exact dependencies used by Stage 03 and Stage 04
- identify every field consumed downstream from preprocessed JSON
- create a migration map: current field -> new field / compatibility field
- avoid changing output paths yet

Deliverable:

- short migration note committed to the branch or included in code comments / docs

Exit condition:

- downstream data contract is understood before any invasive code change starts

---

### Phase 1 — introduce typed schemas and builders

Tasks:

- add sentence / token / unit schema models (dataclasses, TypedDict, or pydantic if already justified)
- centralize object construction
- remove ad-hoc dict assembly from the core logic where practical

Requirements:

- schema version support must exist
- both `tokens` and `units` must be modeled explicitly

Exit condition:

- the code can build sentence objects in memory with a stable internal structure

---

### Phase 2 — rebuild sentence reading and split detection without semantic coupling

Tasks:

- preserve automatic language discovery from folder names
- preserve split detection from filenames
- isolate reading / parsing from normalization and export
- keep support for multiple languages without hardcoded `eng` / `rus` assumptions

Exit condition:

- the reading layer produces stable sentence objects independent of unit merge logic

---

### Phase 3 — rebuild attachment and unit construction

Tasks:

- implement reversible attachment logic
- preserve raw tokens always
- build units from a transparent policy layer
- store attached markers / function words instead of only hiding them inside a merged surface string

Requirements:

- every unit must know which raw tokens it covers
- root handling must remain explicit
- invalid token ids, multiword tokens, and non-integer ids must be handled safely and predictably

Exit condition:

- units can be reconstructed and debugged from raw token evidence

---

### Phase 4 — add soft hints

Tasks:

- implement a hint generator using UD features and structural context
- add hints to units
- keep hints descriptive, not prescriptive

Requirements:

- hints must work even if the candidate shortlist is fully disabled

Exit condition:

- sample outputs show useful hints on multilingual examples

---

### Phase 5 — isolate or retire hard candidate logic

Tasks:

- move candidate generation into its own module
- make it optional
- reduce its conceptual importance in the preprocessor output
- keep legacy compatibility only where required

Requirements:

- the preprocessor must be able to run in a mode where no hard candidate generation is used

Exit condition:

- Stage 01 no longer depends on semantic shortlist logic for its identity

---

### Phase 6 — add legacy exporter and downstream compatibility adapter

Tasks:

- create `legacy_nodes` exporter or equivalent adapter
- keep downstream pipeline working during migration
- update Stage 03 input conversion to prefer `units` if available

Requirements:

- existing dataset generation flow must still run after the refactor
- migration path must be explicit, not implicit

Exit condition:

- downstream code can consume the new format directly or through a compatibility layer

---

### Phase 7 — testing and multilingual validation

Tasks:

- add focused tests for:
  - attachment behavior
  - token preservation
  - root handling
  - determiners and markers
  - clause-level introducers
  - numeric and temporal examples
  - legacy export shape
- create a small multilingual smoke set using at least these language types:
  - English
  - Russian or Czech
  - French or Italian
  - Finnish or Estonian
  - Chinese or Classical Chinese
  - Japanese or Korean
  - Hebrew

Requirements:

- tests must verify structure, not only absence of exceptions
- include at least a few cases where the old destructive merge would have hidden useful evidence

Exit condition:

- the new stage is proven not just on Russian-like examples

---

### Phase 8 — documentation and operational cleanup

Tasks:

- update README sections related to Stage 01
- document the new schema
- document migration / compatibility behavior
- document how to inspect raw tokens vs units

Exit condition:

- another contributor can understand what Stage 01 is supposed to do without reading internal code first

---

## Required acceptance criteria

The task is only complete if all the conditions below are satisfied.

### Correctness

- Stage 01 preserves raw token evidence for every sentence
- Stage 01 builds explicit unit structures
- root nodes are handled cleanly and predictably
- multi-language sentences no longer rely on Russian-centric destructive assumptions

### Architecture

- unit construction is separated from file reading
- attachment policy is centralized
- soft hints are separated from semantic role assignment
- heuristic candidate generation is isolated and optional

### Compatibility

- downstream pipeline still runs after migration
- Stage 03 can consume the new output directly or through a compatibility path
- existing output folders remain usable unless a deliberate versioned migration path is introduced

### Debuggability

- a contributor can trace any unit back to raw tokens
- attached function words are visible in metadata
- the output is more interpretable than the old opaque merged names

### Tests

- tests exist for the new sentence/unit construction logic
- a multilingual smoke test exists

---

## Practical design guidance for the agent

### Recommended naming behavior

Do not let naming drift back into historical semantics such as:

- `gemini`
- `fix_errors`
- `processor` doing everything

Stage 01 should use names that describe function, not legacy history.

### Recommended payload philosophy

When choosing what to export for the LLM stage, optimize for:

- clarity
- reversibility
- multilingual robustness
- explicit structure

Do not optimize for “shortest possible JSON” at this stage. The project needs better structure more than smaller payloads.

### Recommended migration philosophy

Prefer:

- additive migration
- compatibility layer
- explicit deprecation

Avoid:

- sudden output shape replacement without adapter
- hidden field meaning changes
- partial refactors that leave two contradictory concepts with the same name

---

## Concrete deliverables expected from the Codex agent

The branch produced by the agent must contain:

1. rebuilt Stage 01 code with separated responsibilities
2. versioned v2 preprocessed schema
3. reversible token + unit output
4. centralized attachment policy
5. soft hint generation
6. isolated optional heuristic candidate logic
7. compatibility export or adapter for downstream stages
8. updated Stage 03 preprocessed input adapter
9. tests for core preprocessor behavior
10. updated documentation

---

## Suggested execution checklist

Use this as a concrete checklist during implementation.

- [ ] audit current Stage 01 output and downstream dependencies
- [ ] add internal schema models for sentence, token, unit
- [ ] split reader / builder / exporter responsibilities
- [ ] implement raw token preservation
- [ ] implement reversible unit builder
- [ ] implement centralized attachment policy
- [ ] add soft hint generator
- [ ] isolate heuristic candidates into optional module
- [ ] export new v2 structure
- [ ] export legacy-compatible structure
- [ ] update Stage 03 adapter to understand v2 units
- [ ] add unit tests
- [ ] add multilingual smoke fixtures
- [ ] update README / docs

---

## Final directive

Do not produce a shallow cosmetic refactor.

The purpose of this task is to **change the meaning of Stage 01** from a brittle heuristic semantic pre-classifier into a multilingual, debuggable, reversible structural preparation layer for the model.

If a design choice improves short-term backward compatibility but preserves the old conceptual mistake, reject that choice.
If a design choice requires a compatibility layer but makes the new architecture correct, choose the compatibility layer.
