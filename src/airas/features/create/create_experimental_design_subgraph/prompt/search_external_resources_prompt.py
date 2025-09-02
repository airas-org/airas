search_external_resources_prompt = """
# Instructions
Search for URLs and download links for external resources needed for the experiment described below.

# Task
Based on the experimental strategy and details, identify and find specific URLs for:
- Datasets (download links, GitHub repositories)
- Pretrained models (PyTorch model URLs, Hugging Face links)
- Additional resources (configuration files, auxiliary data)

Return the results in a clear, structured format listing resource names and their URLs.

# Experimental Information
**Strategy:** {{ new_method.experimental_design.experiment_strategy }}

**Details:** {{ new_method.experimental_design.experiment_details }}

# Output Format
Return your response in this exact JSON format:
```json
{
  "external_resources": "Dataset: [Dataset Name]\nURL: [Direct download URL or repository URL]\n\nModel: [Model Name]\nURL: [Download URL or model hub URL]\n\nAdditional: [Resource Name]\nURL: [URL or documentation link]"
}
```
"""
