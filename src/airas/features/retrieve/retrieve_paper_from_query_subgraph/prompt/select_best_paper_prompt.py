select_base_paper_prompt = """
You are an expert research assistant tasked with selecting the most relevant and high-quality paper from a list of research papers. 
Your goal is to identify the paper that best aligns with the research topic and provides the most value as a foundational base for further research.

Below is a list of papers with their details:

{% for paper in candidate_papers %}
**Paper (ID: {{ paper.arxiv_id }})**
- **Title:** {{ paper.title }}
- **Authors:** {{ paper.authors | join(', ') }}
- **Publication Date:** {{ paper.publication_date }}
- **Journal/Conference:** {{ paper.journal }}
- **DOI:** {{ paper.doi }}
- **arXiv URL:** {{ paper.arxiv_url }}
- **GitHub URL:** {{ paper.github_urls }}
- **Main Contributions:** {{ paper.main_contributions }}
- **Methodology:** {{ paper.methodology }}
- **Experimental Setup:** {{ paper.experimental_setup }}
- **Limitations:** {{ paper.limitations }}
- **Future Research Directions:** {{ paper.future_research_directions }}
{% endfor %}

**Selection Criteria:**
1. **Relevance:** The paper should directly address the research topic or provide foundational insights. Exclude papers that are only tangentially related.
2. **Quality:** Prioritize papers published in reputable journals or conferences. Evaluate the clarity of the abstract and the soundness of the methodology.
3. **Future Potential:** Consider whether the paper introduces innovative methods or theories that could be foundational for future research.
4. **Code Availability:** Papers with accessible and functional GitHub repositories are preferred. Evaluate the quality of the code and documentation if available.

**Instructions:**
1. Carefully review the details of each paper.
2. Evaluate each paper based on the selection criteria above.
3. Select the **single most relevant and high-quality paper** that best serves as a foundational base for further research.
4. Return the **arxiv_id** of the selected paper.
5. Provide your response in the following JSON format:
```json
{
  "selected_arxiv_id": "{arxiv_id}"
}
```

"""


select_related_paper_prompt = """
You are an expert research assistant tasked with selecting the most relevant and high-quality research paper from a list of candidate papers. 
Your goal is to identify {{ add_paper_num }} papers that can be effectively synthesized with a given foundational paper (Research A) to create a novel and non-trivial research direction.

**Research A (Base Paper):**
- **Title:** {{ selected_base_paper.title }}
- **Authors:** {{ selected_base_paper.authors | join(', ') }}
- **Publication Date:** {{ selected_base_paper.publication_date }}
- **Journal/Conference:** {{ selected_base_paper.journal }}
- **DOI:** {{ selected_base_paper.doi }}
- **arXiv URL:** {{ selected_base_paper.arxiv_url }}
- **GitHub URL:** {{ selected_base_paper.github_urls }}
- **Main Contributions:** {{ selected_base_paper.main_contributions }}
- **Methodology:** {{ selected_base_paper.methodology }}
- **Experimental Setup:** {{ selected_base_paper.experimental_setup }}
- **Limitations:** {{ selected_base_paper.limitations }}
- **Future Research Directions:** {{ selected_base_paper.future_research_directions }}

Below is a list of candidate papers (Patch paper candidates):

{% for paper in candidate_papers %}
**Paper (ID: {{ paper.arxiv_id }})**
- **Title:** {{ paper.title }}
- **Authors:** {{ paper.authors | join(', ') }}
- **Publication Date:** {{ paper.publication_date }}
- **Journal/Conference:** {{ paper.journal }}
- **DOI:** {{ paper.doi }}
- **arXiv URL:** {{ paper.arxiv_url }}
- **GitHub URL:** {{ paper.github_urls }}
- **Technical Summary:** {{ paper.technical_summary }}
{% endfor %}

**Selection Criteria:**
1. **Synthesis Potential:** The selected paper should complement Research A in a way that leads to a novel and non-trivial research direction when combined.
2. **Relevance:** The paper should have a meaningful conceptual or methodological connection with Research A, avoiding those that are only loosely related.
3. **Quality:** Prioritize papers published in reputable journals or conferences. Evaluate the clarity of the abstract and the soundness of the methodology.
4. **Future Potential:** Consider whether the paper introduces innovative methods or theories that could provide a strong foundation for new research.
5. **Code Availability:** Papers with accessible and functional GitHub repositories are preferred. Evaluate the quality of the code and documentation if available.

**Instructions:**
1. Carefully review the details of each candidate paper.
2. Evaluate each paper based on the selection criteria above.
3. Select {{ add_paper_num }} papers from the candidate papers that are relevant and of high-quality, when synthesized with Research A, enables a non-trivial and novel research direction.
4. Output the ""arxiv_id** of the selected paper as a single plain text string, with each title separated by a newline character.
5. Return your answer in JSON format with a single key "selected_arxiv_id". Do not include any additional commentary or formatting.
"""
