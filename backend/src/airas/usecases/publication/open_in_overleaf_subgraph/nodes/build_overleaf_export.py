import base64
import html
import io
import zipfile

OVERLEAF_DOCS_URL = "https://www.overleaf.com/docs"

# Overleaf creates the project from a POST because the zip is passed inline as
# a base64 data URL (no public URL needed, so private repositories work). The
# POST must come from the user's browser so the project lands in their
# Overleaf account; this page submits itself on load.
_EXPORT_PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Opening in Overleaf…</title>
  </head>
  <body>
    <p>Sending <strong>{project_name}</strong> to Overleaf…</p>
    <p>If nothing happens, <button type="submit" form="overleaf">click here</button>.</p>
    <form id="overleaf" method="POST" action="{overleaf_docs_url}">
      <input type="hidden" name="snip_uri" value="{zip_data_url}" />
      <input type="hidden" name="snip_name" value="{project_name}" />
    </form>
    <script>
      document.getElementById("overleaf").submit();
    </script>
  </body>
</html>
"""


def build_overleaf_export(
    latex_files: dict[str, bytes],
    project_name: str,
) -> str:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in sorted(latex_files.items()):
            archive.writestr(path, content)
    zip_base64 = base64.b64encode(buffer.getvalue()).decode("ascii")

    return _EXPORT_PAGE_TEMPLATE.format(
        overleaf_docs_url=OVERLEAF_DOCS_URL,
        project_name=html.escape(project_name),
        zip_data_url=f"data:application/zip;base64,{zip_base64}",
    )
