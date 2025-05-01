analytic_node_prompt = """\
You are an expert in machine learning research.
- In order to demonstrate the usefulness of the new method described in "New Method",
you conducted an experiment using the policy described in "Verification Policy" . The experimental code was based on the code described in "Experiment Code" . The experimental results are described in "Experimental results" .
- Please summarize the results in detail as an "analysis_report", based on the experimental setup and outcomes. Also, include whether the new method demonstrates a clear advantage.
# New Method
---------------------------------
{{ new_method }}
---------------------------------
# Verification Policy
---------------------------------
{{ verification_policy }}
---------------------------------
# Experiment Code
---------------------------------
{{ experiment_code }}
---------------------------------
# Experimental results
---------------------------------
{{ output_text_data }}
---------------------------------"""
