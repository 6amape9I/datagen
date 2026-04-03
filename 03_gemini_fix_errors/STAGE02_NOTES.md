# Stage 03 — LLM Annotation

Каталог всё ещё называется `03_gemini_fix_errors` по историческим причинам, но логическая роль стадии теперь нейтральна: она читает canonical `units`, собирает model input и сохраняет `syntactic_link_name` в `datasets/04_fixed`.

## Canonical contract

Stage 01 пишет:

- `tokens` — raw UD layer
- `units` — canonical normalized layer
- `legacy_nodes` — optional compat export only

Stage 03 использует:

- `units` для model input
- общую онтологию ролей для validator
- `legacy_nodes` только если нужно вручную сравнить старый экспорт, но не как normal-path dependency

## Основные файлы

- `pipeline.py` — формирует очередь, строит payload для LLM и пишет `datasets/04_fixed/*.jsonl`
- `scheduler.py` — однократный шедулер с пулом ключей и лимитами
- `gemini_client.py` / `local_client.py` — клиенты моделей
- `validator.py` — сравнивает ответ модели с canonical units и логирует ошибки в `logs/validator_errors.log`

## Ход пайплайна

1. `load_processed_ids()` собирает уже обработанные `sentence_id` из `datasets/04_fixed/*.jsonl`.
2. `build_task_queue_from_preprocessed()` читает `datasets/02_preprocessed/*.json`.
3. `_convert_nodes_for_llm()` строит payload из `units`.
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
5. `validator.validate_response()` сравнивает ответ модели с `units`:
   - ID должны совпасть полностью;
   - роль должна входить в общую онтологию;
   - `ROOT` допустим только для unit без `syntactic_link_target_id`.
6. При успехе результат записывается в `datasets/04_fixed/<split>.jsonl`.

## Проверки validator

- набор `id` в ответе должен совпадать с canonical units
- дубликаты ID запрещены
- роль должна входить в shared ontology
- `ROOT` валиден только для корневого unit

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
