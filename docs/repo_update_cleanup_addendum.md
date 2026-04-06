# Addendum — execution rules for Codex on this cleanup pass

## General stance

This pass is a **cleanup and consolidation pass**, not a compatibility-preservation pass.

Be decisive.
Prefer deletion over layering more wrappers.

---

## 1. Do not preserve dead transitions

If a module exists only to redirect to the new place, delete it.
Do not keep “deprecated” wrappers in runtime code.

A clean repository is more valuable here than backwards-compatible clutter.

---

## 2. Integrate AI Studio code surgically

The provided AI Studio code is the basis for the Google provider implementation, not for the entire repository.

Do:
- adapt its request/config pattern into `03_generation/providers/google_genai.py`

Do not:
- paste the entire constructor script into the repo unchanged
- move orchestration into provider code
- bypass the project prompt builder / validator / pipeline

---

## 3. Do not keep ontology helper artifacts

Files like:
- `semantic_roles_compact.py`
- generated compact ontology text builders
- extra prompt-context summary helpers

should be removed if they create a second source of truth.

There must be one canonical prompt source.

---

## 4. Prefer one source of truth per concern

- labels: one source
- schema: one source
- prompt text: one source
- provider implementation: one source
- runtime config: one source

If two files describe the same thing differently, delete one of them.

---

## 5. Be honest about tools

If Google Search tool from AI Studio is not useful for this task, do not keep it enabled “just in case”.
Make it off by default or remove it.

If streaming adds no value, do not keep it just because the constructor used it.

---

## 6. Keep code readable

Avoid:
- extra indirection
- path hacks unless unavoidable
- compatibility glue
- duplicated enums or ontology descriptions
- wrapper modules that only exist to preserve old names

---

## 7. Preserve only stable abstractions

Keep:
- provider protocol / contract
- prompt package
- input builder
- validator
- pipeline orchestration

These are good abstractions.
The transitional compatibility layer is not.

---

## 8. Update docs last, but do update them

After code cleanup:
- update README
- remove references to deleted paths
- document the single canonical execution paths

---

## 9. Success criterion

Success is not “nothing broke”.
Success is:
- the repo is visibly cleaner,
- the execution model is simpler,
- the Google provider is aligned with AI Studio,
- and no duplicated ontology machinery remains.
