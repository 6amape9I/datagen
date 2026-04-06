# План для Codex: объединение `02_local_generation` и `03_annotation` в единый generation layer

## Цель

Перестроить текущие слои генерации в единый, чистый и экономный generation layer, который:

- использует **один общий pipeline** для любых провайдеров;
- принимает на вход **компактный Stage 01 output**;
- подаёт в модель **строго определённый компактный payload**;
- получает ответ в **минимальном формате** `id + syntactic_link_name`;
- поддерживает два основных entrypoint:
  - `local_gen.py`
  - `google_gen.py`
- не хранит и не дублирует лишние промежуточные форматы;
- не смешивает single-sentence node labeling с более высокими межпредложенческими/фактологическими связями.

---

## Архитектурное решение

## Новый слой

Создать новый канонический слой:

`03_generation/`

Содержимое:

- `pipeline.py` — общий orchestration для generation;
- `input_builder.py` — построение model input из compact Stage 01 nodes;
- `prompt_builder.py` — сборка system prompt + user prompt;
- `response_schema.py` — единая схема structured output и список разрешённых ролей;
- `validator.py` — проверка структуры ответа;
- `providers/google_genai.py` — провайдер Google GenAI;
- `providers/local_http.py` — провайдер локального HTTP-сервиса;
- `providers/base.py` — общий протокол / интерфейс провайдера;
- `google_gen.py` — entrypoint для GenAI;
- `local_gen.py` — entrypoint для локальной генерации;
- `scheduler.py` — только если реально нужен для Google batch use case.

После перехода:

- удалить дублирующую бизнес-логику из `02_local_generation/`;
- удалить старый `03_annotation/` как боевой слой;
- если нужно оставить временно — то только как thin compatibility stubs с предупреждением и редиректом на новый слой.

Итоговая каноническая цепочка:

`01_preprocessor -> datasets/02_preprocessed -> 03_generation -> datasets/04_fixed -> 04_postprocessor -> datasets/05_final`

---

## Важное ограничение

Этот generation layer сейчас решает **только задачу назначения node-level semantic relation** для узлов внутри одного предложения.

Не добавлять сюда:

- типы предложений;
- эмоции;
- связи между несколькими предложениями;
- межсобытийные / межфразовые логические отношения;
- фактологические дополнительные метаданные.

Если позже понадобится multi-sentence mode, это должен быть **отдельный режим или отдельный слой**, а не загрязнение текущего single-sentence annotator.

---

## Входные данные: строгий контракт

Generation layer должен читать compact records из `datasets/02_preprocessed/*.json`.

Каждая sentence record уже содержит:

- `sentence_id`
- `text`
- `language_code`
- `split`
- `source_file`
- `nodes`

### Строгий список полей, которые нужно подавать в модель

В model input подавать только:

На уровне предложения:

- `text`
- `nodes`

На уровне узла:

- `id`
- `name`
- `lemma`
- `pos_universal`
- `features`
- `syntactic_link_target_id`
- `original_deprel`
- `introduced_by` (опционально, только если непустой)
- `head_lemma` (вычисляется на лету из `syntactic_link_target_id`, не хранится в Stage 01, но может быть добавлен в model payload)

### Что НЕ подавать в модель

Не подавать:

- `sentence_id`
- `language_code` по умолчанию
- `split`
- `source_file`
- любые candidate lists
- любые legacy-поля
- любые raw-token слои
- любые debug-поля
- любые внутренние решения builder-а
- `pos_specific`, пока не будет доказано эмпирически, что оно реально улучшает качество

### Почему такой вход правильный

Он:

- достаточно информативен для выбора связи;
- экономит токены;
- не заставляет модель заново восстанавливать структуру узлов;
- не тащит лишние поля, не влияющие на качество разметки.

---

## Формат входа в модель

### Канонический model payload

```json
{
  "text": "В советский период времени число ИТ-специалистов в Армении составляло около десяти тысяч.",
  "nodes": [
    {
      "id": "w3",
      "name": "В период",
      "lemma": "период",
      "pos_universal": "NOUN",
      "features": {"Case": "Acc"},
      "syntactic_link_target_id": "w11",
      "original_deprel": "obl",
      "introduced_by": ["В"],
      "head_lemma": "составлять"
    }
  ]
}
```

### Сборка payload

Сборка должна идти через `input_builder.py`.

Там нужно:

1. прочитать compact record;
2. построить `node_map` по `id`;
3. для каждого узла восстановить `head_lemma`, если target существует;
4. включать `introduced_by` только если список непустой;
5. не включать поля со значением `null`/пустой список без необходимости.

---

## Выходные данные: строгая схема

### Требуемый ответ модели

Да, ответ должен быть минимальным ради экономии токенов.

Канонический ответ:

```json
{
  "nodes": [
    {"id": "w3", "syntactic_link_name": "Duration"},
    {"id": "w11", "syntactic_link_name": "ROOT"}
  ]
}
```

### Строгий список полей в выходе

Для каждого узла модель должна вернуть только:

- `id`
- `syntactic_link_name`

### Что НЕ должно возвращаться

- `name`
- `lemma`
- `pos_universal`
- `features`
- `syntactic_link_target_id`
- комментарии
- reasoning
- markdown
- лишние поля

### Почему это правильно

Потому что:

- по `id` downstream всегда восстановит нужный узел;
- выход становится дешёвым по токенам;
- validator и postprocessor могут работать строго и просто.

---

## Structured generation: обязательный контракт

Structured generation обязателен.

Для Google GenAI:

- использовать `response_mime_type="application/json"`;
- использовать явную schema `{"nodes": [{"id": str, "syntactic_link_name": enum[...] }]}`;
- enum должен строиться из онтологии ролей.

Для локального провайдера:

- по возможности требовать тот же JSON shape;
- если локальная модель не умеет schema enforcement, всё равно post-parse validator обязан проверять ту же структуру.

---

## Prompt architecture

## Источники контекста

Есть два уровня контекста:

1. **node-level semantic roles** — это текущая задача;
2. **higher-level sentence / multi-sentence relations** — это НЕ текущая задача этого слоя.

Поэтому generation layer должен использовать **сжатый node-level ontology context**.

Не слать каждый раз полные большие документы в prompt.

---

## Новый prompt design

### 1. System prompt

System prompt должен быть коротким, строгим и стабильным.

Он должен содержать:

- роль модели: semantic relation annotator;
- описание входа;
- описание выхода;
- правило для `ROOT`;
- запрет на лишний текст;
- сжатую онтологию ролей;
- короткие правила разрешения неоднозначности.

### 2. User prompt

User prompt должен быть компактным:

- короткая task-инструкция;
- compact JSON payload.

Не использовать огромный обучающий пример в каждом запросе.

### 3. Context compression

Сделать отдельный компактный runtime context file, например:

- `03_generation/context/semantic_roles_compact.py` или `.json`

Там хранить для каждой роли:

- `name`
- `short_definition`
- `core_cues`
- `common_confusions` (опционально)

Из этого файла автоматически собирать:

- enum для response schema;
- сокращённый system prompt;
- optional disambiguation fragments.

---

## Что делать с текущими prompt-файлами

### Нужно убрать

Из runtime prompt-цепочки убрать:

- гигантский hand-written training example, который сейчас ест много токенов;
- полную энциклопедическую простыню, если она шлётся на каждый запрос;
- любые части, не влияющие на непосредственный выбор `syntactic_link_name`.

### Нужно оставить

- строгую инструкцию;
- компактный glossary ролей;
- правила валидности ответа.

---

## Конкретный состав model context

### Обязательно включить в runtime context

- список разрешённых relation names;
- очень короткие определения ролей;
- ключевые различения:
  - `Agent` vs `Patient`;
  - `Recipient` vs `Patient`;
  - `Inclusion_Containment` vs `Support` vs `Contact_Adjacency`;
  - `Quality` vs `Possession` vs `Content_Theme`;
  - `Duration` vs `Point_in_Time` vs `Frequency`;
  - `ROOT` rule.

### Не включать в каждый запрос

- длинные развёрнутые примеры по каждой роли;
- sentence-type metadata;
- higher-level inter-sentence relations;
- всё, что не нужно для single-sentence node labeling.

---

## Настройки Google GenAI

Сделать настройки generation layer конфигурируемыми.

Вынести в runtime config:

- `MODEL_NAME`
- `THINKING_BUDGET`
- `MAX_OUTPUT_TOKENS`
- `TEMPERATURE` (если используется)
- `REQUEST_STRATEGY` / provider selection

### Базовые рекомендации

- structured output — обязательно;
- thinking budget — не хардкодить навсегда в `-1`;
- сделать нормальный default для bulk annotation;
- сделать отдельный high-think режим для повторных прогонов / sampled review / difficult cases.

### Предпочтительный режим

- обычная массовая разметка: умеренный thinking budget;
- не использовать максимальное think без необходимости;
- retry на повышенном think только при невалидных ответах или проблемных кейсах.

---

## Новый execution model

### Общий pipeline

`pipeline.py` должен:

1. читать preprocessed `.json`;
2. строить очередь задач;
3. собирать model input через `input_builder.py`;
4. собирать prompt через `prompt_builder.py`;
5. отправлять запрос через provider;
6. валидировать ответ;
7. писать результат в `datasets/04_fixed/*.jsonl`.

### Entry points

#### `google_gen.py`
Запускает общий pipeline с Google provider.

#### `local_gen.py`
Запускает общий pipeline с local provider.

Они не должны дублировать pipeline-логику. Они только выбирают provider/config.

---

## Валидация

`validator.py` должен проверять:

1. ID parity:
   - все входные `id` присутствуют;
   - нет лишних `id`;
   - нет дублей `id`.

2. Ontology membership:
   - `syntactic_link_name` входит в разрешённый enum.

3. ROOT integrity:
   - если `syntactic_link_target_id is null`, то только `ROOT`;
   - если `syntactic_link_target_id != null`, то `ROOT` запрещён.

### Что validator НЕ должен делать

- не должен возвращать старые candidate-based ограничения;
- не должен зависеть от legacy candidate lists;
- не должен пытаться реконструировать семантику.

---

## Выходной артефакт generation layer

Каждая строка `datasets/04_fixed/*.jsonl` должна содержать:

- `sentence_id`
- `text`
- `nodes` (только `id` + `syntactic_link_name`)
- `model_name`
- опционально `provider`
- опционально `request_mode` / `generation_profile`

Не писать туда дубли узловой информации, которая уже есть в Stage 01.

---

## Postprocessor alignment

`04_postprocessor` должен продолжать работать так:

- брать узлы из Stage 01 compact `nodes`;
- брать labels из `04_fixed`;
- склеивать по `id`;
- строить final dataset.

Ничего дополнительного для Stage 04 в generation output не нужно.

---

## Конфигурация

Generation layer должен использовать существующий укреплённый runtime config слой.

Нужно расширить конфигурацию аккуратно:

### Вынести в config/runtime.py или соседний generation config:

- `MODEL_NAME`
- `LOCAL_API_URL`
- `LOCAL_INFER_URL`
- `API_KEYS_STR`
- `ALL_KEYS_FOR_SHEDULE`
- `REQUEST_STRATEGY`
- `THINKING_BUDGET`
- `MAX_OUTPUT_TOKENS`
- `GENERATION_PROFILE` / `PROMPT_VARIANT` (если потребуется)

### Не делать

- не хардкодить настройки прямо в provider-файлах;
- не размазывать prompt-настройки по нескольким модулям;
- не плодить дублирующие config sources.

---

## Что удалить / вычистить

После завершения рефакторинга удалить или вычистить:

- дублирующую бизнес-логику из `02_local_generation/pipeline.py`;
- старый отдельный orchestration из `03_annotation/`, если он заменён;
- старые prompt-артефакты, которые больше не используются;
- runtime code paths, которые шлют только `text` без `nodes`;
- старые, слишком длинные training-style prompt blocks, если они больше не входят в новый prompt design.

Если старые entrypoints временно остаются — пусть они печатают короткое предупреждение и делегируют в новый слой.

---

## Тесты

Нужно добавить или обновить тесты:

1. `input_builder`:
   - формирует ровно нужные поля;
   - не тащит лишние поля;
   - корректно вычисляет `head_lemma`.

2. `prompt_builder`:
   - system prompt не пустой;
   - user prompt содержит compact payload;
   - не включает запрещённые лишние блоки.

3. `validator`:
   - валидный минимальный ответ проходит;
   - invalid role отклоняется;
   - duplicate ids отклоняются;
   - bad ROOT usage отклоняется.

4. provider contract:
   - provider interface единый;
   - pipeline одинаково работает с local/google providers.

5. end-to-end smoke:
   - одно preprocessed предложение -> prompt -> mocked provider -> validator -> jsonl output.

---

## Что считать завершением работы

Definition of Done:

1. В проекте существует единый generation layer вместо двух разрозненных слоёв.
2. Есть два entrypoint:
   - `local_gen.py`
   - `google_gen.py`
3. Оба используют один и тот же pipeline.
4. На вход модели подаётся строго определённый compact payload.
5. На выходе ожидается только `id + syntactic_link_name`.
6. Structured generation обязателен для Google provider.
7. Prompt стал компактнее и дешевле, чем раньше.
8. Полные docs не шлются в каждый запрос.
9. Stage 04 не ломается и продолжает восстанавливать полную узловую информацию по `id`.
10. Старые дублирующие code paths удалены или сведены к thin wrappers.

---

## Приоритет выполнения

### Фаза 1 — Архитектура
- создать `03_generation/`
- перенести общий pipeline
- создать provider interface
- завести два entrypoint

### Фаза 2 — Input / Output contract
- реализовать `input_builder.py`
- зафиксировать минимальный output schema
- обновить validator

### Фаза 3 — Prompt redesign
- сократить system prompt
- убрать гигантские runtime examples
- сделать компактный ontology context

### Фаза 4 — Config
- добавить generation-specific runtime settings
- убрать хардкод thinking/output settings из provider code

### Фаза 5 — Cleanup
- убрать старые дублирующие пути
- обновить README
- обновить docs
- прогнать smoke tests
