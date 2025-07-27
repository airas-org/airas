generate_experiment_details_prompt = """\
Please follow the instructions below and tell us the details of the experiment for verification as described in the “Verification Policy”.
# Introduction
- Please answer each of the verification policies given in the “Verification Policy”.
- Please explain the details of the experiment as fully as possible. It is fine if the output is long in order to explain in detail.
- If you have any examples of experimental codes, please include them.
- Please use an experimental method that will increase the reliability of your research.
- Please make sure that the content of each experiment does not overlap too much. If several verification items can be confirmed in one experiment, please combine them into one experiment.
- Please consider the details of the experiment on the assumption that Pytorch will be used for implementation.
- Please keep in mind that you should use existing python libraries as much as possible, and avoid implementing things from scratch.
- The section 'Experimental code from the research on which it is based' and 'Experimental information from the research on which it is based' includes details about the experiments conducted in the original research. Please use this information to make your experimental setup as close as possible to the original.

# New Methods
-------------------------
{{ new_method }}
-------------------------
# Verification Policy
-------------------------
{{ verification_policy }}
--------------------------"""
