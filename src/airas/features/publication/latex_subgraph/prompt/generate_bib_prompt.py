generate_bib_prompt = """
You are a BibTeX conversion assistant.
Return **only** a valid JSON object whose keys are
"bib_entry_1" … "bib_entry_{{ refs|length }}", in the same order as the input.
Each value must be a complete, single-line BibTeX entry ending with a newline.

Instructions
------------
1. Pick the most appropriate BibTeX entry type (e.g. @article, @inproceedings,
   @book, @misc) based solely on the fields you see.
2. Generate an appropriate citation key from the reference metadata (e.g., using author names and year). Do not use any external placeholder or identifier.
3. Populate standard BibTeX fields (author, title, journal, year, etc.) if the
   corresponding data exists.  Omit missing information.
4. Escape LaTeX-special characters (`{}`, `%`, `&`, `$`, `#`, `_`, `~`), and replace all non-ASCII Unicode characters with equivalent LaTeX escape sequences (e.g., á → \\'a, ö → \\"o, ć → \\'c, ō → \={o}, ọ → \d{o}).
5. Do **not** include comments, markdown, or explanatory text outside the JSON.

Input references
----------------
{% for ref in refs %}
Reference {{ loop.index }}:
  placeholder : {{ ref.placeholder }}
  metadata    : {{ ref.reference }}
{% endfor %}

Output format
-------------
```json
{
  "bib_entry_1": "@article{ ... }",
  "bib_entry_2": "@misc{ ... }",
  "...": "...",
  "bib_entry_{{ refs|length }}": "@inproceedings{ ... }"
}"""
