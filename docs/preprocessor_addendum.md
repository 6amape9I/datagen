# Addendum for the Codex execution agent

This addendum defines how to behave while implementing the preprocessor rebuild.

## 1. Prioritize architecture over cosmetic cleanup

Do not spend the branch budget on:

- style-only rewrites
- renaming for aesthetics without structural gain
- formatting churn across unrelated files
- “cleanup” that makes diffs larger but design no clearer

Make each change serve the Stage 01 redesign.

---

## 2. Do not silently break downstream stages

You may change contracts, but only if you also add an explicit migration path.

Whenever you change the output shape of preprocessing:

- either adapt Stage 03 in the same branch
- or add a compatibility exporter / adapter
- or do both

Never leave the repository in a state where preprocessing is “more correct” but the pipeline is unusable.

---

## 3. Prefer additive migration to destructive replacement

During this task, prefer:

- adding `units`
- adding `tokens`
- adding schema versioning
- adding a compatibility export

instead of deleting old behavior immediately.

The goal is a controlled transition, not a dramatic rewrite that strands the rest of the code.

---

## 4. Be explicit about what is authoritative

After the rebuild:

- `tokens` should be the authoritative raw layer
- `units` should be the authoritative normalized layer
- `legacy_nodes` should be transitional only

Reflect this clearly in names, docs, and comments.

Do not create ambiguous parallel fields that appear equally official.

---

## 5. Avoid re-embedding domain assumptions into hidden heuristics

The project’s semantic ontology is valuable, but this task is not about forcing that ontology back into Stage 01 through a new maze of heuristics.

When in doubt:

- preserve UD evidence
- emit a soft hint
- leave final semantic choice to the model layer

Do not compensate for uncertainty by expanding hardcoded role rules.

---

## 6. Do not make the design Russian-centric again

While implementing attachment or normalization behavior, constantly test your assumptions against typologically different languages.

Specifically challenge assumptions involving:

- determiners / articles
- adpositions vs postpositions
- particles
- auxiliaries
- lack of overt case morphology
- rich case morphology
- head direction differences
- fixed multiword expressions

If a rule only “feels right” for Russian, do not make it global by default.

---

## 7. Centralize policy, do not scatter it

Any merge / attachment / normalization policy must live in a dedicated policy layer.

Do not hide behavior in:

- random conditionals inside `main.py`
- exporter-only hacks
- duplicated logic across builder and adapter modules
- tiny special cases with no shared explanation

The rebuild succeeds only if another contributor can find and understand the policy in one obvious place.

---

## 8. Preserve debuggability even if output becomes larger

Bigger but traceable output is acceptable.
Opaque but compact output is not.

If you must choose between:

- smaller JSON
- clearer provenance of units and attachments

choose provenance.

---

## 9. Keep tests close to real failure modes

Do not write placeholder tests that only confirm files exist.

Tests should target actual risks, such as:

- lost function tokens
- incorrect root handling
- non-reversible merges
- article / determiner attachment behavior
- marker introduction tracking
- clause introducer handling
- broken compatibility export
- multilingual structure regressions

---

## 10. Prefer small, reviewable steps inside one coherent branch

Even if the final branch is substantial, organize the work internally as sequential steps:

1. schemas
2. reader separation
3. unit builder
4. attachment policy
5. hints
6. compatibility export
7. Stage 03 adapter
8. tests
9. docs

This reduces the chance of tangled half-migrations.

---

## 11. When uncertain, preserve information rather than collapsing it

If the correct attachment behavior is unclear for a pattern:

- keep the raw token visible
- attach conservatively
- annotate metadata
- avoid irreversible collapsing

The model can work with preserved structure.
It cannot recover information that preprocessing deleted.

---

## 12. Minimize hidden behavior changes

If an old field changes meaning, do at least one of the following:

- rename it
- version it
- document it loudly

Do not keep the same field name while silently changing what it means.

---

## 13. Update documentation as part of the implementation, not afterthought

README and code-level docs are part of the task.

A contributor should be able to answer these questions after reading the docs:

- What is Stage 01 now responsible for?
- What is a token?
- What is a unit?
- What is attached vs preserved?
- Are candidates hard or soft?
- Which layer is used by Stage 03?
- How does backward compatibility work?

If the branch cannot answer those questions, it is not done.

---

## 14. Avoid accidental scope creep

Do not turn this task into:

- a full repository modernization
- a global package architecture rewrite
- a prompt redesign campaign
- a semantic ontology rewrite
- a production infra overhaul

Touch other parts of the repository only where required to make the Stage 01 rebuild real and safe.

---

## 15. Final working attitude

Act like an implementation architect, not a blind code generator.

That means:

- understand the old contract before changing it
- preserve valuable behavior where justified
- remove conceptual mistakes, not just symptoms
- leave the repository in a state that a human can continue from

The correct outcome is not merely “tests pass”.
The correct outcome is:

- Stage 01 has a clearer purpose
- multilingual preprocessing is more believable
- model-facing structure is richer
- downstream stages still function
- future contributors can iterate without fighting the old lava layer
