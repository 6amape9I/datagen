ALL_RELATION_NAMES = [
    # Тематические роли
    "Agent", "Patient", "Recipient", "Instrument",
    # Статические пространственные отношения
    "Inclusion_Containment", "Exteriority", "Support", "Subjacency", "Covering_Superadjacency",
    "Proximity", "Contact_Adjacency", "Attachment", "Front_Region", "Posterior_Region_Behind",
    "Intermediacy", "Opposition_Across_from", "Alignment_Alongness", "Circumference_Encirclement",
    "Crossing_Transverse", "Lateral_Beside", "Functional_Proximity",
    # Динамические отношения: ИЗ
    "Source_as_Origin", "Egress_Exiting_an_Interior", "Separation_from_a_Surface",
    "Departure_from_a_Landmark", "Emergence_from_below", "Descent_from_a_high_point",
    "Ascent_to_a_high_point", "Detachment", "Egress_from_an_intermediate_position",
    "Emergence_from_behind_an_obstacle",
    # Динамические отношения: К
    "Goal_as_Recipient", "Distribution_over_an_area", "Ingress_Entering_an_Interior",
    "Attaining_a_Surface", "Approaching_a_Landmark", "Attachment_Connection",
    "Reaching_a_lower_position", "Reaching_the_other_side_Crossing", "Movement_to_a_posterior_region",
    "Entering_an_intermediate_position",
    # Динамические отношения: Траектория
    "Penetration", "Transverse", "Alignment", "Bypass", "Circumvention", "Vertical_path",
    "Superlative_Sublative", "Interlative",
    # Абстрактные и метафорические
    "Reaching_an_abstract_goal_state", "Metaphorical_Path", "Finality", "Acquisition",
    # Количественные
    "Numeric", "Quantitative_Large", "Quantitative_Small", "Collective_Relation",
    "Approximative_Relation", "Proportional_Fractional_Relation", "Metric_Measuring_Relation",
    # Временные
    "Duration", "Point_in_Time", "Frequency", "Terminus_ad_quem_Deadline",
    "Prospective_Starting_point",
    # Атрибутивные и логические
    "Quality", "Possession", "Content_Theme", "Addition_Conjunction", "Disjunction",
    # Связи между клаузами
    "Contrast", "Juxtaposition", "Concession", "Alternative", "Clarification",
    "Sequence_in_time_before", "Sequence_in_time_after", "Sequence_in_time_while",
    "Reason_because", "Result_since", "Result_because", "Goal", "Condition",
    "Comparison", "Specification_which", "Specification_that_is", "Exception", "Addition",
    # Специальная метка
    "ROOT"
]
