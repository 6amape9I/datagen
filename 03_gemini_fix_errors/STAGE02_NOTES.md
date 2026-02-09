# Stage 03 — Gemini Fix Errors

Стадия `03_gemini_fix_errors` берёт результат локальной генерации и правит ошибки с помощью Gemini. На вход подаются объединённые данные из `datasets/02_preprocessed` и `datasets/03_local_generated`, а на выходе формируется исправленный набор в `datasets/04_fixed`.

## Основные файлы и импорты

- `pipeline.py` — точка входа `run_pipeline_final()`. Импортирует:
  - служебные модули (`Path`, `json`, `threading`, `Queue`, `cycle`);
  - `requests` (HTTP-клиент);
  - `config` (`API_KEYS`, `MODEL_NAME`, `NUM_WORKERS`, `MAX_RETRIES`, `INITIAL_BACKOFF_DELAY`, `PREPROCESSED_DATA_DIR`, `LOCAL_GENERATED_DATA_DIR`, `FIXED_DATA_DIR`);
  - локальные `gemini_client.get_model_response` и `validator.validate_response`.
- `scheduler.py` — дневной шедулер, переиспользует helper’ы из `pipeline.py`.
- `gemini_client.py` — обёртка над HTTP-сервисом. Использует из `config` промпты и `LOCAL_API_URL`.
- `validator.py` — проверяет ответ модели и логирует ошибки в `logs/validator_errors.log`.

## Конфигурация и данные

- API ключи приходят из `config/pipeline_conf.py`: строка по умолчанию прописана в `config/generate_conf.py`, но её можно переопределить переменной окружения `GEMINI_API_KEYS="key1,key2"`.
- Число воркеров (`NUM_WORKERS`) и лимиты ретраев (`MAX_RETRIES`, `INITIAL_BACKOFF_DELAY`) задаются в `config/pipeline_conf.py`.
- Пути к данным берутся из `config/paths.py`:
  - вход-1: `datasets/02_preprocessed/*.json` (`PREPROCESSED_DATA_DIR`);
  - вход-2: `datasets/03_local_generated/*.jsonl` (`LOCAL_GENERATED_DATA_DIR`);
  - выход: `datasets/04_fixed/*.jsonl` (`FIXED_DATA_DIR`).
- Модель (`MODEL_NAME`) задаётся в `config/generate_conf.py` и сохраняется в выходных записях для трекинга.

## Ход пайплайна (`pipeline.run_pipeline_final`)

1. Если ключей нет, пишет предупреждение и продолжает работать через локальный сервис.
2. `load_processed_ids()` проходит по `datasets/04_fixed/*.jsonl`, собирает `sentence_id`, чтобы не перегенерировать записи (дубли игнорируются).
3. `migrate_data_to_include_model_name()` обеспечивает наличие поля `model_name` в старых jsonl (ставит `unknown`).
4. `build_task_queue_from_local()` формирует очередь задач:
   - берёт каждый `*.jsonl` из `datasets/03_local_generated`;
   - ищет соответствующий `*.json` в `datasets/02_preprocessed`;
   - объединяет записи по `sentence_id` через `merge_sentence_data()` так, чтобы сохранить кандидатов из preprocessed;
   - кладёт в очередь только ещё не обработанные `sentence_id`.
5. Если очередь пустая — ранний выход.
6. Создаются воркеры (`threading.Thread`, имя `Воркер-i`), каждый поднимает `requests.Session` с отключённым прокси (`trust_env = False`).
7. Каждый воркер:
   - забирает объединённую запись из очереди;
   - до `MAX_RETRIES` раз:
     - делает копию данных → `preprocess_sentence_for_llm()` → `gemini_client.get_model_response()`;
     - прогоняет ответ через `validator.validate_response(original, response['nodes'])`;
     - при успехе пишет запись (с `model_name`) в `datasets/04_fixed/<split>.jsonl` под lock.
8. Основной поток ждёт `task_queue.join()` и печатает, что работа завершена.

## Проверки и логи

- `validator.validate_response()` гарантирует:
  - `id` в ответе полностью совпадает с исходными (`set` сравнение).
  - Выбранная `syntactic_link_name` входит в кандидатов для ноды (`syntactic_link_candidates` поддерживает оба формата — список словарей с `name` или просто имена).
- При нарушении второго правила логирует JSON с подробным описанием ноды и текста в `logs/validator_errors.log` через выделенный логгер.
- `file_locks` создаются лениво для каждого встреченного `output_filename` и устраняют гонки при одновременной записи потоков.

## Взаимодействие с локальным сервисом (`gemini_client.get_model_response`)

- Собирает полный промпт: `BASE_PROMPT + json.dumps(sentence_data) + PROMPT_SUFFIX`.
- Отправляет `POST` на `LOCAL_API_URL` с `{"text": "...промпт..."}`.
- Берёт строку ответа из поля `response`, декодирует `json.loads`.
- Все ошибки (отсутствие клиента, пустой ответ, `JSONDecodeError`) логируются в stdout; вызывающий воркер запускает повтор.

## Быстрый запуск

```bash
export GEMINI_API_KEYS="key1,key2"  # если нужно переопределить config (не обязателен для локального сервиса)
python 03_gemini_fix_errors/pipeline.py
```

Перед запуском убедитесь, что:

- в `datasets/02_preprocessed/` лежат `*.json` из этапа 01;
- в `datasets/03_local_generated/` лежат `*.jsonl` из этапа 02;
- директории из `config/paths.py` существуют (создаются автоматически при импорте config);
- локальный сервис доступен на `LOCAL_API_URL`;
- лог `logs/validator_errors.log` доступен на запись (создаётся автоматически).

## Ежедневный шедулер

- Конфигурация ключей: `config/generate_conf.ALL_KEYS_FOR_SHEDULE` (строка через запятую). После изменения перезапустите скрипт.
- Параметры параллелизма и ограничений: `config/pipeline_conf` (`SCHEDULER_MAX_CONCURRENT_WORKERS`, `SCHEDULER_CONSECUTIVE_ERROR_LIMIT`, `SCHEDULER_DAILY_QUOTA`).
- Запуск: `python 03_gemini_fix_errors/scheduler.py`. Скрипт один раз сканирует очередь, отрабатывает и завершает работу. Его можно дергать раз в день cron'ом.
- Алгоритм держит ровно `N` активных воркеров (по умолчанию 4). Каждый воркер:
  1. Берёт из пула очередной ключ и генерирует датасет, пока не получит сообщение о квоте/не достигнет лимита `SCHEDULER_DAILY_QUOTA`.
  2. Останавливается, если 10 задач подряд завершились ошибкой (после всех `MAX_RETRIES`), при этом текущая задача возвращается в очередь.
  3. После завершения ключ попадает в список использованных, воркер переключается на следующий ключ до тех пор, пока список не закончится.
- В конце работы подсчитывается количество успешных запросов и пишется сводка в `logs/scheduler_summary.log`. Если ключи закончились раньше задач, оставшиеся предложения останутся в очереди для следующего запуска.
