# datagen — следующий план перехода в новый формат и удаления legacy-зависимостей

## Цель этапа

Довести проект из состояния **"Stage 01 уже обновлён, но вся система ещё живёт на переходном слое"**
до состояния **"canonical-слой = units, downstream работает по units, legacy удалён или сведён к минимальному импортному адаптеру"**.

Этот этап не про косметику. Он про:

- окончательный выход из transition-mode;
- удаление устаревших слоёв и двусмысленных контрактов;
- устранение ошибок, которые искажают датасет;
- перевод проекта в архитектуру, где смена модели не требует ломать pipeline.

---

## Главные проблемы, которые должны быть устранены

1. **Validator всё ещё завязан на `legacy_nodes` и не отклоняет плохой ответ**, потому что ветка с `return False` закомментирована.
2. **Stage 04 всё ещё строит финальный датасет из `legacy_nodes`, а не из canonical `units`.**
3. **Legacy candidate logic всё ещё влияет на валидацию и переходный контракт.**
4. **В `heuristic_candidates.py` matching условий правил работает как OR, а не как AND.**
5. **Model layer всё ещё gemini-centric и partially hardcoded.**
6. **Attachment policy пока формально multilingual, но фактически не использует `language_code`.**
7. **В проекте ещё есть transitional compatibility элементы, которые надо либо удалить, либо изолировать.**

---

## Итоговое целевое состояние

После завершения работ проект должен выглядеть так:

- `tokens` = raw authoritative UD layer;
- `units` = canonical normalized layer;
- model input строится только из `units`;
- validator работает по `units` и общей онтологии ролей;
- Stage 04 собирает финальный `input/output` из `units`;
- legacy candidate logic не управляет качеством и не является gatekeeper;
- `legacy_nodes` либо удалён полностью, либо вынесен в отдельный explicit export mode для старых данных/сравнений;
- model layer не привязан по именам и структуре к Gemini;
- multilingual attachment policy действительно использует типологические различия языков;
- проект имеет чёткие тесты на новую схему и на миграционный сценарий.

---

# PHASE 1 — Немедленно устранить ошибки, искажающие поведение

## 1.1. Исправить validator

### Что сделать

- В `03_gemini_fix_errors/validator.py` убрать ложную "полустатусную" валидацию.
- Выбрать один из двух режимов и реализовать его явно:

#### Вариант A — strict validation
Если `syntactic_link_name` отсутствует в допустимом наборе, validator возвращает `False`, а pipeline делает retry/reject.

#### Вариант B — ontology-only validation
Если проект больше не хочет ограничивать модель candidates-списками, validator должен:
- проверять совпадение ID;
- проверять, что роль входит в общую онтологию;
- проверять специальные условия для `ROOT`;
- **не** проверять членство в `syntactic_link_candidates`.

### Решение для этого проекта
Рекомендуется **Вариант B**.

Почему:
- проект уже сместился к модели как основному решающему модулю;
- candidates стали soft layer;
- держать строгую проверку по legacy candidates — значит тащить старую архитектуру дальше.

### Что удалить

Удалить из validator:
- зависимость от `legacy_nodes` как от канонического источника для проверки роли;
- логику, в которой список кандидатов трактуется как обязательное ограничение;
- закомментированную ветку `#return False`.

### Acceptance criteria

- validator больше не использует legacy candidates как обязательный барьер;
- поведение validator описано явно и не содержит закомментированной логики;
- invalid role действительно приводит к `False`;
- mismatch ID действительно приводит к `False`.

---

## 1.2. Исправить OR-баг в heuristic rules

### Что сделать

В `01_preprocessor/heuristic_candidates.py` исправить rule matching:
- сейчас правило считается сработавшим, если совпало **любое одно** условие;
- нужно изменить это на **all conditions must match**.

### Что удалить

Удалить текущую логику:
- `conditions_met = True` на первом совпавшем условии;
- саму OR-семантику внутри одного rule.

### Что оставить

Допустимо сохранить fallback-уровни, но только после корректного AND matching.

### Acceptance criteria

- каждое правило матчит только если выполнены все его условия;
- soft candidates становятся уже и чище;
- число fallback-all случаев не увеличивается искусственно из-за широкого OR-match.

---

## 1.3. Убрать misleading naming там, где это влияет на решения

### Что сделать

Необязательно сразу переименовывать всё физически, но надо как минимум:
- убрать из комментариев и документации ощущение, что `legacy_nodes` — нормальный основной контракт;
- пометить его как deprecated transitional export;
- явно указать, что canonical layer = `units`.

### Acceptance criteria

- нет двусмысленных описаний, где legacy выглядит как нормальный постоянный слой.

---

# PHASE 2 — Перевести downstream на canonical `units`

## 2.1. Перевести Stage 04 с `legacy_nodes` на `units`

### Что сделать

Переписать `04_postprocessor/prepare_final_dataset.py`, чтобы он собирал итоговый dataset из:
- `source_record["units"]`
- ответа модели `datasets/04_fixed/*.jsonl`

### Новый контракт Stage 04

Для каждого unit в source:
- `id` = `unit_id`
- `name` = `surface`
- `pos_universal` = `upos`
- `case` = `features.get("Case")`
- `syntactic_link_target_id` = `syntactic_link_target_id`
- `syntactic_link_name` = из model output

### Что удалить

Удалить из Stage 04:
- зависимость от `get_legacy_nodes(source_record)`;
- трансформацию финального output из legacy-формы;
- идею, что final dataset обязан отражать старую форму `name`, если canonical surface уже есть в `units`.

### Допустимо

На переходный период можно оставить feature flag:
- `USE_LEGACY_POSTPROCESSOR=false` по умолчанию;
- старый режим только временно для сравнения.

Но после завершения фазы старый режим должен быть удалён.

### Acceptance criteria

- Stage 04 может собрать финальный датасет без `legacy_nodes`;
- output полностью совместим по смыслу со старым форматом;
- для v2 preprocessed-файлов legacy не нужен.

---

## 2.2. Перевести validator на `units`

### Что сделать

Сделать validator структурным и unit-centric.

Он должен проверять:
- совпадение `unit_id` и ID в model output;
- отсутствие дублей;
- все units покрыты ответом;
- все `syntactic_link_name` входят в общую онтологию;
- `ROOT` допустим только для node с `syntactic_link_target_id = null`.

### Что удалить

Удалить из validator:
- `get_legacy_nodes()` как основной источник истины;
- обязательную зависимость от `syntactic_link_candidates`.

### Acceptance criteria

- validator полностью работает на `units`;
- legacy-слой больше не участвует в принятии решения, принимать ответ или нет.

---

## 2.3. Перевести local generation comparison с legacy count на units count

### Что сделать

В `02_local_generation/pipeline.py` перестать сравнивать размер ответа с `legacy_nodes`.
Сравнивать нужно с `units`.

### Что удалить

Удалить:
- использование `get_legacy_nodes()` ради expected node count.

### Acceptance criteria

- Stage 02 опирается на canonical unit count.

---

# PHASE 3 — Удалить или изолировать legacy export

## 3.1. Перевести `legacy_nodes` в optional export mode

### Что сделать

Сделать `legacy_nodes` не обязательной частью каждого preprocessed record, а одним из режимов экспорта.

Рекомендуемые режимы:
- `export_mode="canonical"` → сохраняются только `tokens` и `units`;
- `export_mode="canonical+legacy"` → добавляется `legacy_nodes` для сравнения/миграции.

### Что удалить

Удалить assumption, что `legacy_nodes` всегда должен присутствовать в JSON.

### Acceptance criteria

- Stage 01 умеет генерировать preprocessed v2 без `legacy_nodes`;
- downstream stages нового формата не падают без `legacy_nodes`.

---

## 3.2. Ограничить legacy logic отдельным модулем совместимости

### Что сделать

Оставить весь старый экспорт и bridge logic в одном явно помеченном месте, например:
- `compat/legacy_export.py`
- `compat/legacy_preprocessed_utils.py`

### Что удалить

Удалить legacy helper'ы из основного happy path.

### Acceptance criteria

- legacy совместимость физически изолирована;
- core pipeline не импортирует legacy модули в нормальном пути выполнения.

---

## 3.3. После успешной миграции — удалить `legacy_export.py`

### Что сделать

После того как Stage 03 validator, Stage 04 postprocessor и Stage 02 local comparison будут переведены на units:
- удалить `01_preprocessor/legacy_export.py`;
- удалить соответствующие вызовы;
- удалить `legacy_nodes` из docs как активный стандарт.

### Preconditions

Удалять только после прохождения integration tests на новом формате.

---

# PHASE 4 — Сделать Stage 01 действительно multilingual

## 4.1. Начать использовать `language_code` в attachment policy

### Что сделать

Сейчас `language_code` передаётся в `decide_attachment(...)`, но не используется. Нужно ввести хотя бы минимальные профили.

### Рекомендуемая структура

- `attachment_profiles/base.py`
- `attachment_profiles/article_heavy.py`
- `attachment_profiles/postposition_particle.py`
- `attachment_profiles/rich_case.py`
- `attachment_profiles/analytic_min_morphology.py`

Или проще:
- `attachment_policy.py` + словарь language groups.

### Минимальные группы для старта

1. **Article-heavy Indo-European**
   - English, French, Italian, Portuguese, German, Danish, Norwegian
   - внимание к `det`, `aux`, `cop`, артиклям

2. **Slavic / rich inflection**
   - Russian, Czech, Belarusian, Bulgarian, Croatian
   - внимание к case-heavy noun modifiers и свободному порядку

3. **Finnic / rich local cases**
   - Finnish, Estonian
   - внимание к локативным case-маркерам и отсутствию нужды насильно attach-ить то, что уже закодировано в морфологии

4. **CJK / low morphology**
   - Chinese, Classical Chinese, Japanese, Korean
   - внимание к particles / function markers / segmentation artifacts

5. **Semitic**
   - Hebrew, Armenian partially separate if needed

### Acceptance criteria

- `language_code` реально влияет на attachment decisions хотя бы в нескольких правилах;
- есть документ с table-driven объяснением, какие профили на какие языки распространяются.

---

## 4.2. Ввести golden examples для нескольких языков

### Что сделать

Добавить небольшие вручную проверенные fixture-наборы минимум для:
- English
- Russian or Czech
- French or Italian
- Finnish or Estonian
- Chinese or Classical Chinese
- Japanese or Korean
- Hebrew or Armenian

### Проверять

- состав `units`;
- `span_token_ids`;
- `introduced_by`;
- `attached_tokens`;
- `surface`;
- `syntactic_link_target_id`.

### Acceptance criteria

- тесты явно фиксируют multilingual behavior;
- дальнейшие изменения policy нельзя делать вслепую.

---

## 4.3. Пересмотреть attach для determiner / auxiliary / copula

### Что сделать

Отдельно проверить, что:
- article languages не порождают лишние отдельные units для trivially attached determiners;
- при этом не ломается обратимость;
- auxiliary/copula attach не уничтожает важную предикативную структуру.

### Acceptance criteria

- attach decisions объяснимы и документированы;
- нет ощущения "русская логика просто натянута на все языки".

---

# PHASE 5 — Довести model layer до нормального состояния

## 5.1. Переименовать Stage 03

### Что сделать

Переименовать директорию и сущности из gemini-centric naming в model-neutral naming.

Рекомендуемо:
- `03_gemini_fix_errors` → `03_llm_annotation`
- `gemini_client_comp.py` → `providers/google_genai_client.py`
- `local_client.py` → `providers/local_http_client.py`

### Что удалить

Удалить из названий компонентов слово `gemini`, если компонент логически не привязан только к Gemini.

### Acceptance criteria

- названия отражают роль, а не историческую модель.

---

## 5.2. Убрать hardcoded model selection из клиента

### Что сделать

Сейчас model name забит прямо в клиенте. Это надо убрать.

Нужно:
- получать model name из config/settings;
- сохранять в output именно фактически использованную модель;
- не допускать рассинхрона между логами, config и фактическим вызовом.

### Что удалить

Удалить:
- локальную константу `MODEL_NAME = "gemini-flash-latest"` внутри клиента;
- любую схему, где client silently overrides config.

### Acceptance criteria

- один источник истины для имени модели;
- `model_name` в output соответствует реально вызванной модели.

---

## 5.3. Вынести prompt builder и schema builder

### Что сделать

Разделить:
- provider client,
- prompt assembly,
- response schema,
- relation ontology source.

### Что удалить

Удалить giant monolithic client file, в котором одновременно:
- transport;
- model selection;
- full prompt;
- schema enum.

### Acceptance criteria

- prompt можно менять отдельно от transport;
- schema relations берутся из общей онтологии, а не дублируются руками в нескольких местах.

---

# PHASE 6 — Упростить Stage 01 после миграции

## 6.1. Перевести `semantic_candidates_soft` в genuinely optional diagnostic layer

### Что сделать

После исправления heuristic engine и перевода validator/postprocessor на `units`, проверить, нужен ли `semantic_candidates_soft` вообще в production pipeline.

Возможные варианты:

#### Вариант A
Оставить только как debug output.

#### Вариант B
Включать только по флагу `ENABLE_SOFT_CANDIDATES=true`.

### Что удалить

Если soft candidates не участвуют в downstream — убрать их из default output, чтобы не засорять preprocessed JSON.

### Acceptance criteria

- проект не зависит от soft candidates для корректной работы;
- soft candidates не masquerade as authoritative data.

---

## 6.2. Удалить fallback-all по всем ролям из нормального режима

### Что сделать

Если soft candidates остаются, fallback-all должен быть только debug/diagnostic option.

### Что удалить

Удалить normal-path поведение:
- "если ничего не сработало, верни вообще все роли".

Потому что это превращает сигнал в шум и делает кандидаты бессмысленными.

### Acceptance criteria

- обычный pipeline не продуцирует giant all-relations candidate lists;
- пустой soft candidate list допустим и не считается аварией.

---

# PHASE 7 — Убрать технический мусор и сделать проект пригодным к долгой жизни

## 7.1. Убрать `sys.path.append(...)` и привести проект к нормальным imports

### Что сделать

Собрать проект как нормальный Python package или хотя бы consistent module layout.

### Что удалить

Удалить `sys.path.append(str(Path(__file__).parent.parent))` из postprocessor и других мест.

### Acceptance criteria

- запуск из корня работает без path hacks.

---

## 7.2. Убрать глобальные logging side effects на import

### Что сделать

Не конфигурировать logging при импорте модулей.
Сделать dedicated logger builder'ы, как уже частично сделано в validator/local generation.

### Что удалить

Удалить `logging.basicConfig(...)` в `01_preprocessor/processor.py` как import-time side effect.

### Acceptance criteria

- логирование не ломается от порядка импорта.

---

## 7.3. Добавить обязательные тесты migration-to-new-format

### Что сделать

Добавить тесты:
- schema v2 roundtrip;
- Stage 03 reads units without legacy;
- Stage 04 builds final dataset from units;
- validator works on units;
- attachment policy multilingual snapshots;
- heuristic condition matching = AND.

### Acceptance criteria

- есть тесты, которые доказывают, что legacy можно удалить без регресса.

---

# Порядок выполнения

## Шаг 1 — critical fixes
1. Исправить validator.
2. Исправить AND/OR bug в heuristics.
3. Добавить тесты на validator и heuristics.

## Шаг 2 — canonical migration
4. Перевести Stage 04 на units.
5. Перевести validator на units.
6. Перевести Stage 02 expected count на units.

## Шаг 3 — isolate legacy
7. Сделать `legacy_nodes` optional export.
8. Вынести legacy code в compat слой.
9. После прохождения тестов удалить legacy export из normal path.

## Шаг 4 — multilingual hardening
10. Реально использовать `language_code` в attachment policy.
11. Добавить multilingual fixtures и golden tests.
12. Пересмотреть det/aux/copula behavior.

## Шаг 5 — model layer cleanup
13. Переименовать Stage 03 в neutral naming.
14. Убрать hardcoded model selection.
15. Вынести prompt/schema builder.

## Шаг 6 — final cleanup
16. Удалить fallback-all из normal mode.
17. Сделать soft candidates optional.
18. Убрать sys.path hacks и import-time logging.

---

# Что можно удалять без сожалений

Если есть бэкап и цель — довести архитектуру до нормального состояния, можно смело удалять после миграции:

- жёсткую зависимость validator от `legacy_nodes`;
- проверку по `syntactic_link_candidates` как обязательное правило;
- `legacy_export.py` из normal path;
- `get_legacy_nodes()` из критического downstream;
- hardcoded model name в provider client;
- giant fallback-all candidate behavior;
- sys.path hacks;
- gemini-centric naming там, где компонент уже давно шире Gemini.

---

# Definition of Done

Работа считается завершённой, когда одновременно выполнены все пункты:

1. `units` — единственный canonical слой для Stage 03 и Stage 04.
2. validator больше не зависит от `legacy_nodes` и не имеет закомментированной логики.
3. heuristic matching работает по AND.
4. project pipeline работает без обязательного `legacy_nodes`.
5. `legacy_nodes` либо удалён, либо сведён к отдельному compat/export режиму.
6. Stage 03 model layer нейтрален по именованию и не hardcode'ит модель внутри клиента.
7. attachment policy реально использует `language_code`.
8. multilingual tests покрывают ключевые семейства языков.
9. финальный dataset собирается из нового формата без legacy bridge.
10. в репозитории не осталось мест, где старый слой silently определяет корректность новой системы.
