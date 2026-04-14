# akin_core_datagen

Пайплайн подготовки датасета для семантической разметки синтаксических связей на базе UD/CoNLL-U.

## Поток данных

`01_preprocessor` -> `datasets/02_preprocessed` -> `03_generation` -> `datasets/04_fixed` -> `04_postprocessor` -> `datasets/05_final`

Канонический контракт Stage 01 теперь один: компактный JSON с `sentence_id`, `text`, `language_code`, `split`, `source_file` и `nodes[]`.

Схема: [`docs/preprocessed_schema_v2.md`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/docs/preprocessed_schema_v2.md)

## Stage 01

Точка входа: [`01_preprocessor/main.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/01_preprocessor/main.py)

Stage 01:

- читает `.conllu` через `pyconll`
- нормализует UD-токены только как internal builder step
- строит компактные semantic nodes
- пишет только production `nodes[]`, без `tokens`, `units`, `legacy_nodes` и candidate lists
- поддерживает reproducible audit через [`01_preprocessor/audit_preprocessed.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/01_preprocessor/audit_preprocessed.py)

First-pass empirical report: [`docs/stage01_first_pass_audit.md`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/docs/stage01_first_pass_audit.md)

## Stage 03

Точки входа:

- [`03_generation/local_gen.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/local_gen.py)
- [`03_generation/google_gen.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/google_gen.py)
- [`03_generation/scheduler.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/scheduler.py)
- [`03_generation/README.md`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/README.md)

Stage 03:

- использует один общий generation pipeline для local и Google providers
- строит model input напрямую из compact `nodes`
- валидирует только structural integrity и ontology membership
- разрешает `ROOT` только для узлов без `syntactic_link_target_id`
- пишет ответы в `datasets/04_fixed/*.jsonl`

Model layer разделён по ответственности:

- orchestration: [`03_generation/pipeline.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/pipeline.py)
- input builder: [`03_generation/input_builder.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/input_builder.py)
- prompt assembly: [`03_generation/prompt_builder.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/prompt_builder.py)
- schema/ontology: [`03_generation/response_schema.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/response_schema.py)
- transport: [`03_generation/providers/`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_generation/providers)

## Stage 04

Точка входа: [`04_postprocessor/prepare_final_dataset.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/04_postprocessor/prepare_final_dataset.py)

Stage 04 объединяет compact Stage 01 nodes и Stage 03 labels по `id` и пишет финальные `input/output` записи.

## Конфигурация

Ключевые файлы:

- [`config/paths.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/paths.py)
- [`config/runtime.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/runtime.py)
- [`config/defaults.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/defaults.py)
- [`config/generate_conf.example.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.example.py)
- [`config/pipeline_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/pipeline_conf.py)
- [`config/semantic.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/semantic.py)

`config/paths.py` больше не создаёт директории при импорте. Runtime-директории создаются только entrypoint’ами.

Runtime-config приоритет:

- environment variables
- локальный приватный `config/generate_conf.py`, если он существует
- публичные defaults из `config/defaults.py`

Поддерживаемые env overrides:

- `GOOGLE_MODEL_NAME`
- `GOOGLE_API_KEYS`
- `GOOGLE_SCHEDULER_KEYS`
- `GOOGLE_THINKING_LEVEL`
- `GOOGLE_ENABLE_SEARCH_TOOL`
- `LOCAL_MODEL_NAME`
- `GENERATION_MAX_OUTPUT_TOKENS`
- `MAX_SAMP_PER_JSON`
- `GENERATION_TEMPERATURE`
- `GENERATION_PROFILE`
- `LOCAL_API_URL`

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install pyconll google-genai tqdm requests pytest
```

## Команды

```bash
python 01_preprocessor/main.py
python 01_preprocessor/audit_preprocessed.py --mode rebuild --sentence-limit 200
python 03_generation/local_gen.py
python 03_generation/google_gen.py
python 03_generation/scheduler.py
python 04_postprocessor/prepare_final_dataset.py
python utils/analyze_dataset.py
python -m pytest 01_preprocessor/tests -q
```

## Данные и логи

- raw corpora: `datasets/01_raw_corpus`
- preprocessed compact records: `datasets/02_preprocessed`
- generation outputs: `datasets/04_fixed`
- final dataset: `datasets/05_final`

Логи:

- `logs/processor.log`
- `logs/scheduler_summary.log`

## Замечания

- split определяется по имени файла: `train`, `dev|val`, `test`
- compact Stage 01 output intentionally не хранит raw-token trace и builder internals
- проект корректно импортируется и без `config/generate_conf.py`
- для реальной эксплуатации API keys лучше держать в переменных окружения, а `config/generate_conf.py` использовать только как локальный override
