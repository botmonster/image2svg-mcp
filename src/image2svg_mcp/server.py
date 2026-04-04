"""FastMCP server exposing the image-to-SVG conversion tool."""

import base64
import re
import urllib.parse
from pathlib import Path
from typing import Annotated

import httpx
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from pydantic import Field

from image2svg_mcp.convert import convert_image_bytes_to_svg

MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

_allow_local_files_path: Path | None = None

mcp = FastMCP("image2svg")


def _strip_data_uri_prefix(data: str) -> str:
    """Strip optional data URI prefix like 'data:image/png;base64,'."""
    return re.sub(r"^data:[^;]+;base64,", "", data)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    }
)
async def convert_image_to_svg(
    image_base64: Annotated[str | None, Field(
        description="Base64-encoded image data (PNG, JPG, or WEBP). "
                    "Provide this OR image_url, not both.",
    )] = None,
    image_url: Annotated[str | None, Field(
        description="URL to fetch the image from (PNG, JPG, or WEBP). "
                    "Provide this OR image_base64, not both.",
    )] = None,
    colormode: Annotated[str, Field(
        description="Color mode: 'color' for full color, 'binary' for black/white line art",
    )] = "color",
    mode: Annotated[str, Field(
        description="Tracing mode: 'spline' (smooth curves), 'polygon' (straight edges), "
                    "or 'none' (pixel-perfect)",
    )] = "spline",
    filter_speckle: Annotated[int, Field(
        ge=0, le=128,
        description="Remove speckles of this many pixels or fewer. "
                    "Higher = cleaner but loses small details. Default 4.",
    )] = 4,
    color_precision: Annotated[int, Field(
        ge=1, le=12,
        description="Number of significant bits for color quantization. "
                    "Lower = fewer colors, simpler SVG. Default 6.",
    )] = 6,
    layer_difference: Annotated[int, Field(
        ge=0, le=128,
        description="Color difference threshold for merging layers. "
                    "Higher = fewer layers, simpler SVG. Default 16.",
    )] = 16,
    corner_threshold: Annotated[int, Field(
        ge=0, le=180,
        description="Angle threshold in degrees for detecting corners. Default 60.",
    )] = 60,
    length_threshold: Annotated[float, Field(
        ge=3.5, le=10.0,
        description="Minimum path segment length. Default 4.0.",
    )] = 4.0,
    splice_threshold: Annotated[int, Field(
        ge=0, le=180,
        description="Angle threshold for splicing splines. Default 45.",
    )] = 45,
    path_precision: Annotated[int, Field(
        ge=1, le=12,
        description="Decimal precision for SVG path coordinates. "
                    "Lower = smaller file size. Default 8.",
    )] = 8,
    hierarchical: Annotated[str, Field(
        description="Layer arrangement: 'stacked' (overlapping) or 'cutout' (non-overlapping)",
    )] = "stacked",
    max_iterations: Annotated[int, Field(
        ge=1, le=100,
        description="Maximum curve fitting iterations. "
                    "Higher = more accurate but slower. Default 10.",
    )] = 10,
    ctx: Context | None = None,
) -> str:
    """Convert a raster image (PNG, JPG, or WEBP) to SVG vector format.

    Accepts either base64-encoded image data or a URL. Returns the SVG
    content as a string. Adjust tracing parameters to control the
    fidelity and complexity of the output.
    """
    if image_base64 and image_url:
        raise ToolError("Provide either image_base64 or image_url, not both.")
    if not image_base64 and not image_url:
        raise ToolError("Provide either image_base64 or image_url.")

    if image_base64:
        if ctx:
            await ctx.info("Decoding base64 image data")
        image_base64 = _strip_data_uri_prefix(image_base64)
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            raise ToolError(f"Invalid base64 data: {e}")
    else:
        if ctx:
            await ctx.info(f"Fetching image from URL: {image_url}")

        if image_url.startswith("file://"):
            if _allow_local_files_path is None:
                raise ToolError(
                    "Local file access is disabled. "
                    "Start the server with --allow-local-files-path to enable file:// URLs."
                )
            parsed = urllib.parse.urlparse(image_url)
            raw_path = Path(urllib.parse.unquote(parsed.path))
            file_path = raw_path.resolve()
            if not file_path.is_relative_to(_allow_local_files_path):
                # Try as a path relative to the allowed directory
                file_path = (_allow_local_files_path / raw_path.relative_to(raw_path.anchor)).resolve()
            if not file_path.is_relative_to(_allow_local_files_path):
                raise ToolError(f"File not found: {raw_path}")
            if not file_path.is_file():
                raise ToolError(f"File not found: {raw_path}")
            file_size = file_path.stat().st_size
            if file_size > MAX_DOWNLOAD_BYTES:
                raise ToolError(
                    f"File too large ({file_size} bytes). "
                    f"Maximum allowed: {MAX_DOWNLOAD_BYTES // (1024 * 1024)}MB."
                )
            image_bytes = file_path.read_bytes()
        else:
            try:
                async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                    async with client.stream("GET", image_url) as response:
                        response.raise_for_status()

                        content_length = response.headers.get("content-length")
                        if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                            raise ToolError(
                                f"Image too large ({int(content_length)} bytes). "
                                f"Maximum allowed: {MAX_DOWNLOAD_BYTES // (1024 * 1024)}MB."
                            )

                        chunks = []
                        total = 0
                        async for chunk in response.aiter_bytes():
                            total += len(chunk)
                            if total > MAX_DOWNLOAD_BYTES:
                                raise ToolError(
                                    f"Image download exceeded {MAX_DOWNLOAD_BYTES // (1024 * 1024)}MB limit."
                                )
                            chunks.append(chunk)
                        image_bytes = b"".join(chunks)
            except ToolError:
                raise
            except httpx.HTTPError as e:
                raise ToolError(f"Failed to fetch image from URL: {e}")

    if ctx:
        await ctx.info("Converting image to SVG")
        await ctx.report_progress(progress=1, total=3)

    try:
        result = convert_image_bytes_to_svg(
            image_bytes,
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
    except Exception as e:
        raise ToolError(f"Conversion failed: {e}")

    if ctx:
        await ctx.report_progress(progress=3, total=3)
        await ctx.info(
            f"Conversion complete: {result.width}x{result.height}px source, "
            f"{len(result.svg_content)} bytes SVG"
        )

    return result.svg_content


def main():
    import argparse

    parser = argparse.ArgumentParser(description="image2svg MCP server")
    parser.add_argument(
        "--allow-local-files-path",
        type=str,
        default=None,
        help="Allow file:// URLs from this directory (and subdirectories)",
    )
    args, _ = parser.parse_known_args()

    global _allow_local_files_path
    if args.allow_local_files_path:
        _allow_local_files_path = Path(args.allow_local_files_path).resolve()

    mcp.run()
