# Stage 03 — Gemini Fix Errors

Стадия `03_gemini_fix_errors` читает записи из `datasets/02_preprocessed`, строит model input и сохраняет размеченные `syntactic_link_name` в `datasets/04_fixed`.

## Что изменилось после rebuild Stage 01

Stage 01 теперь пишет schema v2:

- `tokens` — сырой UD-слой
- `units` — основной normalized слой
- `legacy_nodes` — transitional compatibility слой

Stage 03 использует это так:

- для model input предпочитает `units`
- для validator compatibility-check использует `legacy_nodes`
- для старых файлов без schema v2 умеет падать обратно на `nodes`

## Основные файлы

- `pipeline.py` — формирует очередь, строит payload для LLM и пишет `datasets/04_fixed/*.jsonl`
- `scheduler.py` — однократный шедулер с пулом ключей и лимитами
- `gemini_client.py` / `local_client.py` — клиенты моделей
- `validator.py` — сравнивает ответ модели с compatibility-слоем и логирует ошибки в `logs/validator_errors.log`

## Ход пайплайна

1. `load_processed_ids()` собирает уже обработанные `sentence_id` из `datasets/04_fixed/*.jsonl`.
2. `build_task_queue_from_preprocessed()` читает `datasets/02_preprocessed/*.json`.
3. `_convert_nodes_for_llm()`:
   - если есть `units`, строит payload из них;
   - если `units` нет, использует legacy `nodes`.
4. В payload для модели можно передавать:
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
5. `validator.validate_response()` сравнивает ответ модели с `legacy_nodes` или, для старого формата, с `nodes`.
6. При успехе результат записывается в `datasets/04_fixed/<split>.jsonl`.

## Проверки validator

- набор `id` в ответе должен совпадать с compatibility-слоем;
- выбранная `syntactic_link_name` должна входить в `syntactic_link_candidates`;
- при нарушении второго правила ошибка логируется, но сейчас не делает ответ фатальным, потому что `return False` в этой ветке закомментирован.

## Быстрый запуск

```bash
export GEMINI_API_KEYS="key1,key2"
python 03_gemini_fix_errors/pipeline.py
```

Для локального сервиса:

```bash
export GEMINI_REQUEST_STRATEGY=local
python 03_gemini_fix_errors/pipeline.py
```

## Шедулер

Запуск:

```bash
python 03_gemini_fix_errors/scheduler.py
```

Конфиг задаётся через `config/pipeline_conf.py` и `config/generate_conf.py`:

- `SCHEDULER_MAX_CONCURRENT_WORKERS`
- `SCHEDULER_CONSECUTIVE_ERROR_LIMIT`
- `SCHEDULER_DAILY_QUOTA`
- `ALL_KEYS_FOR_SHEDULE`
