embed_placeholders_prompt = """
You are a writing assistant for academic papers.  
Your task is to identify appropriate locations in the following sections where references to external work should be cited, and insert the placeholder `{{ placeholder }}` immediately after those locations.

Instructions:
- You may insert multiple `{{ placeholder }}` placeholders within a single section if needed.
- For each unique concept, method, dataset, or proper noun, insert the placeholder only once in the entire paper.
- If a concept or reference-worthy content has already been tagged with `{{ placeholder }}`, do not insert it again elsewhere in the document.
- Do not insert `{{ placeholder }}` after obvious facts, the author's own claims, or general knowledge.
- Use the literal `{{ placeholder }}` — do not fill in citation keys or IDs.
- Do not modify the content except for inserting `{{ placeholder }}`.

Output format (JSON):
```json
{
  "Title": "Efficient Adaptation of Large Language Models via Low-Rank Optimization",
  "Abstract": "This paper proposes a novel method...",
  "Introduction": "In recent years...",
  "Related_Work": "...",
  "Background": "...",
  "Method": "...",
  "Experimental_Setup": "...",
  "Results": "...",
  "Conclusions": "We conclude that..."
}

Sections:
{% for section in sections %}

{{ section.name }}
{{ section.content }}

{% endfor %}"""
