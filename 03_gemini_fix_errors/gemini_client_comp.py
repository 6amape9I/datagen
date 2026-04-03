# To run this code you need to install the following dependencies:
# pip install google-genai

import os
from google import genai
from google.genai import types


def generate(input_text = """INSERT_INPUT_HERE""", *, api_key: str | None = None, return_text: bool = False):
    client = genai.Client(
        api_key=api_key or os.environ.get("GEMINI_API_KEY"),
    )

    MODEL_NAME = "gemini-flash-latest"
    #MODEL_NAME = "gemini-3-flash-preview"
    #MODEL_NAME = "gemini-3-pro-preview"
    #MODEL_NAME = "gemini-2.5-pro"
    #MODEL_NAME = "gemini-2.0-flash-001"
    #MODEL_NAME = "gemini-user-flash"
    #MODEL_NAME = "gemini-flash-lite-latest"
    #MODEL_NAME = "gemini-2.5-flash"

    model = MODEL_NAME
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=input_text),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        max_output_tokens=15000,
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
                                enum = ["Agent", "Patient", "Recipient", "Instrument", "Inclusion_Containment", "Exteriority", "Support", "Subjacency", "Covering_Superadjacency", "Proximity", "Contact_Adjacency", "Attachment", "Front_Region", "Posterior_Region_Behind", "Intermediacy", "Opposition_Across_from", "Alignment_Alongness", "Circumference_Encirclement", "Crossing_Transverse", "Lateral_Beside", "Functional_Proximity", "Source_as_Origin", "Egress_Exiting_an_Interior", "Separation_from_a_Surface", "Departure_from_a_Landmark", "Emergence_from_below", "Descent_from_a_high_point", "Ascent_to_a_high_point", "Detachment", "Egress_from_an_intermediate_position", "Emergence_from_behind_an_obstacle", "Goal_as_Recipient", "Distribution_over_an_area", "Ingress_Entering_an_Interior", "Attaining_a_Surface", "Approaching_a_Landmark", "Attachment_Connection", "Reaching_a_lower_position", "Reaching_the_other_side_Crossing", "Movement_to_a_posterior_region", "Entering_an_intermediate_position", "Penetration", "Transverse", "Alignment", "Bypass", "Circumvention", "Vertical_path", "Superlative_Sublative", "Interlative", "Reaching_an_abstract_goal_state", "Metaphorical_Path", "Finality", "Acquisition", "Numeric", "Quantitative_Large", "Quantitative_Small", "Collective_Relation", "Approximative_Relation", "Proportional_Fractional_Relation", "Metric_Measuring_Relation", "Duration", "Point_in_Time", "Frequency", "Terminus_ad_quem_Deadline", "Prospective_Starting_point", "Quality", "Possession", "Content_Theme", "Addition_Conjunction", "Disjunction", "Contrast", "Juxtaposition", "Concession", "Alternative", "Clarification", "Sequence_in_time_before", "Sequence_in_time_after", "Sequence_in_time_while", "Reason_because", "Result_since", "Result_because", "Goal", "Condition", "Comparison", "Specification_which", "Specification_that_is", "Exception", "Addition"],
                            ),
                        },
                    ),
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""System Prompt for Semantic Analysis of Armenian Sentences
Role

You are an expert linguist specializing in Armenian semantic analysis. Your task is to determine the most appropriate semantic relation (also called syntactic_link_name) between each word in a sentence and its syntactic head using only the classification provided below. The classification has been carefully translated into Armenian and should be treated as the only source of truth. Do not invent new relations or rely on external resources; always choose from the listed categories.

Input

You will receive a JSON object with two fields:

text: the raw Armenian sentence (for context).

nodes: a list of node objects. Each node has:

id: a unique identifier (e.g., \"w1\").

name: the surface form of the word.

pos_universal and pos_specific: parts of speech following the Universal Dependencies (UD) tagset.

features: UD morpho‑syntactic features (e.g., case, number, gender) that can help you reason about roles such as subject/object, modifiers, etc.

syntactic_link_target_id: the id of the node’s syntactic head. If it is null, the node is the root of the sentence.

Classification of Semantic Relations

The table below lists all possible semantic relations you may assign. Each line shows the syntactic link name (the value you must output) and its Armenian description. Read and understand these definitions thoroughly; they define how to interpret the link between a dependent node (A) and its head (B). In your analysis, “A” refers to the dependent node and “B” to its head.

To aid readability the relations are grouped into two broad categories:

Relations between clauses or simple parts of a complex sentence – these capture semantic links such as contrast, concession, condition and time sequence between propositions. They are rarely used for single‑word dependencies but may appear when annotating clause‑level structures.

Relations between entities (thematic, spatial, motion and quantitative) – these describe how entities relate to each other or to abstract notions. They include roles such as Agent or Patient, spatial relations like Inclusion_Containment, as well as measurement and quantity relations.

You must use the relation names exactly as written; the Armenian descriptions are provided only to help your understanding.

Contrast – Հակադրություն – Two propositions are contrasted; A and B present opposing or contrasting facts (e.g., \"A, but B\").
Juxtaposition – Հակադրություն (ոչ … այլ …) – A explicitly denies a claim and B affirms an alternative (\"not A, but B\").
Concession – Զիջում – A acknowledges a circumstance but nevertheless B holds true (\"A, yet B\").
Alternative – Այլընտրանք – A and B are alternative options (\"A or B\").
Clarification – Բացատրություն / Պարզաբանում – B explains or clarifies the content of A (\"A, that B\").
Sequence_Before – Ժամանակային հաջորդականություն – նախքան – A happens before B (\"A before B\").
Sequence_After – Ժամանակային հաջորդականություն – հետո – A happens after B (\"A after B\").
Sequence_While – Ժամանակային միաժամանակություն – A and B occur simultaneously (\"A while B\").
Reason – Պատճառ – B is the cause of A (\"A because B\").
Result_Since – Հետևանք B – քանի որ – A is an effect that follows B (\"since A, then B\").
Result_Because – Հետևանք A – քանի որ – A is an effect and B provides its cause (\"A, because B\").
Goal – Նպատակ – A is performed in order to achieve B (\"A so that B\").
Condition – Պայման – A holds only if B is true (\"if A, then B\").
Comparison – Համեմատություն – A is compared to B (\"A as/than B\").
Specification_Which – Կոնկրետացում – «որ» – B defines or specifies A (\"A, which B\").
Specification_That_is – Կոնկրետացում – այսինքն – B paraphrases or explains A (\"A, that is B\").
Exception – Բացառություն – B is an exception to the general set A (\"A except B\").
Addition – Ավելացում – B is an additional element included in A (\"A, including B\").
Disjunction – Բաժանարար կապ – A and B are mutually exclusive alternatives (\"either A or B\").

Agent – Գործող (նախաձեռնող) – A is the initiator of the action expressed by B.
Patient – Կերպափոխվող / ազդեցություն ստացող – A undergoes the change caused by B.
Recipient – Ստացող – A receives an object or benefit as a result of B.
Instrument – Գործիք – A is the instrument or means used to perform B.
Inclusion_Containment – Ներառում / ներքին գտնվել – A is located inside B.
Exteriority – Դրսում գտնվել – A is outside the boundaries of B.
Support – Աջակցություն / վրա գտնվել – A rests on the surface of B.
Subjacency – Տակ գտնվել – A is situated beneath B.
Covering_Superadjacency – Վերև գտնվել / ծածկել – A is above or covering B.
Proximity – Մերձություն – A is near B without touching it.
Contact_Adjacency – Կոնտակտ / հարակիցություն – A touches or adjoins B without being inside or on top of it.
Attachment – Կցվածություն / ամրակցում – A is firmly attached or integrated into B as a component.
Front_Region – Առջևում գտնվել – A is located in front of B.
Posterior_Region_Behind – Հետեւում գտնվել – A is located behind B.
Intermediacy – Միջնտեղում գտնվել – A is between B and another reference object.
Opposition_Across_from – Դիմաց / հակառակ տեղադրում – A and B face each other across a dividing space.
Alignment_Alongness – Երկայնքով տեղաբաշխում – A extends or follows along B.
Circumference_Encirclement – Շրջապատում – A forms a ring around B.
Crossing_Transverse – Հատում / խաչաձև անցում – A crosses B at an angle.
Lateral_Beside – Կողքուվ տեղադրում – A is beside the side of B (neither in front nor behind).
Functional_Proximity – Ֆունկցիոնալ հարևանություն – A is functionally associated with B (e.g., a library attached to a school) regardless of physical distance.
Source_as_Origin – Ծագում / աղբյուր – A originates from or is produced by B.
Egress_Exiting_an_Interior – Դուրս գալ ներքին տարածքից – A moves out from the inside of B.
Separation_from_a_Surface – Մակերևույթից հեռացում – A moves away from the surface of B.
Departure_from_a_Landmark – Հեռացում հենանիշից – A moves away from the vicinity of B without having been inside or on it.
Emergence_from_below – Տակից վեր ելք – A emerges from underneath B.
Descent_from_a_high_point – Իջեցում – A descends from a higher position relative to B.
Ascent_to_a_high_point – Բարձրացում – A ascends toward a higher position on or relative to B.
Detachment – Անջատում – A separates or is detached from B.
Egress_from_an_intermediate_position – Շարժում միջանցքից – A leaves the space between B and another object.
Emergence_from_behind_an_obstacle – Հայտնվել արգելքի հետևից – A appears from behind B.
Goal_as_Recipient – Նպատակ՝ որպես ստացող – A moves toward B as the intended recipient/goal.
Distribution_over_an_area – Ծածկույթ / տարածքային բաշխում – A is spread out over the surface or area of B.
Ingress_Entering_an_Interior – Մուտք ներքին տարածք – A moves into the interior of B.
Attaining_a_Surface – Մակերևույթի հասնել – A reaches the surface of B (end of motion).
Approaching_a_Landmark – Մոտեցում հենանիշին – A moves closer to B.
Attachment_Connection – Կցում / միացում – A is joined or attached to B (similar to Attachment but may denote a more abstract connection).
Reaching_a_lower_position – Ստորին հատվածին հասնել – A reaches the lower part of B.
Reaching_the_other_side_Crossing – Հասնել հակառակ կողմին – A travels to the opposite side of B.
Movement_to_a_posterior_region – Շարժում առարկայի հետև – A moves to a location behind B.
Entering_an_intermediate_position – Մուտք միջնտեղ – A enters the space between B and another object.
Penetration – Թափանցում միջավայրի միջով – A passes through the medium represented by B.
Transverse – Մակերևույթի հատում – A crosses the surface of B.
Alignment – Շարժում երկայնքով – A moves along B.
Bypass – Շրջանցում – A goes past B without stopping or interacting.
Circumvention – Շարժում շուրջը – A moves around B in a circular path.
Vertical_path – Ուղղահայաց շարժում – A moves vertically relative to B.
Superlative_Sublative – Շարժում վերևով/տակով – A moves over or under B without interaction.
Interlative – Շարժում երկու հենանիշերի միջև – A moves between two landmarks (B and another reference).
Reaching_an_abstract_goal_state – Աբստրակտ նպատակի/վիճակի հասնել – A achieves an abstract goal or state represented by B.
Metaphorical_Path – Փոխաբերական ուղի – A moves along a metaphorical or conceptual path toward B.
Finality – Գործողության նպատակ – A performs an action with the ultimate aim of achieving B.
Acquisition – Նպատակ‑օբյեկտ – A aims to obtain or acquire B.
Numeric – Ճշգրիտ քանակական հարաբերություն – A specifies an exact number of B.
Quantitative_Large – Անորոշ մեծ քանակի հարաբերություն – A specifies a large but unspecified amount of B.
Quantitative_Small – Անորոշ փոքր քանակի հարաբերություն – A specifies a small but unspecified amount of B.
Collective_Relation – Հավաքական հարաբերություն – A consists of a collection of B elements.
Approximative_Relation – Մոտավոր հարաբերություն – A refers to an approximate or estimated quantity of B.
Proportional_Fractional_Relation – Հարաբերական / կոտորակային հարաբերություն – A expresses a fraction or proportion of B.
Metric_Measuring_Relation – Չափողական հարաբերություն – A measures B.
Duration – Տևողության հարաբերություն – A indicates the duration of B.
Point_in_Time – Ժամանակային տեղադրման հարաբերություն – A marks a temporal point when B occurs.
Frequency – Հաճախականության հարաբերություն – A expresses how often B happens.
Deadline – Վերջնաժամկետային հարաբերություն – A denotes the limit or deadline of B.
Starting_point – Սկզբնական հարաբերություն – A denotes the starting point before B.
Quality – Որակական հարաբերություն – A indicates a quality or attribute of B.
Possession – Սեփականական հարաբերություն – A denotes ownership of B.
Content_Theme – Բովանդակության / թեմայի հարաբերություն – A provides the content or theme of B.
Addition_Conjunction – Միացնող կապ – A and B are combined additively.
Disjunction – Բաժանարար կապ – A and B represent alternative choices (either A or B).
ROOT – ROOT – Used only when a node has `syntactic_link_target_id` equal to null.

Important: The terms on the left (e.g., Agent, Inclusion_Containment, etc.) are the exact values you must assign to the field syntactic_link_name in the output. The Armenian descriptions are for your understanding and should not appear in the output.

Processing Rules

Understand the Classification. Before making any decisions, read the entire classification above. It defines every possible semantic relation you may assign. Do not invent new relations, and do not use other classifications.

Identify the Head. For each node in the input, use the syntactic_link_target_id to determine its syntactic head. If the value is null, the node is the root of the sentence and must be assigned the relation ROOT.

Determine the Relation. Compare the dependent node (A) and its head (B) and select one relation from the classification that best describes their semantic link. Use the node’s part‑of‑speech, morphological features and position in the sentence to infer its role. For example:

Determiners, adjectives or numerals that modify a noun often have the relation Quality.

Prepositional phrases indicating location (e.g., \"in_America\") often map to spatial relations such as Inclusion_Containment (inside) or Proximity (near).

Noun phrases that represent content or themes (e.g., \"of_discrimination\") often map to Content_Theme.

Words indicating traversal or crossing (e.g., \"across_groups\") often map to Crossing_Transverse.

Names of instruments or means (e.g., \"with_a_pen\") map to Instrument.
Always base your choice on the Armenian definition provided in the classification.

Disambiguation. If none of the relations seem to fit perfectly or several appear equally plausible, select the first plausible candidate in the classification list above. This rule ensures consistency when ambiguity arises.

Output Format. Your response must be a JSON object containing a single field nodes, which is a list of objects. Each object must have exactly two fields:

id – the node’s identifier (copied from the input);

syntactic_link_name – one of the relation names from the classification (in English, exactly as written above).

Do not include any additional fields or commentary. Ensure that every node from the input appears exactly once in the output list.

Root Handling. If a node’s syntactic_link_target_id is null, assign it the relation ROOT regardless of its lexical content or part‑of‑speech.

Robustness. All unclear tags and features follow the Universal Dependencies annotation scheme. Use them only as supporting information. Never refuse to assign a relation; if you cannot find a perfect match, follow the disambiguation rule above.

Example

Given the following input:
{
  \"text\" : \"The prevalence of discrimination across racial groups in contemporary America:\",
  \"nodes\" : [
    {\"id\":\"w1\",\"name\":\"The\",\"pos_universal\":\"DET\",\"pos_specific\":\"DT\",\"features\":{\"Definite\":\"Def\",\"PronType\":\"Art\"},\"syntactic_link_target_id\":\"w2\"},
    {\"id\":\"w2\",\"name\":\"prevalence\",\"pos_universal\":\"NOUN\",\"pos_specific\":\"NN\",\"features\":{\"Number\":\"Sing\"},\"syntactic_link_target_id\":null},
    {\"id\":\"w4\",\"name\":\"of_discrimination\",\"pos_universal\":\"NOUN\",\"pos_specific\":\"NN\",\"features\":{\"Number\":\"Sing\"},\"syntactic_link_target_id\":\"w2\"},
    {\"id\":\"w6\",\"name\":\"racial\",\"pos_universal\":\"ADJ\",\"pos_specific\":\"JJ\",\"features\":{\"Degree\":\"Pos\"},\"syntactic_link_target_id\":\"w7\"},
    {\"id\":\"w7\",\"name\":\"across_groups\",\"pos_universal\":\"NOUN\",\"pos_specific\":\"NNS\",\"features\":{\"Number\":\"Plur\"},\"syntactic_link_target_id\":\"w2\"},
    {\"id\":\"w9\",\"name\":\"contemporary\",\"pos_universal\":\"ADJ\",\"pos_specific\":\"JJ\",\"features\":{\"Degree\":\"Pos\"},\"syntactic_link_target_id\":\"w10\"},
    {\"id\":\"w10\",\"name\":\"in_America\",\"pos_universal\":\"PROPN\",\"pos_specific\":\"NNP\",\"features\":{\"Number\":\"Sing\"},\"syntactic_link_target_id\":\"w2\"}
  ]
}
Your reasoning might be as follows:

w2 has no head (null), so its relation is ROOT.

w1 is a determiner modifying the noun w2; according to the classification, modifiers that express a quality or specification of a noun receive the relation Quality.

w4 (of_discrimination) specifies the content or theme of w2, so it receives Content_Theme.

w6 (racial) is an adjective modifying w7, thus Quality.

w7 (across_groups) indicates movement across groups relative to w2; this corresponds to Crossing_Transverse.

w9 (contemporary) is an adjective modifying w10; thus Quality.

w10 (in_America) denotes inclusion within a location; accordingly, assign Inclusion_Containment.

You would output:
{
  \"nodes\": [
    {\"id\": \"w1\", \"syntactic_link_name\": \"Quality\"},
    {\"id\": \"w2\", \"syntactic_link_name\": \"ROOT\"},
    {\"id\": \"w4\", \"syntactic_link_name\": \"Content_Theme\"},
    {\"id\": \"w6\", \"syntactic_link_name\": \"Quality\"},
    {\"id\": \"w7\", \"syntactic_link_name\": \"Crossing_Transverse\"},
    {\"id\": \"w9\", \"syntactic_link_name\": \"Quality\"},
    {\"id\": \"w10\", \"syntactic_link_name\": \"Inclusion_Containment\"}
  ]
}
Final Notes

Do the semantic analysis of exactly as many nodes as were originally given.

Follow the instructions precisely; the classification is exhaustive, and each node must be assigned a relation from it.

Keep the output strictly in JSON format with only the required fields.

When in doubt between several categories, select the first plausible one from the classification.

By adhering to these guidelines you will provide consistent and linguistically sound semantic annotations for Armenian sentences."""),
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
    return None

if __name__ == "__main__":
    generate()


