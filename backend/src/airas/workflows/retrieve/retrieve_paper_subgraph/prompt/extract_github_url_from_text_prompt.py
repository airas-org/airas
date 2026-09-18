extract_github_url_from_text_prompt = """\
# Task
You carefully read the contents of the “Paper Outline” and select one GitHub link from the “GitHub URLs List” that you think is most relevant to the contents.
# Constraints
- Output the index number corresponding to the selected GitHub URL.
- Be sure to select only one GitHub URL.
- If there is no related GitHub link, output None.

# Paper Summary

## Main Contributions
{{ paper_summary.main_contributions }}

## Methodology
{{ paper_summary.methodology }}

## Experimental Setup
{{ paper_summary.experimental_setup }}

## Limitations
{{ paper_summary.limitations }}

## Future Research Directions
{{ paper_summary.future_research_directions }}

# GitHub URLs List
{{ extract_github_url_list }}"""
