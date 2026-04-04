import io

import pytest
from PIL import Image

from image2svg_mcp.convert import convert_image_bytes_to_svg


def test_basic_png_conversion(red_square_png_bytes):
    result = convert_image_bytes_to_svg(red_square_png_bytes)
    assert "<svg" in result.svg_content
    assert "</svg>" in result.svg_content
    assert result.width == 10
    assert result.height == 10


def test_jpg_conversion(jpg_image_bytes):
    result = convert_image_bytes_to_svg(jpg_image_bytes)
    assert "<svg" in result.svg_content
    assert "</svg>" in result.svg_content
    assert result.width == 10
    assert result.height == 10


def test_webp_conversion(webp_image_bytes):
    result = convert_image_bytes_to_svg(webp_image_bytes)
    assert "<svg" in result.svg_content
    assert "</svg>" in result.svg_content
    assert result.width == 10
    assert result.height == 10


def test_binary_colormode(red_square_png_bytes):
    result = convert_image_bytes_to_svg(red_square_png_bytes, colormode="binary")
    assert "<svg" in result.svg_content
    assert "</svg>" in result.svg_content


def test_polygon_mode(red_square_png_bytes):
    result = convert_image_bytes_to_svg(red_square_png_bytes, mode="polygon")
    assert "<svg" in result.svg_content
    assert "</svg>" in result.svg_content


def test_filter_speckle_effect(red_square_png_bytes):
    result_low = convert_image_bytes_to_svg(red_square_png_bytes, filter_speckle=0)
    result_high = convert_image_bytes_to_svg(red_square_png_bytes, filter_speckle=100)
    # Higher speckle filter should produce same or shorter SVG
    assert len(result_high.svg_content) <= len(result_low.svg_content)


def test_invalid_bytes():
    with pytest.raises(Exception):
        convert_image_bytes_to_svg(b"not an image")


def test_nonsquare_dimensions(wide_image_bytes):
    result = convert_image_bytes_to_svg(wide_image_bytes)
    assert result.width == 20
    assert result.height == 10
    assert "<svg" in result.svg_content


def test_cmyk_input():
    """CMYK images should be converted to RGBA successfully."""
    img = Image.new("CMYK", (10, 10), (0, 0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="TIFF")
    cmyk_bytes = buf.getvalue()

    result = convert_image_bytes_to_svg(cmyk_bytes)
    assert "<svg" in result.svg_content
    assert result.width == 10
    assert result.height == 10
