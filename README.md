# akin_core_datagen

Пайплайн подготовки датасета для семантической разметки синтаксических связей на основе корпусов в формате CoNLL-U. Проект разбит на несколько этапов: предобработка UD-корпусов, локальная генерация черновых ответов, исправление разметки через Gemini или локальный сервис и сборка финального датасета для обучения.

## Что делает проект

На вход проект принимает `.conllu`-корпуса, автоматически раскладывает их по языкам и сплитам, преобразует предложения в промежуточный JSON-формат с кандидатами семантических связей, затем получает итоговые `syntactic_link_name` от модели и формирует финальный датасет вида `input/output`.

Текущий поток данных в коде такой:

`01_preprocessor` -> `datasets/02_preprocessed` -> `03_gemini_fix_errors` -> `datasets/04_fixed` -> `04_postprocessor` -> `datasets/05_final`

Отдельно существует `02_local_generation`, который пишет результаты в `datasets/03_local_generated`, но на текущий момент `03_gemini_fix_errors` не использует этот выход и строит очередь задач напрямую из `datasets/02_preprocessed`.

## Структура репозитория

```text
.
├── 01_preprocessor/          # Парсинг .conllu и генерация промежуточного JSON
├── 02_local_generation/      # Локальный inference по preprocessed JSON
├── 03_gemini_fix_errors/     # Валидация и разметка через Gemini / локальный сервис
├── 04_postprocessor/         # Сборка финального training dataset
├── config/                   # Пути, промпты, модели, лимиты, семантические правила
├── datasets/
│   ├── 01_raw_corpus/        # Исходные корпуса по языкам
│   ├── 02_preprocessed/      # JSON после preprocessor
│   ├── 03_local_generated/   # JSONL после local generation
│   ├── 04_fixed/             # JSONL после Gemini/local correction
│   └── 05_final/             # Финальный JSON для обучения
├── logs/                     # Логи fallback, validator, scheduler, local generation
└── utils/                    # Утилиты анализа и сохранения данных
```

## Основные этапы

### 1. `01_preprocessor`

Точка входа: [`01_preprocessor/main.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/01_preprocessor/main.py)

Что делает:

- ищет языковые подпапки в `datasets/01_raw_corpus`;
- определяет `train` / `val` / `test` по имени `.conllu`-файла;
- читает корпус через `pyconll`;
- удаляет пунктуацию и технические токены;
- объединяет маркеры и служебные цепочки (`case`, `cc`, `mark`, `fixed`, `flat`, `compound` и др.);
- строит список кандидатов `syntactic_link_candidates` по эвристикам из [`config/semantic.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/semantic.py);
- пишет один JSON-файл на каждый язык и сплит в `datasets/02_preprocessed`.

Выходной формат записи:

```json
{
  "sentence_id": "eng_en_gum-ud-train.conllu_1",
  "text": "Aesthetic Appreciation and Spanish Art:",
  "nodes": [
    {
      "id": "w1",
      "name": "Aesthetic",
      "lemma": "aesthetic",
      "pos_universal": "ADJ",
      "pos_specific": "JJ",
      "features": {"Degree": "Pos"},
      "syntactic_link_candidates": ["Comparison", "Numeric", "Quality"],
      "syntactic_link_target_id": "w2",
      "original_deprel": "amod"
    }
  ]
}
```

### 2. `02_local_generation`

Точка входа: [`02_local_generation/pipeline.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/02_local_generation/pipeline.py)

Что делает:

- читает `datasets/02_preprocessed/*.json`;
- отправляет только поле `text` в локальный inference-сервис `LOCAL_INFER_URL`;
- сохраняет ответ в `datasets/03_local_generated/*.jsonl`;
- отмечает проблемные записи флагом `node_error`;
- логирует несовпадения числа узлов и ошибки запросов в `logs/local_generation_errors.log`.

Это отдельный этап для локального чернового прогона. В текущей версии проекта он не участвует в сборке `datasets/04_fixed`.

### 3. `03_gemini_fix_errors`

Точки входа:

- [`03_gemini_fix_errors/pipeline.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/pipeline.py)
- [`03_gemini_fix_errors/scheduler.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/scheduler.py)

Что делает:

- читает `datasets/02_preprocessed/*.json`;
- преобразует запись в компактный формат для LLM;
- отправляет запрос либо в Google GenAI, либо в локальный сервис;
- валидирует ответ через [`03_gemini_fix_errors/validator.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/validator.py);
- при успехе пишет `sentence_id`, `text`, `nodes`, `model_name` в `datasets/04_fixed/*.jsonl`;
- пропускает уже обработанные `sentence_id`, поэтому пайплайн можно перезапускать.

Проверки валидатора:

- набор `id` в ответе должен совпадать с исходным;
- выбранный `syntactic_link_name` должен входить в `syntactic_link_candidates`.

Ошибки валидации пишутся в `logs/validator_errors.log`.

Шедулер в [`03_gemini_fix_errors/scheduler.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/03_gemini_fix_errors/scheduler.py) рассчитан на регулярный запуск с большим пулом ключей и ограничением по квотам.

### 4. `04_postprocessor`

Точка входа: [`04_postprocessor/prepare_final_dataset.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/04_postprocessor/prepare_final_dataset.py)

Что делает:

- берёт исходные ноды из `datasets/02_preprocessed`;
- подтягивает выбранные `syntactic_link_name` из `datasets/04_fixed`;
- проверяет совпадение числа узлов и набора `id`;
- собирает финальный формат:

```json
{
  "input": "Aesthetic Appreciation and Spanish Art:",
  "output": [
    {
      "id": "w1",
      "name": "Aesthetic",
      "pos_universal": "ADJ",
      "case": null,
      "syntactic_link_name": "Quality",
      "syntactic_link_target_id": "w2"
    }
  ]
}
```

## Конфигурация

Ключевые файлы:

- [`config/paths.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/paths.py) — все пути к данным и логам;
- [`config/generate_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.py) — модель, URL локальных сервисов, строки с ключами;
- [`config/pipeline_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/pipeline_conf.py) — стратегия запросов, воркеры, retry, лимиты шедулера;
- [`config/prompts.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/prompts.py) — системные и пользовательские промпты;
- [`config/semantic.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/semantic.py) — эвристики и карта семантических отношений.

Поддерживаемые переменные окружения:

- `GEMINI_API_KEYS="key1,key2"` — переопределяет строку ключей из `config/generate_conf.py`;
- `GEMINI_REQUEST_STRATEGY=genai|local` — выбор между Google GenAI и локальным сервисом;
- `SCHEDULER_WORKERS=4` — число параллельных воркеров шедулера;
- `SCHEDULER_ERROR_LIMIT=10` — порог подряд идущих ошибок на один ключ;
- `SCHEDULER_DAILY_QUOTA=250` — лимит успешных запросов на воркер.

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

Быстрый старт:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pyconll google-genai tqdm requests
```

## Как запускать

Запускать команды нужно из корня репозитория.

### Предобработка корпуса

```bash
python 01_preprocessor/main.py
```

Результат: `datasets/02_preprocessed/*.json`

### Локальная генерация

```bash
python 02_local_generation/pipeline.py
```

Результат: `datasets/03_local_generated/*.jsonl`

### Исправление через Gemini или локальный сервис

```bash
export GEMINI_API_KEYS="key1,key2"
export GEMINI_REQUEST_STRATEGY=genai
python 03_gemini_fix_errors/pipeline.py
```

Или через локальный сервис:

```bash
export GEMINI_REQUEST_STRATEGY=local
python 03_gemini_fix_errors/pipeline.py
```

Результат: `datasets/04_fixed/*.jsonl`

### Однократный запуск шедулера

```bash
python 03_gemini_fix_errors/scheduler.py
```

Результат: пополнение `datasets/04_fixed/*.jsonl` и сводка в `logs/scheduler_summary.log`

### Сборка финального датасета

```bash
python 04_postprocessor/prepare_final_dataset.py
```

Результат: `datasets/05_final/*.json`

### Анализ preprocessed-датасета

```bash
python utils/analyze_dataset.py
```

## Данные

Ожидаемая структура исходных корпусов:

```text
datasets/01_raw_corpus/
├── arm/
├── eng/
└── rus/
```

Язык определяется по имени подпапки, а сплит по имени файла:

- `*train*.conllu` -> `train`
- `*dev*.conllu` или `*val*.conllu` -> `val`
- `*test*.conllu` -> `test`

Если `.conllu` не содержит ни одного из этих маркеров в имени файла, он будет пропущен.

## Логи

Проект пишет логи в `logs/`:

- `processor_fallback.log` — случаи fallback-эвристик в preprocessor;
- `local_generation_errors.log` — ошибки локальной генерации и mismatch числа узлов;
- `validator_errors.log` — ошибки выбора связи вне списка кандидатов;
- `scheduler_summary.log` — итоговые отчёты шедулера.

## Ограничения и особенности текущей реализации

- `03_gemini_fix_errors` сейчас не использует `datasets/03_local_generated`.
- `validator.py` логирует ошибку выбора связи вне кандидатов, но фактически не отклоняет такой ответ, потому что возврат `False` в этой ветке закомментирован.
- `04_postprocessor` собирает итог только по тем записям, которые есть и в `02_preprocessed`, и в `04_fixed`.
- В репозитории есть захардкоженные ключи в [`config/generate_conf.py`](/home/t_6amape9l/PycharmProjects/akin_core_datagen/config/generate_conf.py); для реальной эксплуатации лучше держать их только в переменных окружения и не коммитить.

## Проверка после запуска

Минимальная ручная проверка:

1. Убедиться, что после `01_preprocessor` появились файлы `datasets/02_preprocessed/<lang>_<split>.json`.
2. Проверить, что после `03_gemini_fix_errors` пополняются `datasets/04_fixed/*.jsonl` и нет массовых ошибок в `logs/validator_errors.log`.
3. Сравнить несколько записей из `datasets/05_final/*.json` с исходными `sentence_id` из preprocessed-файлов.
