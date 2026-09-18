import asyncio
from io import BytesIO
from pathlib import Path
from typing import Any

import vl_convert as vlc
from PIL import Image

from airas.infra.kroki_client import KrokiClient


def _png_to_pdf(png: bytes) -> bytes:
    buffer = BytesIO()
    with Image.open(BytesIO(png)) as image:
        if image.mode != "RGB":
            # Flatten transparency onto white instead of the black that a
            # plain RGB conversion would produce.
            rgba = image.convert("RGBA")
            rgb = Image.new("RGB", rgba.size, (255, 255, 255))
            rgb.paste(rgba, mask=rgba.getchannel("A"))
        else:
            rgb = image.copy()
    rgb.save(buffer, format="PDF")
    return buffer.getvalue()


async def render_diagram(
    kroki_client: KrokiClient, diagram_type: str, diagram_source: str, output_path: str
) -> dict[str, Any]:
    path = Path(output_path).expanduser()
    suffix = path.suffix.lower().lstrip(".")
    if suffix not in ("pdf", "svg", "png"):
        raise ValueError("output_path must end with .pdf, .svg, or .png")
    if suffix == "pdf":
        svg = await kroki_client.arender(diagram_type, diagram_source, "svg")
        if b"<foreignObject" in svg:
            # HTML-in-SVG labels (mermaid etc.) are dropped by the local
            # SVG-to-PDF converter, so rasterize via Kroki's PNG instead.
            png = await kroki_client.arender(diagram_type, diagram_source, "png")
            data = await asyncio.to_thread(_png_to_pdf, png)
        else:
            data = await asyncio.to_thread(vlc.svg_to_pdf, svg.decode("utf-8"))
    else:
        data = await kroki_client.arender(diagram_type, diagram_source, suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"output_path": str(path), "bytes_written": len(data)}
