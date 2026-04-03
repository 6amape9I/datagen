# akin_core_datagen

Пайплайн подготовки датасета для семантической разметки синтаксических связей на базе корпусов в формате CoNLL-U.

Текущее целевое состояние:

- `tokens` — raw authoritative UD layer
- `units` — canonical normalized layer
- Stage 03 и Stage 04 работают по `units`
- `legacy_nodes` не нужен в normal path и включается только как compat export

## Поток данных

`01_preprocessor` -> `datasets/02_preprocessed` -> `03_gemini_fix_errors` -> `datasets/04_fixed` -> `04_postprocessor` -> `datasets/05_final`

`02_local_generation` остаётся вспомогательным локальным прогоном и сравнивает размер ответа с canonical `units`.

## Stage 01

Точка входа: [`01_preprocessor/main.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/01_preprocessor/main.py)

Stage 01 теперь:

- читает `.conllu` через `pyconll`
- сохраняет сырой слой `tokens`
- строит обратимые `units`
- добавляет `ud_semantic_hints`
- может добавлять `semantic_candidates_soft` как диагностический слой
- умеет отдельно включать compat export `legacy_nodes`

Схема v2: [`docs/preprocessed_schema_v2.md`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/docs/preprocessed_schema_v2.md)

### Export modes

Stage 01 управляется переменными окружения:

- `PREPROCESSOR_EXPORT_MODE=canonical` — только `tokens` и `units` (режим по умолчанию)
- `PREPROCESSOR_EXPORT_MODE=canonical+legacy` — дополнительно пишет `legacy_nodes`
- `ENABLE_SOFT_CANDIDATES=true` — включает `semantic_candidates_soft`
- `ENABLE_LEGACY_CANDIDATES=true` — добавляет candidates в `legacy_nodes`
- `ENABLE_LEGACY_CANDIDATE_FALLBACK=true` — включает fallback-all только для compat/debug сценариев

## Stage 03

Точки входа:

- [`03_gemini_fix_errors/pipeline.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/pipeline.py)
- [`03_gemini_fix_errors/scheduler.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/scheduler.py)

Stage 03:

- строит model input только из `units`
- валидирует ответ только по canonical units и общей онтологии ролей
- не использует `syntactic_link_candidates` как обязательный gatekeeper
- разрешает `ROOT` только для unit с `syntactic_link_target_id = null`

Model layer очищен по ответственности:

- transport вынесен в [`03_gemini_fix_errors/providers/`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/providers)
- request text собирается в [`prompt_builder.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/prompt_builder.py)
- response roles берутся из общей онтологии через [`response_schema.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/response_schema.py)
- имя модели берётся из `config.generate_conf.MODEL_NAME`, а не hardcoded в клиенте

## Stage 04

Точка входа: [`04_postprocessor/prepare_final_dataset.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/04_postprocessor/prepare_final_dataset.py)

Stage 04 собирает финальный датасет из canonical `units`:

- `id = unit_id`
- `name = surface`
- `pos_universal = upos`
- `case = features.get("Case")`
- `syntactic_link_target_id` из `units`
- `syntactic_link_name` из model output

## Конфигурация

Ключевые файлы:

- [`config/paths.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/paths.py)
- [`config/generate_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.py)
- [`config/pipeline_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/pipeline_conf.py)
- [`config/prompts.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/prompts.py)
- [`config/semantic.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/semantic.py)

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install pyconll google-genai tqdm requests pytest
```

## Команды

```bash
python 01_preprocessor/main.py
python 02_local_generation/pipeline.py
python 03_gemini_fix_errors/pipeline.py
python 03_gemini_fix_errors/scheduler.py
python 04_postprocessor/prepare_final_dataset.py
python utils/analyze_dataset.py
python -m pytest 01_preprocessor/tests -q
```

## Данные

Исходные корпуса ожидаются в:

```text
datasets/01_raw_corpus/
├── arm/
├── eng/
└── rus/
```

Split определяется по имени файла:

- `*train*.conllu` -> `train`
- `*dev*.conllu` или `*val*.conllu` -> `val`
- `*test*.conllu` -> `test`

## Логи

- `logs/processor_fallback.log` — fallback summary для compat/export режима
- `logs/local_generation_errors.log` — ошибки локальной генерации и node-count mismatch
- `logs/validator_errors.log` — ontology/id validation errors
- `logs/scheduler_summary.log` — сводка шедулера

## Ограничения и заметки

- каталог `03_gemini_fix_errors` пока сохраняет историческое имя, но его внутренний model layer уже разбит на нейтральные provider/prompt/schema компоненты
- `legacy_nodes` остаётся только для explicit compat export, а не как обязательный слой
- `semantic_candidates_soft` и fallback-all не участвуют в корректности downstream pipeline
- для реальной эксплуатации API keys лучше держать в переменных окружения, а не в [`config/generate_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.py)
