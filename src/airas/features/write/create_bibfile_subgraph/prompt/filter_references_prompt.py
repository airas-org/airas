filter_references_prompt = """\
You are an expert research assistant tasked with filtering reference lists to select the most relevant papers for citation in a research project.

**Research Context:**

**Research Study List (Main Papers):**
{% for study in research_study_list %}
Study {{ loop.index }}:
- Title: {{ study.get('title', 'N/A') }}
{% if study.get('full_text') %}
- Full Text: {{ study.full_text }}...
{% else %}
- Abstract: {{ study.get('abstract', 'N/A') }}
{% endif %}
{% endfor %}

**Research Hypothesis and Research Iterations:**
{{ research_session }}


**Reference Study List (Candidate Papers for Citation):**
{% for ref in reference_study_list %}
Reference {{ loop.index0 }}:
- Title: {{ ref.get('title', 'N/A') }}
{% if ref.get('full_text') %}
- Full Text: {{ ref.full_text }}...
{% else %}
- Abstract: {{ ref.get('abstract', 'N/A') }}
{% endif %}
{% endfor %}

**Instructions:**
1. Analyze the research study list and hypothesis to understand the research context and objectives.
2. From the reference study list, select papers that are most relevant for citation based on:
   - Direct relevance to the research topic and hypothesis
   - Methodological relevance (similar or foundational methods)
   - Theoretical background and foundational work
   - Recent developments in the field
   - Quality and impact of the papers
3. Prioritize references that:
   - Support or contradict the research hypothesis
   - Provide methodological foundations
   - Offer comparative studies or benchmarks
   - Present related work in the same domain
4. Avoid selecting papers that are:
   - Too general or unrelated to the specific research focus
   - Duplicative in content or approach
   - Of questionable quality or relevance

Select approximately {{ max_results }} most relevant references (adjust based on the total number available and relevance).
"""
