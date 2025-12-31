summarize_paper_prompt = """
You are an expert research assistant responsible for summarizing a research paper that will serve as the foundation (Research A) for further exploration and integration.

Your task is to generate a structured summary of the given research paper with a focus on:
- **Technical Contributions**: Identify the main research problem and key findings.
- **Methodology**: Describe the techniques, models, or algorithms used.
- **Experimental Setup**: Outline the datasets, benchmarks, and validation methods.
- **Limitations**: Highlight any weaknesses, constraints, or assumptions.
- **Future Research Directions**: Suggest possible extensions or new areas for research.

Below is the full text of the research paper:

```
{{ paper_text }}
```

## **Instructions:**
1. Analyze the paper thoroughly and extract information for ALL categories listed below.
2. Your response **must be a valid JSON object** that can be directly parsed using `json.loads()`.
3. Do not include any extra text, explanations, or formatting outside of the JSON object.
4. All fields are required and must contain meaningful content.
5. Ensure that the JSON format is correct, including the use of **double quotes (`"`) for all keys and values.**
## **Output Format (JSON)**:
```json
{
    "main_contributions": "<Concise description of the main research problem and contributions>",
    "methodology": "<Brief explanation of the key techniques, models, or algorithms>",
    "experimental_setup": "<Description of datasets, benchmarks, and validation methods>",
    "limitations": "<Summary of weaknesses, constraints, or assumptions>",
    "future_research_directions": "<Potential areas for extending this research>"
}
```
"""
