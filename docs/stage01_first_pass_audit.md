# Stage 01 First-Pass Audit

## Scope

First-pass audit was run on representative treebanks with `train` split and `200` sentences each:

- English: `UD_English-GUM`
- German: `UD_German-HDT`
- French: `UD_French-GSD`
- Russian: `UD_Russian-SynTagRus`
- Finnish: `UD_Finnish-TDT`
- Japanese: `UD_Japanese-GSD`
- Chinese: `UD_Chinese-GSD`
- Hebrew: `UD_Hebrew-HTB`
- Armenian: `UD_Armenian-ArmTDP`

Repro commands:

```bash
python 01_preprocessor/audit_preprocessed.py --mode preprocessed --sentence-limit 200
python 01_preprocessor/audit_preprocessed.py --mode rebuild --sentence-limit 200
```

`preprocessed` mode audits the currently materialized compact JSON in `datasets/02_preprocessed`. `rebuild` mode recomputes Stage 01 in memory from raw `.conllu` without polluting production output.

## What Was Wrong

The main first-pass issue was not one language-specific bug. The bigger problem was that language profiles were effectively underused on real corpora because many records carry treebank identifiers like `UD_English-GUM` or `UD_Hebrew-HTB`, not short ISO codes.

This created three recurring noise patterns:

- under-compression of subtype function words such as `case:*`, `mark:*`, `aux:*`
- ugly surfaces in CJK and Semitic data because builder joining assumed whitespace-friendly languages
- persistent standalone service-word nodes where the profile should have allowed attachment

## Changes

The first pass stayed intentionally narrow:

1. `get_language_profile()` now recognizes real treebank names, not just short language codes.
2. Attachment policy now handles common UD subtypes explicitly: `case:*`, `mark:*`, `det:*`, `aux:*`, `cop:*`, `flat:*`, `fixed:*`, `compound:*`, `discourse:*`.
3. `aux:*` is attachable, while plain `aux` and `cop` still preserve predicate structure.
4. CJK surfaces are joined without artificial spaces when the node is entirely CJK-script.
5. Surface cleanup strips underscore wrappers before `name` / `introduced_by` rendering.
6. Semitic determiners are now attached, which removes large numbers of standalone Hebrew article nodes.
7. A reproducible audit script now reports per-treebank compactness and attachment-decision metrics.

No raw tokens, debug traces, candidate lists, or internal builder state were added back into production JSON.

## Before / After Summary

The metrics below compare:

- `before`: currently materialized `datasets/02_preprocessed`
- `after`: in-memory rebuild from raw corpora with the updated Stage 01 rules

### Clear improvements

- English: single function-word nodes `12.20% -> 10.45%`, function POS nodes `12.87% -> 11.10%`
- German: single function-word nodes `13.22% -> 11.41%`, function POS nodes `13.78% -> 11.98%`
- French: single function-word nodes `12.78% -> 9.83%`, function POS nodes `14.60% -> 11.71%`
- Chinese: single function-word nodes `9.91% -> 8.82%`, function POS nodes `17.12% -> 8.82%`, average nodes/sentence `16.70 -> 15.19`
- Hebrew: after Semitic determiner attachment, single function-word nodes `14.44% -> 5.08%`, function POS nodes `16.52% -> 11.47%`, average nodes/sentence `15.40 -> 12.98`
- Japanese: long surfaces `4.24% -> 1.02%` due to removing artificial spaces inside CJK-script nodes

### Tradeoffs and still-open areas

- Hebrew improved strongly on standalone service-word noise, but surface quality still has spaced clitic sequences like `ב ה ציבור ה זה`. That is a rendering problem, not a reason to reintroduce standalone article nodes.
- Russian and Finnish still show higher function-node ratios in rebuilt output. Current profile remains conservative there because many `DET`/`PRON` forms are semantically non-trivial, so this needs a second pass based on targeted examples rather than blind compression.
- Armenian remains broadly stable but still has many standalone copular forms such as `է`, `են`, `էր`.
- Japanese got much cleaner surfaces, but function-node ratio is still high because auxiliary and particle-heavy predicate chains remain structurally meaningful in UD and should not be crushed indiscriminately.

## Representative Observations

### English / German / French

- The biggest cleanup came from proper article-heavy profile activation on real treebank names.
- `aux:*` and subtype markers stopped leaking into standalone nodes as often.
- Marker-start ratio stayed roughly flat because many adposition-led node names are legitimate compact surfaces, not necessarily noise.

### Chinese

- `mark:rel` and related subtype cases were previously leaving nodes like `的`.
- CJK joining removed whitespace artifacts such as `周遭 的`.
- The rebuilt output now compresses function-only nodes more aggressively without inflating long surfaces.

### Hebrew

- The audit exposed mass standalone article noise (`ה`, `_של_`, `את`-style function-only nodes).
- Semitic determiner attachment removed most isolated article nodes.
- Remaining suspicious cases are mostly orthographic clitic rendering and duplicated preposition/article fragments inside already compact nodes.

### Japanese

- The main win is surface readability: many nodes no longer look like token dumps with spaces between every character-sized unit.
- High function-node ratio remains expected for some auxiliary chains; the first pass avoided destructive over-compression there.

## What Remains Debatable

- whether Slavic/Finnic determiners should be split into “semantic pronoun-like determiners” vs lighter attachable determiners
- whether Hebrew surfaces need a profile-aware clitic renderer, or whether that would introduce brittle pseudo-orthography
- whether some Japanese auxiliary chains should collapse further without damaging predicate structure

## Outcome

This pass was successful as an empirical stabilization step:

- the compact Stage 01 production contract stayed unchanged
- attachment/profile logic is now driven by measurable corpus behavior
- several real cross-language noise sources were reduced
- the remaining disputes are now explicit and reproducible via audit output instead of hidden in heuristics
