# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate(input_text = """INSERT_INPUT_HERE""", *, api_key: str | None = None, return_text: bool = False):
    client = genai.Client(
        api_key=api_key or os.environ.get("GEMINI_API_KEY"),
    )

    #MODEL_NAME = "gemini-flash-latest"
    #MODEL_NAME = "gemini-3-flash-preview"
    #MODEL_NAME = "gemini-3-pro-preview"
    #MODEL_NAME = "gemini-2.5-pro"
    #MODEL_NAME = "gemini-2.0-flash-001"
    #MODEL_NAME = "gemini-user-flash"
    #MODEL_NAME = "gemini-flash-lite-latest"

    model = "gemini-2.5-flash"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=""" Давай ты потренируешься на данном примере, виписывай исключительно как считаешь правильным и помни, что 
\"syntactic_link_target_id\" : null это всегда ROOT
{
  \"text\" : \"The prevalence of discrimination across racial groups in contemporary America:\",
  \"nodes\" : [ {
    \"id\" : \"w1\",
    \"name\" : \"The\",
    \"pos_universal\" : \"DET\",
    \"pos_specific\" : \"DT\",
    \"features\" : {
      \"Definite\" : \"Def\",
      \"PronType\" : \"Art\"
    },
    \"syntactic_link_target_id\" : \"w2\"
  }, {
    \"id\" : \"w2\",
    \"name\" : \"prevalence\",
    \"pos_universal\" : \"NOUN\",
    \"pos_specific\" : \"NN\",
    \"features\" : {
      \"Number\" : \"Sing\"
    },
    \"syntactic_link_target_id\" : null
  }, {
    \"id\" : \"w4\",
    \"name\" : \"of_discrimination\",
    \"pos_universal\" : \"NOUN\",
    \"pos_specific\" : \"NN\",
    \"features\" : {
      \"Number\" : \"Sing\"
    },
    \"syntactic_link_target_id\" : \"w2\"
  }, {
    \"id\" : \"w6\",
    \"name\" : \"racial\",
    \"pos_universal\" : \"ADJ\",
    \"pos_specific\" : \"JJ\",
    \"features\" : {
      \"Degree\" : \"Pos\"
    },
    \"syntactic_link_target_id\" : \"w7\"
  }, {
    \"id\" : \"w7\",
    \"name\" : \"across_groups\",
    \"pos_universal\" : \"NOUN\",
    \"pos_specific\" : \"NNS\",
    \"features\" : {
      \"Number\" : \"Plur\"
    },
    \"syntactic_link_target_id\" : \"w2\"
  }, {
    \"id\" : \"w9\",
    \"name\" : \"contemporary\",
    \"pos_universal\" : \"ADJ\",
    \"pos_specific\" : \"JJ\",
    \"features\" : {
      \"Degree\" : \"Pos\"
    },
    \"syntactic_link_target_id\" : \"w10\"
  }, {
    \"id\" : \"w10\",
    \"name\" : \"in_America\",
    \"pos_universal\" : \"PROPN\",
    \"pos_specific\" : \"NNP\",
    \"features\" : {
      \"Number\" : \"Sing\"
    },
    \"syntactic_link_target_id\" : \"w2\"
  } ]
}"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""**Analyzing Discrimination Prevalence**

I'm currently dissecting the sentence \"The prevalence of discrimination across racial groups in contemporary America.\" My focus is on the prevalence aspect, using it as the root of the analysis. I'm building a dependency structure. The word \"prevalence\" is the root node of the parse tree.


**Defining Prevalence Scope**

I've been mapping the connections between key terms to understand the context of \"prevalence\". The word \"racial\" is linked to \"across groups,\" which, in turn, relates back to prevalence. Additionally, \"contemporary\" and \"in America\" also connect with the word prevalence. I'm focusing on \"The\" as a determinant of \"prevalence,\" its specific qualifying role in describing the sentence.


**Clarifying Contextual Relationships**

I'm now zeroing in on the relationships between the terms. Specifically, I see \"discrimination\" acts as the central content or theme of \"prevalence\". The word \"racial,\" also acts as a quality, linked to the groups, while \"across racial groups\" points towards a spatial distribution or range, as well. I'm checking the classification.


**Interpreting \"Across\" Usage**

I'm presently focusing on \"across\" within \"across racial groups.\" It seems to imply a transverse distribution of prevalence. I've considered that the word \"across\" functions as \"transverse\" when used across something. For instance, the phrase \"He walked across the square\" suggests movement over a surface. Similarly, \"across racial groups\" suggests that prevalence exists transversely across the groups.


**Refining Word Relationships**

I'm now revisiting the relationships between the words. I've reclassified \"In America\" as \"Inclusion_Containment\" because it defines the spatial context of the prevalence. I'm focusing on \"The\" as \"Quality\". I am considering that \"across\" could also denote \"Distribution over an area\". I will continue the JSON format.


**Categorizing \"Across\" Usage**

I'm solidifying the categorization of \"across\" within the phrase. I've cross-referenced its usage across multiple sections to pinpoint \"Crossing_Transverse\" as the most appropriate category for the context. This links it to where the prevalence exists. I've also re-examined the relationship of \"prevalence *of* discrimination\" determining that \"Content_Theme\" is accurate.


**Revisiting Term Relationships**

I'm now refining the classifications. I've reassessed \"in contemporary America\" as Inclusion_Containment, correctly pinpointing \"America\" as the container for the prevalence. I'm revisiting \"across,\" considering Distribution_over_an_area to capture the sense of prevalence spread throughout the groups, and I'm re-validating the determiner \"The\" as Quality, recognizing it as a functional property in the context. I'm now cross-validating the prior classifications with a new resource.


"""),
                types.Part.from_text(text="""{
  \"nodes\": [
    {
      \"id\": \"w1\",
      \"syntactic_link_name\": \"Quality\"
    },
    {
      \"id\": \"w2\",
      \"syntactic_link_name\": \"ROOT\"
    },
    {
      \"id\": \"w4\",
      \"syntactic_link_name\": \"Content_Theme\"
    },
    {
      \"id\": \"w6\",
      \"syntactic_link_name\": \"Quality\"
    },
    {
      \"id\": \"w7\",
      \"syntactic_link_name\": \"Crossing_Transverse\"
    },
    {
      \"id\": \"w9\",
      \"syntactic_link_name\": \"Quality\"
    },
    {
      \"id\": \"w10\",
      \"syntactic_link_name\": \"Inclusion_Containment\"
    }
  ]
}"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=input_text),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
        ),
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            properties = {
                "nodes": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        properties = {
                            "id": genai.types.Schema(
                                type = genai.types.Type.STRING,
                            ),
                            "syntactic_link_name": genai.types.Schema(
                                type = genai.types.Type.STRING,
                                enum = ["Agent", "Patient", "Recipient", "Instrument", "Inclusion_Containment", "Exteriority", "Support", "Subjacency", "Covering_Superadjacency", "Proximity", "Contact_Adjacency", "Attachment", "Front_Region", "Posterior_Region_Behind", "Intermediacy", "Opposition_Across_from", "Alignment_Alongness", "Circumference_Encirclement", "Crossing_Transverse", "Lateral_Beside", "Functional_Proximity", "Source_as_Origin", "Egress_Exiting_an_Interior", "Separation_from_a_Surface", "Departure_from_a_Landmark", "Emergence_from_below", "Descent_from_a_high_point", "Ascent_to_a_high_point", "Detachment", "Egress_from_an_intermediate_position", "Emergence_from_behind_an_obstacle", "Goal_as_Recipient", "Distribution_over_an_area", "Ingress_Entering_an_Interior", "Attaining_a_Surface", "Approaching_a_Landmark", "Attachment_Connection", "Reaching_a_lower_position", "Reaching_the_other_side_Crossing", "Movement_to_a_posterior_region", "Entering_an_intermediate_position", "Penetration", "Transverse", "Alignment", "Bypass", "Circumvention", "Vertical_path", "Superlative_Sublative", "Interlative", "Reaching_an_abstract_goal_state", "Metaphorical_Path", "Finality", "Acquisition", "Numeric", "Quantitative_Large", "Quantitative_Small", "Collective_Relation", "Approximative_Relation", "Proportional_Fractional_Relation", "Metric_Measuring_Relation", "Duration", "Point_in_Time", "Frequency", "Terminus_ad_quem_Deadline", "Prospective_Starting_point", "Quality", "Possession", "Content_Theme", "Addition_Conjunction", "Disjunction", "Contrast", "Juxtaposition", "Concession", "Alternative", "Clarification", "Sequence_in_time_before", "Sequence_in_time_after", "Sequence_in_time_while", "Reason_because", "Result_since", "Result_because", "Goal", "Condition", "Comparison", "Specification_which", "Specification_that_is", "Exception", "Addition", "ROOT"],
                            ),
                        },
                    ),
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""РОЛЬ
Ты — эксперт-лингвист, специализирующийся на семантическом анализе текста. Твоя задача — точно определять семантические отношения между словами в предложении, основываясь на предоставленной классификации а также вносить исправления и проверять качество выполненной работы.
ИНСТРУКЦИЯ
Тебе будет предоставлена полная классификация семантических связей с определениями и примерами. Внимательно изучи и запомни её. Это твой единственный источник истины. Не используй никакие другие классификации или внешние знания.
КЛАССИФИКАЦИЯ СЕМАНТИЧЕСКИХ СВЯЗЕЙ
--- START OF CLASSIFICATION ---
I. Тематические роли (участники ситуации):
    1. Агенс (Agent): Одушевлённый и сознательный инициатор действия, контролирующий его. Ключевые признаки: воля, контроль, намерение.
        ◦ Пример: Мальчик бросил мяч.
    2. Пациенс (Patient): Участник, который подвергается действию и в результате изменяет своё состояние (физическое или качественное). Ключевые признаки: изменение состояния, отсутствие контроля.
        ◦ Пример: Ребёнок сломал игрушку.
    3. Реципиент (Recipient): Одушевлённый получатель объекта, блага или информации; конечная точка передачи.
        ◦ Пример: Сестре подарили цветы.
    4. Инструмент (Instrument): Неодушевлённый объект, используемый агенсом как средство или орудие для выполнения действия.
        ◦ Пример: Дверь открыли ключом.
II. Статические пространственные отношения (локализация):
    1. Включение (Inclusion): Объект А находится внутри объёмного объекта-контейнера Б.
        ◦ Пример: Ключи лежат в ящике.
    2. Нахождение снаружи (Exteriority): Объект А находится за пределами границ объекта Б. Является антонимом включения.
        ◦ Пример: Собака ждёт за дверью.
    3. Опора (Support): Объект А находится на поверхности объекта Б, который служит ему опорой, противодействуя силе тяжести. Ключевой признак — контакт с поддерживающей поверхностью.
        ◦ Пример: Книга лежит на полке.
    4. Нахождение под (Subjacency): Объект А расположен ниже объекта Б по вертикали. Физический контакт не обязателен.
        ◦ Пример: Тапочки стоят под кроватью.
    5. Нахождение над (Covering / Superadjacency): Объект А расположен выше объекта Б, часто покрывая или перекрывая его. Контакт не обязателен.
        ◦ Пример: Мост висит над рекой.
    6. Близость / Смежность (Proximity): Объект А находится рядом с объектом Б, но без физического контакта.
        ◦ Пример: Он сидел у окна.
    7. Примыкание (Contact / Adjacency): Объекты А и Б находятся в непосредственном физическом соприкосновении, но без функции опоры или включения.
        ◦ Пример: Лестница прислонена к дому.
    8. Прикрепление (Attachment): Объект А прочно и функционально соединён с объектом Б (прикручен, приклеен, встроен), часто являясь его частью.
        ◦ Пример: Датчик прикреплён к корпусу.
    9. Нахождение спереди (Front Region): Объект А расположен в зоне перед \\\"лицевой\\\" или главной стороной объекта Б.
        ◦ Пример: Автобус остановился перед светофором.
    10. Нахождение сзади (Posterior Region / Behind): Объект А расположен в зоне за \\\"тыльной\\\" стороной объекта Б, часто будучи скрытым от взгляда спереди.
        ◦ Пример: Он спрятался за колонной.
    11. Нахождение между (Intermediacy): Объект А расположен в пространстве, ограниченном двумя другими объектами (Б и В).
        ◦ Пример: Кафе находится между банком и аптекой.
    12. Противоположное положение (Opposition / Across from): Объекты А и Б находятся по разные стороны от разделяющего их пространства (улицы, реки, стола), часто будучи обращёнными друг к другу.
        ◦ Пример: Его дом стоит напротив нашего.
    13. Расположение вдоль (Alignment / Alongness): Объект А (или ряд объектов) вытянут параллельно линейному ориентиру Б (дороге, реке, стене).
        ◦ Пример: Деревья растут вдоль дороги.
    14. Окружение (Circumference / Encirclement): Объект А (единый или множество) расположен по периметру объекта Б, охватывая его снаружи.
        ◦ Пример: Толпа сомкнулась вокруг артиста.
    15. Пересечение (Crossing / Transverse): Протяжённый объект А лежит поперёк другого протяжённого объекта Б, пересекая его под углом.
        ◦ Пример: Упавшее дерево лежит поперёк дороги.
    16. Сбоку (Lateral / Beside): Объект А расположен у боковой стороны объекта Б (не спереди и не сзади).
        ◦ Пример: Пристройка находится сбоку от основного здания.
    17. Функциональное соседство (Functional Proximity): Объект А связан с объектом Б не физически, а в силу институциональной, социальной или функциональной принадлежности.
        ◦ Пример: Врач при школе.
III. Динамические отношения: Движение ИЗ исходной точки (Source)
    1. Происхождение (Source as Origin): Объект А возникает, происходит или берет начало из источника Б (место, человек, информация). Фокус на генерации, а не простом перемещении.
        ◦ Пример: Новость поступила от корреспондента.
    2. Выход из внутреннего пространства (Egress): Движение объекта А изнутри контейнера Б наружу. Динамический аналог Включения (#5).
        ◦ Пример: Он вытащил документы из папки.
    3. Отделение от поверхности (Separation from a Surface): Движение объекта А, начинающееся с поверхности-опоры Б. Динамический аналог Опоры (#7).
        ◦ Пример: Ветер сдул бумагу со стола.
    4. Отдаление от ориентира (Departure from a Landmark): Движение объекта А от точки, находящейся рядом с ориентиром Б, с увеличением дистанции. Динамический аналог Близости (#10).
        ◦ Пример: Поезд отошёл от станции.
    5. Движение из-под объекта (Emergence from below): Движение объекта А из-под укрывающего его объекта Б. Динамический аналог Нахождения под (#8).
        ◦ Пример: Змея выскользнула из-под камня.
    6. Спуск (Descent from a high point): Движение объекта А вниз с возвышенности Б (гора, дерево, крыша).
        ◦ Пример: Кошка слезла с дерева.
    7. Подъём (Ascent to a high point): Движение объекта А вверх на возвышенность Б. Является противоположностью Спуска (#27).
        ◦ Пример: Альпинисты поднялись на вершину.
    8. Открепление (Detachment): Разрыв прочной функциональной связи между объектом А и объектом Б. Динамический аналог Прикрепления (#12).
        ◦ Пример: Пуговица оторвалась от рубашки.
    9. Движение из промежутка (Egress from an intermediate position): Движение А из пространства, ограниченного двумя ориентирами Б и В. Динамический аналог Нахождения между (#15).
        ◦ Пример: Корабль вышел из пролива между утёсами.
    10. Появление из-за препятствия (Emergence from behind an obstacle): Движение А из-за скрывающего его объекта Б в поле зрения наблюдателя. Динамический аналог Нахождения сзади (#14).
        ◦ Пример: Солнце показалось из-за горы.
IV. Динамические отношения: Движение К конечной точке (Goal/Path)
    1. Цель как получатель (Goal as Recipient): Движение объекта А к одушевлённому получателю Б. Динамический аналог Реципиента (#3).
        ◦ Пример: Учитель раздал тетради ученикам.
    2. Распределение по площади (Distribution over an area): Движение массы или множества объектов А с их последующим распространением по поверхности Б.
        ◦ Пример: Пыль осела на мебель.
    3. Вхождение во внутреннее пространство (Ingress): Движение объекта А снаружи внутрь контейнера Б. Противоположность Выхода (#23).
        ◦ Пример: Он положил телефон в сумку.
    4. Достижение поверхности (Attaining a Surface): Движение объекта А, завершающееся контактом с поверхностью-опорой Б. Противоположность Отделения (#24).
        ◦ Пример: Он положил ключи на стол.
    5. Приближение к ориентиру (Approaching a Landmark): Движение объекта А в сторону ориентира Б с сокращением дистанции. Противоположность Отдаления (#25).
        ◦ Пример: Корабль приближается к острову.
    6. Прикрепление (Attachment / Connection): Действие, в результате которого устанавливается прочная связь между А и Б. Противоположность Открепления (#29).
        ◦ Пример: Магнит прилип к холодильнику.
    7. Достижение нижней части (Reaching a lower position): Движение объекта А в пространство под объектом Б. Противоположность Движения из-под (#26).
        ◦ Пример: Ребёнок пролез под забором.
    8. Достижение противоположной стороны / Пересечение (Reaching the other side / Crossing): Движение А через протяжённый ориентир Б (реку, дорогу) с целью оказаться на другой стороне.
        ◦ Пример: Они построили мост через реку.
    9. Движение за объект (Movement to a posterior region): Движение А в пространство позади ориентира Б, часто с целью скрыться. Противоположность Появления из-за (#31).
        ◦ Пример: Ребёнок спрятался за штору.
    10. Вхождение в промежуток (Entering an intermediate position): Движение А в пространство между двумя ориентирами Б и В. Противоположность Движения из промежутка (#30).
        ◦ Пример: Он вклинился между двумя группами.
V. Динамические отношения: Траектория движения (Path)
    1. Прохождение сквозь среду / Пенетрация (Penetration): Движение А внутри трёхмерной среды Б (лес, толпа, туман), которая его окружает.
        ◦ Пример: Он пробился сквозь толпу.
    2. Пересечение поверхности / Трансверсив (Transverse): Движение А поперёк двумерной поверхности Б (поле, площадь).
        ◦ Пример: Машина проехала через площадь.
    3. Движение вдоль ориентира / Алингмент (Alignment): Движение А параллельно протяжённому ориентиру Б (дорога, река). Динамический аналог Расположения вдоль (#17).
        ◦ Пример: Корабль плывёт вдоль побережья.
    4. Движение мимо ориентира / Байпас (Bypass): Движение А вблизи ориентира Б, но без остановки или взаимодействия.
        ◦ Пример: Мы проехали мимо старого моста.
    5. Движение вокруг ориентира / Циркумвенция (Circumvention): Криволинейное движение А, огибающее или вращающееся вокруг центрального объекта Б. Динамический аналог Окружения (#18).
        ◦ Пример: Машины движутся вокруг кольцевой развязки.
    6. Движение по вертикали (Vertical path): Движение А вверх или вниз вдоль вертикальной/наклонной структуры Б (лестница, склон).
        ◦ Пример: Лыжник съехал вниз по склону.
    7. Движение над/под ориентиром (Superlative/Sublative): Движение А выше (над) или ниже (под) ориентира Б без контакта.
        ◦ Пример: Лодка проплыла под мостом.
    8. Движение между ориентирами (Interlative): Движение А через узкий \\\"коридор\\\", образованный ориентирами Б и В.
        ◦ Пример: Поезд прошёл между тоннелем и обрывом.
VI. Абстрактные и метафорические отношения
    1. Достижение абстрактной цели / Состояния (Reaching an abstract goal): Метафорическое \\\"движение\\\" к состоянию, уровню или пределу (температура, цена, статус).
        ◦ Пример: Цена упала до десяти долларов.
    2. Метафорический путь (Metaphorical Path): Описание непространственного процесса (жизненный этап, процедура) в терминах движения (\\\"пройти через\\\", \\\"быть на полпути\\\").
        ◦ Пример: Он переживает (проходит через) трудный период.
    3. Цель-действие (Finality): Действие-средство совершается для того, чтобы выполнить другое действие-цель.
        ◦ Пример: Он учит английский, чтобы поступить в университет.
    4. Цель-объект (Acquisition): Действие совершается ради получения или достижения объекта-цели.
        ◦ Пример: Она вернулась за своими вещами.
VII. Количественные отношения
    1. Точное количество (Numeric): Указание точного числа (количественного или порядкового).
        ◦ Пример: Тридцать два ученика; седьмое ноября.
    2. Неопределённое большое количество (Quantitative): Указание большого, но неточного количества (\\\"много\\\", \\\"множество\\\").
        ◦ Пример: Много времени.
    3. Неопределённое малое количество (Quantitative): Указание малого, но неточного количества (\\\"мало\\\", \\\"несколько\\\", \\\"немного\\\").
        ◦ Пример: Несколько вопросов.
    4. Совокупное (коллективное) отношение (Collective Relation): Использование специального слова для обозначения группы как единого целого.
        ◦ Пример: Стадо оленей.
    5. Аппроксимативное (Приблизительное) отношение (Approximative Relation): Указание приблизительного количества (\\\"около\\\", \\\"примерно\\\").
        ◦ Пример: Человек десять собрались у входа.
    6. Пропорциональное (Дробное) отношение (Proportional / Fractional Relation): Указание части от целого в виде дроби или процента.
        ◦ Пример: Половина времени.
    7. Метрическое (Измерительное) отношение (Metric / Measuring Relation): Использование стандартной единицы для измерения неисчисляемой сущности.
        ◦ Пример: Килограмм сахара.
VIII. Временные отношения
    1. Длительность (Duration): Протяжённость события во времени (ответ на вопрос \\\"как долго?\\\").
        ◦ Пример: Он молчал в течение долгого времени.
    2. Темпоральная локализация (Point in Time): Привязка события к конкретной точке или периоду времени (ответ на вопрос \\\"когда?\\\").
        ◦ Пример: Встреча начнётся в полдень.
    3. Частотность / повторяемость (Frequency): Как часто происходит событие.
        ◦ Пример: Они ходят в спортзал три раза в неделю.
    4. Предельное отношение (Terminus ad quem / \\\"Deadline\\\"): Крайний срок, до которого должно произойти событие.
        ◦ Пример: Вы должны покинуть номер до 12:00.
    5. Начальное отношение (Prospective/Starting point): Точка отсчёта, относительно которой описываются другие события.
        ◦ Пример: После её ухода атмосфера изменилась.
IX. Атрибутивные и логические отношения
    1. Качественное отношение (Quality): Приписывание объекту свойства или характеристики.
        ◦ Пример: Острый нож.
    2. Посессивное отношение (Possession): Отношение принадлежности, владения.
        ◦ Пример: Политика компании.
    3. Отношение содержания / темы (Content/Theme): Указание темы или содержания информационного объекта.
        ◦ Пример: Роман о любви.
    4. Соединительная связь (Addition / Conjunction): Объединение равноправных фактов или событий (союз \\\"и\\\").
        ◦ Пример: Солнце светит, и птицы поют.
    5. Разделительная связь (Disjunction): Представление альтернатив или взаимоисключающих вариантов (союз \\\"или\\\").
        ◦ Пример: Вы можете повернуть налево или ехать прямо.

Связи между простыми частями предложения

I. Противительные и сопоставительные отношения
    1. Контраст (Contrast): Выражает сопоставление двух фактов, которые существуют одновременно, но различаются («А, а Б»).
        ◦ Пример: Я люблю кофе, а она пьёт только чай.
    2. Противопоставление (Juxtaposition): Явно отрицает первый факт («не А») и утверждает второй, альтернативный факт («а Б») как истинный.
        ◦ Пример: Это не ошибка, а закономерный результат.
    3. Уступка (Concession): Указывает, что второй факт (Б) происходит вопреки первому (А), который должен был бы ему помешать.
        ◦ Пример: Хотя погода была плохой, мероприятие прошло успешно.
    4. Альтернатива / Разделительная связь (Alternative / Disjunction): Выражает выбор, взаимоисключение или перечисление нескольких возможных вариантов («А или Б»).
        ◦ Пример: Мы можем поехать на поезде или взять машину.
II. Изъяснительные и конкретизирующие отношения
    1. Изъяснение (Clarification): Придаточное предложение раскрывает содержание действия (речи, мысли, чувства), выраженного в главной части («сказал, что...»).
        ◦ Пример: Он сказал, что не сможет прийти.
    2. Конкретизация - которое (Specification - which): Придаточное предложение определяет или уточняет конкретное существительное из главной части.
        ◦ Пример: Я нашёл ключ, который потерял вчера.
    3. Конкретизация - то есть (Specification - that is): Вторая часть предложения поясняет или переформулирует смысл первой.
        ◦ Пример: Он страдает амнезией, то есть полностью потерял память.
III. Временные отношения
    1. Последовательность во времени - перед (Sequence - before): Одно действие (А) происходит раньше другого (Б).
        ◦ Пример: Перед тем как выйти, я проверил замок.
    2. Последовательность во времени - после (Sequence - after): Одно действие (А) происходит позже другого (Б).
        ◦ Пример: После того как закончился дождь, мы вышли на улицу.
    3. Последовательность во времени - вместе с (Sequence - while): Два действия происходят одновременно, параллельно.
        ◦ Пример: Дети играли, пока родители готовили ужин.
IV. Причинно-следственные, целевые и условные отношения
    1. Причина - потому что (Reason - because): Следствие («А») объясняется причиной («Б»). Структура: [Следствие], потому что [Причина].
        ◦ Пример: Она не пошла на работу, потому что заболела.
    2. Результат - так как (Result - since): Причина («А») предшествует следствию («Б»). Структура: Так как [Причина], то [Следствие].
        ◦ Пример: Поскольку студент не подготовился, то он не сдал экзамен.
    3. Результат - так как (Result - because): Аналогично связи #9, но с использованием союза \\\"так как\\\". Структура: [Следствие], так как [Причина].
        ◦ Пример: Мы отменили пикник, так как начался дождь.
    4. Цель (Goal): Действие («А») совершается для достижения желаемого результата («Б»).
        ◦ Пример: Я пришёл, чтобы помочь тебе.
    5. Условие (Condition): Выполнение следствия («Б») зависит от выполнения условия («А»).
        ◦ Пример: Если будет солнечно, мы поедем за город.
V. Другие логические отношения
    1. Сравнение (Comparison): Сопоставление двух объектов или явлений по какому-либо признаку.
        ◦ Пример: Маша выше, чем её сестра.
    2. Исключение (Exception): Выделение элемента, который не подпадает под общее утверждение.
        ◦ Пример: Все ученики пришли на урок, кроме Марии.
    3. Добавление (Addition): Расширение или дополнение основной информации путем включения нового элемента.
        ◦ Пример: Все участники, включая новичков, получили сертификаты.

--- END OF CLASSIFICATION ---
ПРАВИЛА РАБОТЫ
\"syntactic_link_target_id\" : null это всегда ROOT
ВСЕ неясные для тебя обозначения во входных данных взяты из Universal Dependencies
Выбор связи: Для каждого слова (узла) в JSON тебе нужно будет выбрать ОДНУ наиболее подходящую семантическую связь, ты можешь посмотреть на поле \"link\" конкретного узла и СОГЛАСИТЬСЯ или ИСПРАВИТЬ. Твой выбор должен строго основываться на определениях из КЛАССИФИКАЦИИ.
Если ты получил ПУСТОЙ список, значит предложение 
Обработка корневого элемента: Если у узла syntactic_link_target_id равен null, это корневой элемент предложения. Для него всегда следует выбирать связь ROOT.
Правило разрешения неоднозначности: Если тебе кажется, что ни один из предложенных кандидатов идеально не подходит, или несколько подходят в равной степени, выбери первого кандидата в списке. Это обеспечит стабильность разметки.
Правило разумности - не бойся выбирать свой вариант если он покажется тебе наиболее подходящим.
Формат ответа: Твой ответ должен быть только JSON-массивом объектов. Каждый объект должен содержать только два поля: \\\"id\\\" и \\\"syntactic_link_name\\\". Не добавляй никаких комментариев, объяснений или текста вне структуры JSON."""),
        ],
    )

    chunks: list[str] = []
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        text = chunk.text or ""
        if return_text:
            chunks.append(text)
        else:
            print(text, end="")

    if return_text:
        return "".join(chunks)

if __name__ == "__main__":
    generate("Тестовое сообщение")
