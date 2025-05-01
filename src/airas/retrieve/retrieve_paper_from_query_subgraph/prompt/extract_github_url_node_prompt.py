extract_github_url_node_prompt = """\
# Task
You carefully read the contents of the “Paper Outline” and select one GitHub link from the “GitHub URLs List” that you think is most relevant to the contents.
# Constraints
- Output the index number corresponding to the selected GitHub URL.
- Be sure to select only one GiHub URL.
- If there is no related GitHub link, output None.
# Paper Outline
{{ paper_summary }}
      
# GitHub URLs List
{{ extract_github_url_list }}"""
