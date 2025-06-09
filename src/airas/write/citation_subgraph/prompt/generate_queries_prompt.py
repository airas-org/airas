generate_queries_prompt = """\
You are an expert research assistant tasked with generating search queries for finding research papers
that should be cited at specific placeholder positions in a manuscript.


**Instructions (Important!)**
1. For each placeholder, examine its surrounding context carefully and infer what *seminal* or *most-cited* work is being referenced.
2. Produce search queries that will retrieve papers directly relevant to that context.
3. Include specific algorithm names, theoretical tools (e.g., Lyapunov function, convexity, ADMM), or mathematical concepts wherever possible.
4. Generate exactly **{{ n_queries }} sentence-level search queries**  
   (each query should be a single, well-formed English sentence that could be pasted directly into OpenAlex or Semantic Scholar).
5. *No applied domains*: avoid terms tied to industry, healthcare, finance, etc.
6. Focus on core theoretical ideas, mathematical principles, or model innovations.

**Format**
Output must be a valid Python dictionary literal that can be parsed by `ast.literal_eval`
and must have exactly **{{ n_queries }} keys**:

{% for i in range(1, n_queries + 1) -%}
    - `"generated_query_{{ i }}"`: string
{%- endfor %}

No extra text, no markdown, no backticks.

Now, output the dictionary literal in **one single line** (no additional commentary):"""
