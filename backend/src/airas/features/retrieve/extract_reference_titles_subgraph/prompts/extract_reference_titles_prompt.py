extract_reference_titles_prompt = """\
You are an expert in academic paper analysis.
Your task is to extract reference paper titles from the full text of research papers.

Instructions:
- Analyze the provided full text of research papers
- Extract all reference paper titles mentioned in the text
- Focus on titles that appear in reference sections, citations, or are explicitly mentioned as related work
- Return only the exact titles as they appear in the text
- Exclude general topics or field names that are not specific paper titles
- If no clear reference titles are found, return an empty list

Full Text:
---------------------------------
{{ full_text }}
---------------------------------

Please extract all reference paper titles and return them as a list of strings.
"""
