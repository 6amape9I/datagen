# akin_core_datagen

Пайплайн подготовки датасета для семантической разметки синтаксических связей на основе корпусов в формате CoNLL-U. Основные этапы: Stage 01 подготавливает versioned preprocessed JSON, Stage 03 получает `syntactic_link_name` от модели, Stage 04 собирает финальный `input/output`-датасет.

## Поток данных

`01_preprocessor` -> `datasets/02_preprocessed` -> `03_gemini_fix_errors` -> `datasets/04_fixed` -> `04_postprocessor` -> `datasets/05_final`

`02_local_generation` существует отдельно и пишет в `datasets/03_local_generated`, но не является обязательным звеном для сборки финального датасета.

## Структура репозитория

```text
.
├── 01_preprocessor/          # UD reader, token normalizer, unit builder, legacy export
├── 02_local_generation/      # Локальный inference по preprocessed JSON
├── 03_gemini_fix_errors/     # Подготовка model input и разметка через Gemini / local service
├── 04_postprocessor/         # Сборка финального training dataset
├── config/                   # Пути, промпты, модели, лимиты, semantic mappings
├── datasets/
│   ├── 01_raw_corpus/
│   ├── 02_preprocessed/
│   ├── 03_local_generated/
│   ├── 04_fixed/
│   └── 05_final/
├── docs/
├── logs/
└── utils/
```

## Stage 01

Точка входа: [`01_preprocessor/main.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/01_preprocessor/main.py)

Stage 01 больше не пытается быть источником истины для `syntactic_link_name`. Теперь он:

- читает `.conllu` через `pyconll`;
- сохраняет сырой слой `tokens` почти без потерь;
- строит нормализованный слой `units` с обратимыми attachment'ами вместо разрушительных merge;
- добавляет `ud_semantic_hints`;
- добавляет необязательные `semantic_candidates_soft`;
- экспортирует `legacy_nodes` для совместимости с текущими Stage 03/04.

Правила авторитетности:

- `tokens` — authoritative raw layer;
- `units` — authoritative normalized layer;
- `legacy_nodes` — transitional compatibility layer.

Подробная схема: [`docs/preprocessed_schema_v2.md`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/docs/preprocessed_schema_v2.md)

Пример v2-записи:

```json
{
  "preprocessed_schema_version": 2,
  "sentence_id": "eng_en_gum-ud-train.conllu_1",
  "text": "The city in France",
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
      "head_token_id": "2",
      "deprel": "det"
    }
  ],
  "units": [
    {
      "unit_id": "w2",
      "head_token_id": "2",
      "span_token_ids": ["1", "2"],
      "surface": "The city",
      "core_lemma": "city",
      "upos": "NOUN",
      "xpos": "NN",
      "features": {"Number": "Sing"},
      "syntactic_link_target_id": null,
      "original_deprel": "root",
      "attached_tokens": [],
      "introduced_by": [],
      "function_parts": [],
      "ud_semantic_hints": ["determiner_attached", "nominal_head", "root_nominal", "root_unit"],
      "semantic_candidates_soft": ["ROOT"]
    }
  ],
  "legacy_nodes": [
    {
      "id": "w2",
      "name": "city",
      "lemma": "city",
      "pos_universal": "NOUN",
      "pos_specific": "NN",
      "features": {"Number": "Sing"},
      "syntactic_link_candidates": ["ROOT"],
      "syntactic_link_target_id": null,
      "original_deprel": "root"
    }
  ]
}
```

## Downstream stages

### `02_local_generation`

Точка входа: [`02_local_generation/pipeline.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/02_local_generation/pipeline.py)

- читает `datasets/02_preprocessed/*.json`;
- отправляет только `text` в локальный inference-сервис;
- сравнивает размер ответа с ожидаемым числом `legacy_nodes`;
- пишет JSONL в `datasets/03_local_generated`.

### `03_gemini_fix_errors`

Точки входа:

- [`03_gemini_fix_errors/pipeline.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/pipeline.py)
- [`03_gemini_fix_errors/scheduler.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/scheduler.py)

Stage 03 теперь предпочитает `units` для model input. В payload можно передавать:

- `surface`
- `core_lemma`
- `upos` / `xpos`
- `features`
- `syntactic_link_target_id`
- `original_deprel`
- `introduced_by`
- `attached_tokens`
- `ud_semantic_hints`
- `head_surface` / `head_lemma`

Валидация остаётся на compatibility-слое и сравнивает ответ с `legacy_nodes[*].id` и `legacy_nodes[*].syntactic_link_candidates`.

### `04_postprocessor`

Точка входа: [`04_postprocessor/prepare_final_dataset.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/04_postprocessor/prepare_final_dataset.py)

Stage 04 читает `legacy_nodes` из preprocessed JSON, сопоставляет их с `datasets/04_fixed/*.jsonl` и формирует финальный датасет в `datasets/05_final`.

## Конфигурация

Ключевые файлы:

- [`config/paths.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/paths.py) — все пути к данным и логам
- [`config/generate_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.py) — модель, URL локальных сервисов, строки с ключами
- [`config/pipeline_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/pipeline_conf.py) — стратегия запросов, воркеры, retry, лимиты шедулера
- [`config/prompts.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/prompts.py) — системные и пользовательские промпты
- [`config/semantic.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/semantic.py) — legacy heuristic candidate logic и карта semantic relations

Поддерживаемые переменные окружения:

- `GEMINI_API_KEYS="key1,key2"`
- `GEMINI_REQUEST_STRATEGY=genai|local`
- `SCHEDULER_WORKERS=4`
- `SCHEDULER_ERROR_LIMIT=10`
- `SCHEDULER_DAILY_QUOTA=250`

Локальные endpoint'ы по умолчанию:

- `LOCAL_INFER_URL = http://127.0.0.1:8000/infer`
- `LOCAL_API_URL = http://127.0.0.1:8080/generate`

## Установка

Требования:

- Python 3.12+
- `pyconll`
- `google-genai`
- `tqdm`
- `requests`
- `pytest`

Быстрый старт:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pyconll google-genai tqdm requests pytest
```

## Команды

Запускать из корня репозитория.

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

Ожидаемая структура исходных корпусов:

```text
datasets/01_raw_corpus/
├── arm/
├── eng/
└── rus/
```

Язык определяется по имени подпапки, а split по имени файла:

- `*train*.conllu` -> `train`
- `*dev*.conllu` или `*val*.conllu` -> `val`
- `*test*.conllu` -> `test`

## Логи

- `logs/processor_fallback.log` — fallback-all для `legacy_nodes[*].syntactic_link_candidates`
- `logs/local_generation_errors.log` — ошибки локальной генерации и mismatch числа узлов
- `logs/validator_errors.log` — ошибки выбора связи вне списка кандидатов
- `logs/scheduler_summary.log` — итоговые отчёты шедулера

## Ограничения и особенности

- `legacy_nodes` остаётся переходным слоем совместимости; canonical слой Stage 01 — это `units`
- `03_gemini_fix_errors` всё ещё не использует `datasets/03_local_generated`
- `validator.py` логирует ошибку выбора связи вне кандидатов, но фактически не отклоняет такой ответ, потому что `return False` в этой ветке закомментирован
- `04_postprocessor` собирает итог только по тем записям, которые есть и в `02_preprocessed`, и в `04_fixed`
- ключи лучше держать в переменных окружения, а не в [`config/generate_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.py)
