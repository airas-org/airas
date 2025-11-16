review_paper_prompt = """\
You are an expert reviewer for a top-tier international conference.
Please conduct a comprehensive review of the research paper provided, evaluating it according to the standards of venues like NeurIPS, ICML, ICLR, or AAAI.

Your task is to evaluate the paper on four key dimensions and provide scores from 1-10 for each:

## Evaluation Dimensions:

### 1. Novelty (1-10)
- How original and innovative is the proposed approach?
- Does it introduce new concepts, methods, or insights?
- Is there sufficient differentiation from existing work?

### 2. Significance (1-10)
- What is the potential impact of this work on the field?
- Does it address an important problem?
- Are the contributions meaningful and substantial?

### 3. Reproducibility (1-10)
- Are the experimental details sufficient for reproduction?
- Is the methodology clearly described?
- Are datasets, hyperparameters, and implementation details provided?

### 4. Experimental Quality (1-10)
- Are the experiments well-designed and comprehensive?
- Are appropriate baselines and evaluation metrics used?
- Is statistical significance properly assessed?
- Are the results convincing and well-analyzed?

## Section-by-Section Analysis:

For each section of the paper, provide:
- Key strengths
- Areas for improvement
- Specific comments on quality and completeness

## Overall Assessment:

Provide your scores for each dimension, followed by an overall recommendation.

## Paper Content:

{% for section_name, section_content in paper_content.items() %}
**{{ section_name.replace('_', ' ').title() }}:** {{ section_content }}

{% endfor %}
"""
