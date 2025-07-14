from typing import Optional

from jinja2 import Template


def generate_note(
    base_method_text: Optional[str] = None,
    new_method: Optional[str] = None,
    verification_policy: Optional[str] = None,
    experiment_details: Optional[str] = None,
    experiment_code: Optional[str] = None,
    output_text_data: Optional[str] = None,
    analysis_report: Optional[str] = None,
    image_file_name_list: Optional[list[str]] = None,
) -> str:
    template = Template("""
    {% for section, items in sections.items() %}
    # {{ section }}
    {% for key, value in items.items() %}
    {% if key == "image_file_name_list" and value %}
    {% for img in value %}
    - {{ img }}
    {% endfor %}
    {% elif value is not none %}
    {{ key }}: {{ value }}
    {% endif %}
    {% endfor %}
    {% endfor %}
    """)

    sections = {
        "Methods": {
            "base_method_text": base_method_text,
            "new_method": new_method,
            "verification_policy": verification_policy,
            "experiment_details": experiment_details,
        },
        "Codes": {
            "experiment_code": experiment_code,
        },
        "Results": {
            "output_text_data": output_text_data,
        },
        "Analysis": {
            "analysis_report": analysis_report,
        },
        "Figures": {
            "image_file_name_list": image_file_name_list or [],
        },
    }

    return template.render(sections=sections)
