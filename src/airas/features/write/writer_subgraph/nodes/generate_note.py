from jinja2 import Template

note: dict[str, list[str]] = {
    "Methods": [
        "base_method_text",
        "new_method",
        "verification_policy",
        "experiment_details",
    ],
    "Codes": ["experiment_code"],
    "Results": ["output_text_data"],
    "Analysis": ["analysis_report"],
    "Figures": ["image_file_name_list"],
}


def generate_note(state: dict) -> str:
    template = Template("""
    {% for section, items in sections.items() %}
    # {{ section }}
    {% for key, value in items.items() %}
    {% if key == "image_file_name_list" %}
    {% for img in value %}
    - {{ img }}
    {% endfor %}
    {% else %}
    {{ key }}: {{ value }}
    {% endif %}
    {% endfor %}
    {% endfor %}
    """)

    sections: dict[str, dict] = {
        section: {name: state[name] for name in names}
        for section, names in note.items()
    }

    return template.render(sections=sections)


if __name__ == "__main__":
    sample_state = {
        "base_method_text": "Baseline method using XYZ.",
        "new_method": "Proposed method with enhancements.",
        "verification_policy": "We compare on ABC metric.",
        "experiment_details": "3 trials on synthetic data.",
        "experiment_code": "def run(): pass",
        "output_text_data": "Achieved 95% accuracy.",
        "analysis_report": "Consistent improvement observed.",
        "image_file_name_list": ["fig1.pdf", "fig2.pdf"],
    }

    note_text = generate_note(sample_state)
    print(note_text)
