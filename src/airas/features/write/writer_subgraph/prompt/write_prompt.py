from airas.features.write.constants import (
    REFERENCE_CANDIDATES_MARKER,
    REQUIRED_CITATIONS_MARKER,
)

write_prompt = f"""
Now write the complete research paper following all the guidelines and requirements specified above.

IMPORTANT CITATION REQUIREMENTS:
- If you see "{REQUIRED_CITATIONS_MARKER}" section in the references, you MUST cite ALL papers listed under that section in your manuscript
- These required citations should be naturally integrated into relevant sections of the paper
- Papers under "{REFERENCE_CANDIDATES_MARKER}" section are optional and can be cited if relevant to your discussion
"""
