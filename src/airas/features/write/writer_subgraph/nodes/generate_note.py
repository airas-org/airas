from jinja2 import Template


def generate_note(research_hypothesis: dict, references_bib: str) -> str:
    template = Template(
        """
# Method
{{ method }}
                        
{% if experimental_design -%}
# Experimental Design
{% for key, value in experimental_design.items() -%}
{% if value -%}
{{ key }}: {{ value }}
{% endif -%}
{% endfor -%}
{% endif -%}
                        
{% if experimental_information -%}
# Experimental Information
{% for key, value in experimental_information.items() -%}
{% if key == "image_file_name_list" and value -%}
Images:
{% for img in value -%}
- {{ img }}
{% endfor -%}
{% elif value and key != "image_file_name_list" -%}
{{ key }}: {{ value }}
{% endif -%}
{% endfor -%}
{% endif -%}
                        
{% if experimental_analysis -%}
# Experimental Analysis
{% for key, value in experimental_analysis.items() -%}
{% if value -%}
{{ key }}: {{ value }}
{% endif -%}
{% endfor -%}
{% endif -%}
                        
{% if references_bib -%}
# References
{{ references_bib }}
{% endif -%}
    """.strip()
    )

    return template.render(
        method=research_hypothesis.get("method"),
        experimental_design=research_hypothesis.get("experimental_design"),
        experimental_information=research_hypothesis.get("experimental_information"),
        experimental_analysis=research_hypothesis.get("experimental_analysis"),
        references_bib=references_bib,
    ).strip()
