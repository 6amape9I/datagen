# Repository Update Plan — generation cleanup + AI Studio integration

## Goal

Bring the repository to a cleaner, more final state after the `03_generation` refactor by doing three things:

1. remove deprecated compatibility layers and dead transitional code;
2. adapt the Google AI Studio constructor code into the real project architecture;
3. remove runtime ontology artifacts such as `semantic_roles_compact.py` and similar duplicated prompt-context files, replacing them with a single canonical prompt source.

This is **not** a migration plan. Treat the current refactor as already accepted and now perform the cleanup / consolidation pass.

---

## High-level architectural target

After this task, the repository should have:

- one canonical generation layer: `03_generation/`
- one canonical Google provider implementation based on the AI Studio constructor code
- one canonical local provider implementation
- one canonical prompt source for node-level semantic labeling
- no deprecated wrappers in `02_local_generation/` or `03_annotation/`
- no duplicated ontology summary files in runtime code
- no legacy redirect modules pretending to preserve older entrypoints

The resulting project should feel like a clean, intentional repository, not a transition state.

---

## Phase 1 — Delete deprecated and transitional elements

### 1.1 Remove deprecated wrappers completely

Delete transitional wrappers that only redirect to the new generation layer.

Target removals:

- `02_local_generation/`
- `03_annotation/` runtime modules that only redirect or re-export the new layer

At minimum remove:

- `02_local_generation/pipeline.py`
- `03_annotation/pipeline.py`
- `03_annotation/scheduler.py`
- any redirect-only provider shims or wrapper modules in `03_annotation/`
- redirect-only clients / prompt builders / validators that exist only for compatibility

### 1.2 Decide whether to delete the whole `03_annotation/` directory

Preferred outcome:
- remove `03_annotation/` entirely if it no longer contains unique logic.

If some file there still contains useful documentation, move the content to:
- `03_generation/README.md`
- or top-level `README.md`
- or `docs/`

Do **not** keep dead historical module trees in the codebase just because they once existed.

### 1.3 Remove obsolete docs and references

Delete or replace documents that describe the pre-cleanup transition state if they are now misleading.

Review and prune:
- outdated stage notes that still speak in terms of wrappers / redirects
- docs that describe temporary compatibility behavior
- references in README to deprecated entrypoints

### 1.4 Rename outdated tests if necessary

If test names still refer to old stage names (`stage02`, `stage03_adapter`, etc.) but now test the canonical `03_generation` layer, rename them for clarity.

Do not break coverage, but remove naming confusion.

---

## Phase 2 — Canonicalize the generation layer

The repository already has `03_generation/` as the new center. Now make it the only one.

### 2.1 Preserve these core responsibilities in `03_generation/`

Keep and clean up:

- `pipeline.py` — orchestration
- `input_builder.py` — compact model payload builder
- `prompt_builder.py` — prompt assembly
- `response_schema.py` — schema and allowed labels
- `validator.py` — structural response validation
- `providers/google_genai.py`
- `providers/local_http.py`
- `google_gen.py`
- `local_gen.py`
- `scheduler.py` only if it is still truly needed

### 2.2 Remove sys.path hacks where possible

A lot of modules currently inject project paths into `sys.path`.

Refactor toward package-style imports where feasible.
Preferred direction:
- run modules via `python -m`
- use stable package imports
- reduce path injection in entrypoints and providers

This does not need a full packaging revolution, but obvious `sys.path` surgery should be reduced.

---

## Phase 3 — Integrate Google AI Studio constructor code properly

The user supplied Google AI Studio constructor code should become the baseline for the Google provider.

### 3.1 Treat the AI Studio code as the authoritative transport pattern
The provided constructor located in 03_generation/providers/generation_example.py
The provided constructor code uses:
- `genai.Client(api_key=...)`
- `client.models.generate_content_stream(...)`
- `types.GenerateContentConfig(...)`
- explicit `response_mime_type="application/json"`
- explicit structured schema with `nodes -> [{id, syntactic_link_name}]`
- `thinking_config=types.ThinkingConfig(thinking_level="HIGH")`
- `max_output_tokens=32760`
- optional `tools=[types.Tool(googleSearch=...)]`
- a large `system_instruction`
- the actual user payload inserted as text input

The project should adopt this **provider-side pattern** rather than keep a home-grown variation.

### 3.2 Important constraint: do NOT rewrite the whole project around the constructor snippet

Only adapt the constructor code into:
- `03_generation/providers/google_genai.py`

Do **not** move orchestration into the provider.
Do **not** inline project business logic into the constructor code.
Do **not** destroy the current `PromptPackage` / validator / pipeline separation.

Correct layering:

- `input_builder.py` builds model payload
- `prompt_builder.py` builds `PromptPackage`
- `response_schema.py` builds schema
- `providers/google_genai.py` performs the actual Google request using the AI Studio style
- `pipeline.py` handles retries / writing / orchestration
- `validator.py` validates returned ids + labels

### 3.3 Required provider behavior

Refactor `03_generation/providers/google_genai.py` so that it:

1. uses the AI Studio constructor approach as the core implementation;
2. takes `PromptPackage.system_prompt` and `PromptPackage.user_prompt` from the project instead of hardcoding huge strings inside the provider;
3. uses the project `response_schema.py` as the single schema source;
4. returns a `GenerationResult(payload, error)` compatible with the existing pipeline contract;
5. supports project runtime settings for:
   - model name
   - max output tokens
   - temperature
   - thinking mode / thinking level
   - optional tool enablement
6. cleanly handles JSON decode failures and provider errors.

### 3.4 Decide what to do about `generate_content_stream`

Prefer one of these two options:

#### Preferred
Use non-streaming request mode if it integrates more cleanly with the existing pipeline and still matches the constructor semantics.

#### Acceptable
Use `generate_content_stream` only if you collect the stream into final text cleanly and it genuinely benefits this project.

Important:
The pipeline currently expects a final parsed JSON payload.
Do not complicate orchestration with token-by-token streaming if it adds no value.

### 3.5 Google Search tool decision

The AI Studio constructor code includes `googleSearch`.

For this repository, default behavior should be:

- `googleSearch` **disabled by default**

Reason:
This task is structured semantic labeling of already-prepared sentence nodes, not open-web research.
External search will add cost, latency, unpredictability, and can hurt reproducibility.

If you want to preserve the capability, make it:
- optional
- explicitly controlled by runtime config
- off by default

### 3.6 Thinking mode adaptation

The constructor code uses `thinking_level="HIGH"`.

The project currently has numeric `THINKING_BUDGET`.

You must choose one canonical configuration style for Google generation.

Preferred direction:
- adapt runtime config to the constructor model semantics:
  - e.g. `GOOGLE_THINKING_LEVEL = HIGH | MEDIUM | LOW | OFF`
- remove or deprecate numeric `THINKING_BUDGET` for Google if it does not match the AI Studio model interface well.

If the SDK still supports numeric budgets in some modes, document the mapping clearly.
But avoid ambiguous dual semantics in runtime config.

### 3.7 Model default update

The constructor code uses `gemma-4-31b-it`.

Decide one canonical project default for Google generation and set it intentionally in runtime defaults / example config.
Do not leave a stale default just because it was there historically.

---

## Phase 4 — Remove ontology artifacts from runtime code

### 4.1 Delete `semantic_roles_compact.py` and similar artifacts

The user does **not** want ontology fragments or hand-maintained prompt-context artifacts drifting around the codebase during a full rebuild.

Delete:

- `03_generation/context/semantic_roles_compact.py`
- other similar runtime ontology helper files if they only duplicate prompt definitions

### 4.2 Remove ontology text generation from `response_schema.py`

`response_schema.py` should do one thing well:
- define the allowed label set
- build structured schemas for providers

It should **not** also be responsible for assembling prompt ontology text.

So:
- remove `build_runtime_ontology_context()` from `response_schema.py`
- remove imports that couple schema code to prompt-context code

### 4.3 Replace artifact-based ontology context with one canonical prompt source

Use exactly one canonical source for the node-level prompt text.

Preferred options:

#### Option A (recommended)
A dedicated source file such as:
- `03_generation/prompt_assets/node_level_system_prompt.txt`
or
- `03_generation/prompt_assets/node_level_system_prompt.md`

and then:
- `prompt_builder.py` loads this text
- runtime prompt assembly stays simple

#### Option B
A dedicated Python module containing only the canonical prompt strings/templates:
- `03_generation/prompt_source.py`

In either case:
- one source of truth
- no compact ontology artifact
- no extra runtime summary builders
- no duplicated mini-ontologies in multiple modules

### 4.4 Keep only one label source

The actual list of allowed labels should remain canonical in one place.
If `config/translate.py` already serves that role, keep it there.

Do not create a second hand-maintained label list inside prompt artifacts.

The prompt source may reference the canonical list or include a curated textual explanation, but labels themselves must not drift.

---

## Phase 5 — Prompt layer cleanup

### 5.1 Make `prompt_builder.py` simple and explicit

After cleanup, `prompt_builder.py` should:
- load / assemble the canonical system prompt
- inject the compact JSON payload into the user prompt
- return `PromptPackage`

It should not:
- synthesize ontology summaries from helper artifacts
- create its own secondary ontology representation
- hide prompt source behind multiple indirections

### 5.2 Support full vs compact prompt profiles only if truly needed

If the project needs:
- a fuller prompt for high-quality Google runs
- a more compact one for cheaper runs

then define them explicitly as named profiles in the canonical prompt source.

Do not keep half-generated ontology helper files for this.

---

## Phase 6 — Runtime config cleanup

### 6.1 Revisit generation runtime fields

After AI Studio integration, runtime config should clearly support the generation layer.

Target config fields:
- model name
- API key(s)
- local API URL
- local infer URL
- max output tokens
- temperature
- generation profile
- Google thinking mode / level
- optional Google Search tool enablement

### 6.2 Remove misleading or obsolete settings

If some existing fields no longer fit the new provider contract, remove them instead of carrying confusing compatibility baggage.

Examples:
- numeric thinking budget if replaced by thinking level
- duplicated strategy fields if no longer needed
- settings that existed only because of the old split between stage 02 and stage 03

### 6.3 Update example config

Update:
- `config/defaults.py`
- `config/generate_conf.example.py`
- README config docs

so that the repository reflects the new canonical generation layer and AI Studio-aligned Google provider.

---

## Phase 7 — Validation and acceptance checks

### 7.1 Static checks
Run:
- `python -m py_compile ...`
- relevant tests

### 7.2 Update tests
Adjust tests so they reflect the canonical new structure:
- generation input builder
- response schema
- validator
- runtime config
- provider contract shape

### 7.3 Do not fake runtime validation
It is acceptable if live Google requests are not executed during implementation.
But the code must be import-clean and contract-clean.

---

## Required end state

After this task:

1. `03_generation/` is the only generation layer.
2. `02_local_generation/` and `03_annotation/` no longer carry runtime logic or wrappers.
3. `03_generation/providers/google_genai.py` is adapted from the AI Studio constructor style.
4. Google Search tool is disabled by default or removed.
5. Runtime config cleanly supports the new provider contract.
6. `semantic_roles_compact.py` and similar prompt-context artifacts are removed.
7. The prompt layer has one canonical source of truth.
8. The repository no longer looks transitional.

---

## Concrete deletion list

Unless a file still contains unique, active logic, delete:

- `02_local_generation/`
- `03_annotation/`
- `03_generation/context/semantic_roles_compact.py`
- helper files whose only role is backward compatibility
- prompt-related files that duplicate ontology summaries in runtime code

---

## Definition of Done

The task is done when all of the following are true:

- there are no deprecated wrapper entrypoints left in runtime code;
- there is only one canonical generation layer;
- the Google provider follows the AI Studio transport pattern while still fitting the project architecture;
- there is no hand-maintained compact ontology artifact inside runtime code;
- prompts come from a single canonical source;
- config reflects the new provider contract clearly;
- tests / import checks pass;
- README no longer mentions deprecated execution paths.
