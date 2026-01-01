convert_to_html_prompt = """\
Convert research paper sections to clean, semantic HTML for GitHub Pages publication.

## Input Data:
{% for section in sections %}
**{{ section.name }}:**
{{ section.content }}

{% endfor %}
{% if image_file_name_list %}
**Available Images:**
{% for image in image_file_name_list %}
- {{ image }}
{% endfor %}
{% endif %}

## HTML Requirements:

### Section Structure:
- **Title section**: Use `<h2 class="paper-title">Title Text</h2>` (no wrapper)
- **Other sections**: Use `<section><h2>Section Name</h2>...</section>`
- **Paragraphs**: Use `<p>` for each logical paragraph
- **Lists**: Use `<ul><li><strong>Key:</strong> Description</li></ul>`

### Figures (Results section only):
- Use `<figure><img src="images/filename.png"><figcaption>Figure N: Description</figcaption></figure>`
- Convert .pdf to .png in src paths (e.g., `plot1.pdf` → `images/plot1.png`)
- **Width rules:**
  - Paired images (*_pair1.png, *_pair2.png): `<figure class="img-pair">` with `style="width:48%"` each
  - Single images: `style="width:70%"`

### Code (Method section only):
- Use `<pre><code>` for pseudocode/code blocks

### General Rules:
- No `<html>`, `<head>`, `<body>` tags
- All links need `target="_blank"`
- Only use content from input - don't invent anything
- Citations in [key] format will be converted to links automatically

## Output:
Generate only the HTML content as shown:

```html
<h2 class="paper-title">Title Text</h2>

<section>
  <h2>Abstract</h2>
  <p>Abstract content...</p>
</section>

<section>
  <h2>Introduction</h2>
  <p>Introduction content...</p>
</section>
```"""
