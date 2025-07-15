generate_queries_prompt = """\
You are an expert research assistant tasked with generating search queries for finding relevant research papers.
Your goal is to create a set of well-structured queries that can be used with a research paper search API 
to retrieve papers that are conceptually or methodologically related to a given foundational paper (Research A).

**Research A (Base Paper):**
- **Title:** {{ paper_info.title }}
- **Authors:** {{ paper_info.authors | join(', ') }}
- **Publication Date:** {{ paper_info.publication_date }}
- **Journal/Conference:** {{ paper_info.journal }}
- **DOI:** {{ paper_info.doi }}
- **Main Contributions:** {{ paper_info.main_contributions }}
- **Methodology:** {{ paper_info.methodology }}
- **Experimental Setup:** {{ paper_info.experimental_setup }}
- **Limitations:** {{ paper_info.limitations }}
- **Future Research Directions:** {{ paper_info.future_research_directions }}
---

Previous Query: {{ previous_query }}

**Instructions (Important!):**
1. Analyze the provided Research A details.
2. Maintain topic relevance**: The generated queries should closely relate to the user's original query.
3. Generate exactly **{{ n_queries }} short search queries** (ideally 1-3 words each).
4. **No applied domains**: Do not generate queries related to industry applications, business applications, healthcare, finance, medical research, or market trends.
5. **Instead, focus on core theoretical concepts, mathematical principles, and model advancements** rather than how they are used in real-world industries.

**Format**
1. **Output must be a valid Python dictionary literal that can be parsed by `ast.literal_eval`.**
   - The dictionary must have exactly **{{ n_queries }} keys**:
{%- for i in range(1, n_queries + 1) %}
     - `"generated_query_{{ i }}"`: string  
{%- endfor %}
2. **No extra text, no triple backticks, no markdown.** Output ONLY the dictionary.
3. If you are unsure, only output valid Python dictionary syntax with double quotes for strings.

Now, output the dictionary literal in one single line (no additional commentary):"""
