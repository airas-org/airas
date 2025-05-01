import os
import logging
from jinja2 import Environment

logger = logging.getLogger(__name__)


def _wrap_in_html_template(paper_html_content: str) -> str:
    base_template = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <title>Research Paper</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 2rem auto;
      max-width: 800px;
      padding: 0 1rem;
      line-height: 1.6;
      color: #333;
      background-color: #fff;
    }
    h2.paper-title {
      font-size: 1.8em;
      font-weight: 700;
      text-align: center;
      margin-bottom: 0.5em;
      border-bottom: none;
    }
    h2 {
      border-bottom: 2px solid #ddd;
      padding-bottom: 0.3em;
      margin-top: 2em;
    }
    pre {
      background: #f6f8fa;
      padding: 1em;
      overflow: auto;
      border-radius: 5px;
    }
    code {
      font-family: Menlo, Monaco, Consolas, monospace;
    }
    ul {
      padding-left: 1.5em;
    }
    figure {
      text-align: center;
      margin: 1.5em 0;
    }
    figcaption {
      font-size: 0.9em;
      color: #666;
    }
  </style>
</head>
<body>
{{ content }}
</body>
</html>"""
    env = Environment()
    template = env.from_string(base_template)
    return template.render(content=paper_html_content)


def _save_index_html(content: str, save_dir: str) -> None:
    os.makedirs(save_dir, exist_ok=True)
    html_path = os.path.join(save_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Saved HTML to: {html_path}")


def render_html(paper_html_content: str, save_dir: str) -> str:
    full_html = _wrap_in_html_template(paper_html_content)
    _save_index_html(full_html, save_dir)
    return full_html
