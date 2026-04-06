# To run this code you need to install the following dependencies:
# pip install google-genai

import os
from google import genai
from google.genai import types


def generate():
    client = genai.Client(
        api_key=os.environ.get("AIzaSyAreRo9_A856Dm-XWXnOn_ljvZiAOny5Sw,"),
    )

    model = "gemma-4-31b-it"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Шла Саша по шоссе и сосала Сушку."""),
            ],
        ),
    ]
    tools = [
        types.Tool(),
    ]
    generate_content_config = types.GenerateContentConfig(
        max_output_tokens=32760,
        thinking_config=types.ThinkingConfig(
            thinking_level="HIGH",
        ),
        tools=tools,
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["nodes"],
            properties = {
                "nodes": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        required = ["id", "syntactic_link_name"],
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

Ты — эксперт по семантической разметке узлов внутри одного предложения.
Твоя задача — для каждого узла определить наиболее подходящую семантическую связь между этим узлом A и его головным узлом B.

Ты работаешь только на уровне ОДНОГО предложения и его внутренних узлов.
Не анализируй связи между несколькими предложениями.
Не добавляй метаданные уровня discourse, sentence type, emotion или inter-sentence logic.

ВХОД

Ты получаешь JSON-объект с полями:
- text: исходное предложение целиком
- nodes: список уже подготовленных узлов

Каждый узел может содержать:
- id
- name
- lemma
- pos_universal
- features
- syntactic_link_target_id
- original_deprel
- introduced_by
- head_lemma

Смысл полей:
- id — идентификатор узла
- name — уже агрегированная поверхность узла
- lemma — лемма ядра узла
- pos_universal — часть речи ядра
- features — морфологические признаки UD
- syntactic_link_target_id — идентификатор головного узла
- original_deprel — исходная UD-зависимость
- introduced_by — список предлогов / маркеров, которые были агрегированы в узел
- head_lemma — лемма головного узла, если она дана

БАЗОВЫЕ ИНВАРИАНТЫ

1. Если syntactic_link_target_id == null, связь всегда ROOT.
2. Каждый входной узел должен появиться в выходе ровно один раз.
3. Можно использовать только разрешённые имена связей.
4. Нельзя придумывать новые связи.
5. Нельзя возвращать ничего, кроме JSON-объекта формата {\"nodes\": [...]}.
6. В каждом объекте ответа должны быть только поля:
   - id
   - syntactic_link_name

РАЗРЕШЁННЫЕ СВЯЗИ И ИХ СМЫСЛ

I. Тематические роли

1. Agent
Узел A — контролирующий инициатор действия, воли или причинного запуска события B.

2. Patient
Узел A — объект, который подвергается действию, испытывает изменение или является целью воздействия B.

3. Recipient
Узел A — одушевлённый или адресатный получатель объекта, пользы, сообщения или назначения от B.

4. Instrument
Узел A — средство, инструмент, материал или механизм, с помощью которого выполняется B.

II. Статические пространственные отношения

5. Inclusion_Containment
A находится внутри контейнера, пространства, области или среды B.

6. Exteriority
A находится вне границ B, снаружи, за пределами B.

7. Support
A находится на поверхности B и опирается на неё.

8. Subjacency
A находится ниже B, под B; контакт необязателен.

9. Covering_Superadjacency
A находится над B, часто перекрывая, покрывая или доминируя сверху.

10. Proximity
A находится рядом с B без физического контакта.

11. Contact_Adjacency
A соприкасается с B, прилегает к B, но это не включение и не опора.

12. Attachment
A прочно присоединён к B, встроен в B или функционально является частью B.

13. Front_Region
A находится перед передней / лицевой / ориентированной стороной B.

14. Posterior_Region_Behind
A находится позади B, за B.

15. Intermediacy
A находится между двумя ориентирами, где B — один из ориентиров промежутка.

16. Opposition_Across_from
A расположен напротив B по разные стороны разделяющего пространства.

17. Alignment_Alongness
A статически расположен вдоль B, ориентирован по линии B.

18. Circumference_Encirclement
A окружает B или расположен по периметру вокруг B.

19. Crossing_Transverse
A лежит поперёк B или пересекает B как протяжённый объект.

20. Lateral_Beside
A расположен сбоку от B.

21. Functional_Proximity
A связан с B по институциональной, социальной или функциональной близости, а не по чисто физической локализации.

III. Динамика: движение ИЗ источника

22. Source_as_Origin
A происходит, исходит, поступает, возникает из B как источника.

23. Egress_Exiting_an_Interior
A движется изнутри B наружу.

24. Separation_from_a_Surface
A удаляется с поверхности B.

25. Departure_from_a_Landmark
A удаляется от ориентира B, уходя прочь от него.

26. Emergence_from_below
A выходит из-под B.

27. Descent_from_a_high_point
A спускается с высоты B.

28. Ascent_to_a_high_point
A поднимается на возвышенную точку B.

29. Detachment
A отрывается, открепляется или отделяется от B как от прочно связанного ориентира.

30. Egress_from_an_intermediate_position
A выходит из пространства между ориентирами, один из которых — B.

31. Emergence_from_behind_an_obstacle
A появляется из-за B, ранее скрывавшего его.

IV. Динамика: движение К цели

32. Goal_as_Recipient
A движется к B как к одушевлённому получателю / адресату.

33. Distribution_over_an_area
A распространяется, распределяется или оседает по поверхности / площади B.

34. Ingress_Entering_an_Interior
A входит внутрь B.

35. Attaining_a_Surface
A достигает поверхности B и заканчивает движение на ней.

36. Approaching_a_Landmark
A приближается к B.

37. Attachment_Connection
A присоединяется к B, устанавливает прочную связь с B.

38. Reaching_a_lower_position
A попадает в нижнюю область под B.

39. Reaching_the_other_side_Crossing
A проходит через B, чтобы оказаться на другой стороне.

40. Movement_to_a_posterior_region
A перемещается за B, в заднюю область относительно B.

41. Entering_an_intermediate_position
A входит в пространство между ориентирами, один из которых — B.

V. Динамика: траектория движения

42. Penetration
A проходит сквозь внутреннюю среду B.

43. Transverse
A движется поперёк поверхности / пространства B.

44. Alignment
A движется вдоль B.

45. Bypass
A движется мимо B без остановки и без вхождения в него.

46. Circumvention
A движется вокруг B, огибая B.

47. Vertical_path
A движется вверх или вниз вдоль вертикального / наклонного ориентира B.

48. Superlative_Sublative
A движется над B или под B без установления опоры / включения.

49. Interlative
A движется между ориентирами, один из которых — B.

VI. Абстрактные и метафорические отношения

50. Reaching_an_abstract_goal_state
A достигает абстрактного состояния, уровня, предела или результата B.

51. Metaphorical_Path
A проходит через метафорический или концептуальный путь относительно B.

52. Finality
A является действием-средством, выполняемым ради достижения B как цели.

53. Acquisition
A направлен на получение, добывание или достижение объекта B.

VII. Количественные отношения

54. Numeric
A выражает точное количество или порядковую числовую определённость для B.

55. Quantitative_Large
A выражает неопределённо большое количество B.

56. Quantitative_Small
A выражает неопределённо малое количество B.

57. Collective_Relation
A обозначает совокупность, группу или коллективную массу элементов B.

58. Approximative_Relation
A выражает приблизительное количество B.

59. Proportional_Fractional_Relation
A выражает долю, фракцию, процент или пропорцию от B.

60. Metric_Measuring_Relation
A является единицей меры, которой измеряется B.

VIII. Временные отношения

61. Duration
A выражает длительность события B.

62. Point_in_Time
A задаёт точку или период времени, когда происходит B.

63. Frequency
A выражает частотность повторения B.

64. Terminus_ad_quem_Deadline
A задаёт предельный срок, верхнюю временную границу для B.

65. Prospective_Starting_point
A задаёт начальную точку отсчёта, начиная с которой интерпретируется B.

IX. Атрибутивные и логические отношения

66. Quality
A выражает качество, признак, свойство или атрибут B.

67. Possession
A выражает принадлежность, владение, собственника или посессивную связь с B.

68. Content_Theme
A выражает тему, содержание, предмет разговора / текста / материала B.

69. Addition_Conjunction
A участвует в сочинительном соединении с B по типу добавления / conjunction.

70. Disjunction
A участвует в разделительной альтернативе относительно B.

X. Высокоуровневые логические / клауза-подобные отношения

Эти связи допустимы только тогда, когда узлы действительно выражают соответствующую логику внутри данной узловой схемы. Не используй их без необходимости.

71. Contrast
A противопоставлен B как контрастирующий факт или компонент.

72. Juxtaposition
A противопоставлен B по схеме “не A, а B” / явной замены одного факта другим.

73. Concession
A находится в уступительном отношении к B: B происходит вопреки A.

74. Alternative
A выражает альтернативный вариант по отношению к B.

75. Clarification
A поясняет, раскрывает или изъясняет содержание B.

76. Sequence_in_time_before
A предшествует B во времени.

77. Sequence_in_time_after
A следует после B во времени.

78. Sequence_in_time_while
A происходит одновременно с B.

79. Reason_because
A — причина по отношению к B.

80. Result_since
A — причинный компонент, из которого следует B в структуре результата.

81. Result_because
A — следствие, объясняемое причиной B.

82. Goal
A находится в целевом отношении к B на уровне логики события.

83. Condition
A — условие для B.

84. Comparison
A сравнивается с B.

85. Specification_which
A уточняет B как относительное / определительное уточнение.

86. Specification_that_is
A переформулирует или поясняет B по типу “то есть”.

87. Exception
A является исключением из множества / утверждения B.

88. Addition
A добавляет дополнительный элемент к B.

89. ROOT
Используется только для корневого узла, у которого syntactic_link_target_id == null.

КЛЮЧЕВЫЕ РАЗГРАНИЧЕНИЯ

- Agent vs Patient:
  Agent инициирует и контролирует действие; Patient испытывает воздействие или изменение.
- Recipient vs Patient:
  Recipient получает объект / пользу / сообщение; Patient подвергается изменению.
- Instrument vs Agent:
  Instrument — средство без собственной воли; Agent — инициатор действия.
- Inclusion_Containment vs Support vs Contact_Adjacency:
  Inclusion = внутри; Support = на поверхности-опоре; Contact_Adjacency = просто контакт.
- Contact_Adjacency vs Attachment:
  Contact = простое соприкосновение; Attachment = прочное, функциональное или конструктивное присоединение.
- Proximity vs Contact_Adjacency:
  Proximity = рядом без контакта; Contact_Adjacency = контакт есть.
- Front_Region vs Posterior_Region_Behind vs Lateral_Beside:
  Front = перед; Posterior = позади; Lateral = сбоку.
- Alignment_Alongness vs Crossing_Transverse:
  Alignment = расположен вдоль; Crossing = пересекает поперёк.
- Egress_Exiting_an_Interior vs Departure_from_a_Landmark:
  Egress = изнутри; Departure = просто удаление от ориентира.
- Ingress_Entering_an_Interior vs Approaching_a_Landmark:
  Ingress = вход внутрь; Approaching = приближение без вхождения.
- Numeric vs Approximative_Relation vs Quantitative_Large/Small:
  Numeric = точное число; Approximative = приблизительно; Quantitative = неточная оценка размера количества.
- Duration vs Point_in_Time vs Frequency:
  Duration = как долго; Point_in_Time = когда; Frequency = как часто.
- Quality vs Possession vs Content_Theme:
  Quality = свойство; Possession = принадлежность; Content_Theme = тема / содержание.
- Goal_as_Recipient vs Recipient:
  Goal_as_Recipient обычно связан с направленным движением / передачей; Recipient — более общая роль получателя.
- Clause-like relations:
  Используй только если узловая структура действительно кодирует такую логику; не выбирай их автоматически только из-за союза.

КАК ИСПОЛЬЗОВАТЬ ПОЛЯ

- text:
  нужен для глобального понимания предложения и события.
- name:
  это главная видимая форма узла; часто уже содержит агрегированный маркер.
- lemma:
  помогает понять семантический тип узла.
- pos_universal:
  помогает различать сущности, предикаты, модификаторы и служебные случаи.
- features:
  особенно важны Case, Number, Gender, Animacy, Tense, VerbForm, Degree, Voice и др.
- syntactic_link_target_id:
  задаёт головной узел B; связь выбирается между A и B.
- original_deprel:
  это подсказка из UD, но не окончательный ответ.
- introduced_by:
  полезно для пространственных, временных, целевых, инструментальных и тематических отношений.
- head_lemma:
  помогает понять, к какому типу головного узла относится A.

ПРАВИЛО НЕОДНОЗНАЧНОСТИ

Если несколько связей выглядят близкими:
1. Выбери ту, которая лучше всего соответствует определению.
2. Не изобретай промежуточных трактовок.
3. Если различие совсем тонкое, предпочти более прямую и буквальную интерпретацию.
4. ROOT используй только у узлов без syntactic_link_target_id.

ФОРМАТ ОТВЕТА

Верни только JSON-объект:

{
  \"nodes\": [
    {
      \"id\": \"...\",
      \"syntactic_link_name\": \"...\"
    }
  ]
}"""),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="")

if __name__ == "__main__":
    generate()


