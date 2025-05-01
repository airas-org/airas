extract_paper_title_node_prompt = """\
"Queries" represents the user's search keywords.
"Content" is a block of markdown that lists research papers based on the user's search.
# Instructions:
- Extract only the titles of research papers from the "Content".
  - These titles may appear as the text inside markdown links (e.g., bold text or text inside square brackets [ ] if it represents a paper title).
- Sort the extracted titles in descending order of relevance to the "Queries" — meaning the most relevant titles should come first.
- Output the titles as a list of strings.
# Queries:
--------
{{ queries }}
--------
# Content:
--------
{{ result }}
--------"""
