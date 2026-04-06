You are annotating the semantic relation between node A and its syntactic head B inside a single sentence.

Input:
- `text`
- `nodes[]`

Each node may contain:
- `id`
- `name`
- `lemma`
- `pos_universal`
- `features`
- `syntactic_link_target_id`
- `original_deprel`
- `introduced_by`
- `head_lemma`

Core rules:
- If `syntactic_link_target_id` is `null`, the label must be `ROOT`.
- If `syntactic_link_target_id` is not `null`, `ROOT` is forbidden.
- Every input node id must appear exactly once in the output.
- Return only JSON with shape `{"nodes":[{"id":"...","syntactic_link_name":"..."}]}`.
- Each output node object must contain only `id` and `syntactic_link_name`.
- Do not return explanations, markdown, comments, or any extra fields.

Key distinctions:
- `Agent` initiates or controls an event; `Patient` is affected by it.
- `Recipient` receives transfer; `Instrument` is the means or tool.
- `Inclusion_Containment` means inside; `Support` means on a supporting surface; `Contact_Adjacency` means contact without support or containment.
- `Attachment` means a stable attachment or integration.
- `Duration` answers “how long”, `Point_in_Time` answers “when”, and `Frequency` answers “how often”.
- `Quality` is a property, `Possession` is ownership/belonging, `Content_Theme` is topic or subject matter.

Allowed labels:
{{ALLOWED_LABELS}}
