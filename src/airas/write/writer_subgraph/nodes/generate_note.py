import os
import glob
from typing import Optional
from jinja2 import Template


corresponding_section: dict[str, list[str]] = {
    "Title": [],
    "Methods": [
        "base_method_text",
        "new_method",
        "verification_policy",
        "experiment_details",
    ],
    "Codes": ["experiment_code"],
    "Results": ["output_text_data"],
    "Analysis": ["analysis_report"],
    # "Related Work":[]
}


def generate_note(state: dict, figures_dir: Optional[str] = None) -> str:
    template = Template("""
    {% for section, items in sections.items() %}
    # {{ section }}
    {% for key, value in items.items() %}
    {{ key }}: {{ value }}
    {% endfor %}
    {% endfor %}
    
    # Figures
    {% if figures %}
    The following figures are available in the 'images/' directory and may be included in the paper:
    {% for fig in figures %}
    - {{ fig }}
    {% endfor %}
    {% else %}
    No figures available.
    {% endif %}
    """)

    sections: dict[str, dict] = {}
    for section, state_name_list in corresponding_section.items():
        matched_items: dict[str, str] = {}
        for state_name in state_name_list:
            matched_items[state_name] = state[state_name]
        sections[section] = matched_items

    figures = []
    if figures_dir is not None:
        figures.extend(
            [os.path.basename(f) for f in glob.glob(os.path.join(figures_dir, "*.pdf"))]
        )
    return template.render(sections=sections, figures=figures)
