# 03_generation

Canonical generation layer for node-level semantic labeling.

## Entry points

```bash
python 03_generation/local_gen.py
python 03_generation/google_gen.py
python 03_generation/scheduler.py
```

## Responsibilities

- read compact Stage 01 records from `datasets/02_preprocessed`
- build compact model payloads from `text + nodes[]`
- assemble prompts from one canonical system prompt asset
- request generation from either the local HTTP provider or Google GenAI
- validate minimal `id + syntactic_link_name` output
- write validated records to `datasets/04_fixed/*.jsonl`
- enqueue at most `MAX_SAMP_PER_JSON` eligible records from each input `.json`

## Prompt source

The canonical system prompt lives in:

- [`prompt_assets/node_level_system_prompt.md`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/prompt_assets/node_level_system_prompt.md)

There is no runtime ontology helper artifact or secondary prompt-context builder.

## Google provider

[`providers/google_genai.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/providers/google_genai.py) follows the Google AI Studio request pattern:

- `genai.Client(api_key=...)`
- `types.GenerateContentConfig(...)`
- structured JSON schema
- optional Google Search tool, disabled by default
- thinking level config via `GOOGLE_THINKING_LEVEL`
