# akin_core_datagen

Пайплайн подготовки датасета для семантической разметки синтаксических связей на базе UD/CoNLL-U.

## Поток данных

`01_preprocessor` -> `datasets/02_preprocessed` -> `02_local_generation` или `03_annotation` -> `datasets/04_fixed` -> `04_postprocessor` -> `datasets/05_final`

Канонический контракт Stage 01 теперь один: компактный JSON с `sentence_id`, `text`, `language_code`, `split`, `source_file` и `nodes[]`.

Схема: [`docs/preprocessed_schema_v2.md`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/docs/preprocessed_schema_v2.md)

## Stage 01

Точка входа: [`01_preprocessor/main.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/01_preprocessor/main.py)

Stage 01:

- читает `.conllu` через `pyconll`
- нормализует UD-токены только как internal builder step
- строит компактные semantic nodes
- пишет только production `nodes[]`, без `tokens`, `units`, `legacy_nodes` и candidate lists

## Stage 02

Точка входа: [`02_local_generation/pipeline.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/02_local_generation/pipeline.py)

Stage 02 читает те же compact preprocessed records и проверяет размер ответа локальной модели по `nodes`.

## Stage 03

Точки входа:

- [`03_annotation/pipeline.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_annotation/pipeline.py)
- [`03_annotation/scheduler.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_annotation/scheduler.py)

Stage 03:

- строит model input напрямую из compact `nodes`
- валидирует только structural integrity и ontology membership
- разрешает `ROOT` только для узлов без `syntactic_link_target_id`
- пишет ответы в `datasets/04_fixed/*.jsonl`

Model layer разделён по ответственности:

- transport: [`03_annotation/providers/`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_annotation/providers)
- prompt assembly: [`03_annotation/prompt_builder.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_annotation/prompt_builder.py)
- schema/ontology: [`03_annotation/response_schema.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_annotation/response_schema.py)

## Stage 04

Точка входа: [`04_postprocessor/prepare_final_dataset.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/04_postprocessor/prepare_final_dataset.py)

Stage 04 объединяет compact Stage 01 nodes и Stage 03 labels по `id` и пишет финальные `input/output` записи.

## Конфигурация

Ключевые файлы:

- [`config/paths.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/paths.py)
- [`config/generate_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.py)
- [`config/pipeline_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/pipeline_conf.py)
- [`config/prompts.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/prompts.py)
- [`config/semantic.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/semantic.py)

`config/paths.py` больше не создаёт директории при импорте. Runtime-директории создаются только entrypoint’ами.

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
python 03_annotation/pipeline.py
python 03_annotation/scheduler.py
python 04_postprocessor/prepare_final_dataset.py
python utils/analyze_dataset.py
python -m pytest 01_preprocessor/tests -q
```

## Данные и логи

- raw corpora: `datasets/01_raw_corpus`
- preprocessed compact records: `datasets/02_preprocessed`
- local generation outputs: `datasets/03_local_generated`
- validated annotations: `datasets/04_fixed`
- final dataset: `datasets/05_final`

Логи:

- `logs/processor.log`
- `logs/local_generation_errors.log`
- `logs/validator_errors.log`
- `logs/scheduler_summary.log`

## Замечания

- split определяется по имени файла: `train`, `dev|val`, `test`
- compact Stage 01 output intentionally не хранит raw-token trace и builder internals
- для реальной эксплуатации API keys лучше держать в переменных окружения, а не в [`config/generate_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.py)
