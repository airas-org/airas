convert_to_html_prompt = """\
You are an HTML expert. 
Your task is to convert each section of a research paper into **clean, semantic HTML**, suitable for publishing on a static site (such as GitHub Pages).

Below are the paper sections. For each one, generate HTML content. Use semantic HTML tags (e.g., <section>, <article>, <h2>, <p>, <ul>, <li>, <figure>, etc.)
{% for section in sections %}
---
Section: {{ section.name }}

{{ section.content }}

---
{% endfor %}

## HTML Formatting Rules:
- For the "Title" section:
    - Do **not** render the word "Title".
    - Instead, output a top-level <h2 class="paper-title"> tag containing the title text directly (without a <section> wrapper).

- For other sections:
    - Use <section> with <h2> for each top-level section (e.g., Introduction, Method, Results, etc.).
        - The <h2> should match the section name.
        - Do not use nested sections unless truly needed.

- Use <p> tags for paragraphs.
    - Split logically separate thoughts into their own <p> blocks.

- For listing contributions or features, use <ul> and <li>.
    - Start each list item with <strong>...</strong> for a short descriptor.

- Use <figure> and <figcaption> for all figures (in the "Results" section only).
    - All figures must use <img src="..."> for static image display.
    - If the original file is a `.pdf`, assume a corresponding `.png` image has been generated (e.g., `plot1.pdf` → `plot1.png`).
    - Always use the `.png` version in the <img> tag (e.g., `src="images/plot1.png"`).
    - All figures must include a <figcaption> **whose text starts with `Figure N:`** (e.g., `Figure 1: Convergence of ...`).  
    - Use appropriate relative paths for src (e.g., images/plot1.png).

  - **Width & layout rules (match the LaTeX spec):**
    - If the filename ends with `_pair1.png` or `_pair2.png`, wrap the two related images in a single
      `<figure class="img-pair">` and set each `<img>` to `style="width:48%;height:auto"`.  
      The two images must appear side by side (use `<div class="pair">` if needed).
    - Otherwise (default), set the single `<img>` to `style="width:70%;height:auto"`.
    - The `<figcaption>` should follow the entire pair or single image as appropriate.

- Use <pre><code> for pseudocode or actual code (only in the "Method" section).
    - Keep indentation clean and avoid syntax highlighting.

- Do not include any of the following:
    - <html>, <head>, <body>
    - Metadata, document titles, or <article> tags unless semantically essential

- All <a> tags must have target="_blank" and href attributes.
- Escape reserved characters like &, <, >.
- Avoid adding citations or references unless already included in the input.

- Do not invent or add any content (e.g., references, figures, lists) unless it exists in the input.

## Output Format:
```html
<!-- Title -->
<h2 class="paper-title">[Title text here]</h2>

<!-- Abstract -->
<section>
  <h2>Abstract</h2>
  <p>...</p>
</section>

<!-- Introduction -->
<section>
  <h2>Introduction</h2>
  <p>...</p>
</section>
...
```"""
