"""Pure image-to-SVG conversion logic."""

import io
from dataclasses import dataclass

import vtracer
from PIL import Image


@dataclass
class ConversionResult:
    svg_content: str
    width: int
    height: int


def convert_image_bytes_to_svg(
    image_bytes: bytes,
    *,
    colormode: str = "color",
    hierarchical: str = "stacked",
    mode: str = "spline",
    filter_speckle: int = 4,
    color_precision: int = 6,
    layer_difference: int = 16,
    corner_threshold: int = 60,
    length_threshold: float = 4.0,
    max_iterations: int = 10,
    splice_threshold: int = 45,
    path_precision: int = 8,
) -> ConversionResult:
    """Convert raw image bytes (any supported format) to SVG.

    Normalizes the input to PNG via Pillow before passing to the
    vectorization engine. Returns a ConversionResult with the SVG
    string and source dimensions.
    """
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGBA")
    width, height = img.size

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    svg_content = vtracer.convert_raw_image_to_svg(
        png_bytes,
        img_format="png",
        colormode=colormode,
        hierarchical=hierarchical,
        mode=mode,
        filter_speckle=filter_speckle,
        color_precision=color_precision,
        layer_difference=layer_difference,
        corner_threshold=corner_threshold,
        length_threshold=length_threshold,
        max_iterations=max_iterations,
        splice_threshold=splice_threshold,
        path_precision=path_precision,
    )

    return ConversionResult(
        svg_content=svg_content,
        width=width,
        height=height,
    )
