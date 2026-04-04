import base64
from unittest.mock import patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

import image2svg_mcp.server
from image2svg_mcp.server import mcp, _strip_data_uri_prefix


@pytest.fixture
def client():
    return Client(mcp)


@pytest.mark.asyncio
async def test_convert_base64(client, red_square_b64):
    async with client:
        result = await client.call_tool(
            "convert_image_to_svg",
            {"image_base64": red_square_b64},
        )
        svg_text = result.content[0].text
        assert "<svg" in svg_text
        assert "</svg>" in svg_text


@pytest.mark.asyncio
async def test_neither_input_provided(client):
    async with client:
        with pytest.raises(ToolError):
            await client.call_tool("convert_image_to_svg", {})


@pytest.mark.asyncio
async def test_both_inputs_provided(client, red_square_b64):
    async with client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "convert_image_to_svg",
                {"image_base64": red_square_b64, "image_url": "http://example.com/img.png"},
            )


@pytest.mark.asyncio
async def test_invalid_base64(client):
    async with client:
        with pytest.raises(ToolError):
            await client.call_tool(
                "convert_image_to_svg",
                {"image_base64": "not-valid-base64!!!"},
            )


@pytest.mark.asyncio
async def test_custom_parameters(client, red_square_b64):
    async with client:
        result = await client.call_tool(
            "convert_image_to_svg",
            {
                "image_base64": red_square_b64,
                "colormode": "binary",
                "mode": "polygon",
                "filter_speckle": 10,
            },
        )
        svg_text = result.content[0].text
        assert "<svg" in svg_text


@pytest.mark.asyncio
async def test_data_uri_prefix_stripping(client, red_square_b64):
    data_uri = f"data:image/png;base64,{red_square_b64}"
    async with client:
        result = await client.call_tool(
            "convert_image_to_svg",
            {"image_base64": data_uri},
        )
        svg_text = result.content[0].text
        assert "<svg" in svg_text


@pytest.mark.asyncio
async def test_url_fetch(client, red_square_png_bytes):
    """Test URL fetching path with a mocked HTTP response."""

    class MockResponse:
        status_code = 200
        headers = {"content-length": str(len(red_square_png_bytes))}

        def raise_for_status(self):
            pass

        async def aiter_bytes(self):
            yield red_square_png_bytes

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class MockClient:
        def __init__(self, **kwargs):
            pass

        def stream(self, method, url):
            return MockResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    with patch("image2svg_mcp.server.httpx.AsyncClient", MockClient):
        async with client:
            result = await client.call_tool(
                "convert_image_to_svg",
                {"image_url": "http://example.com/test.png"},
            )
            svg_text = result.content[0].text
            assert "<svg" in svg_text


@pytest.mark.asyncio
async def test_file_url_disabled_by_default(client):
    """file:// URLs are rejected when --allow-local-files-path is not set."""
    async with client:
        with pytest.raises(ToolError, match="--allow-local-files-path"):
            await client.call_tool(
                "convert_image_to_svg",
                {"image_url": "file:///tmp/test.png"},
            )


@pytest.mark.asyncio
async def test_file_url_enabled(client, red_square_png_bytes, tmp_path):
    """file:// URLs work when path is inside allowed directory."""
    img_file = tmp_path / "test.png"
    img_file.write_bytes(red_square_png_bytes)

    with patch.object(image2svg_mcp.server, "_allow_local_files_path", tmp_path.resolve()):
        async with client:
            result = await client.call_tool(
                "convert_image_to_svg",
                {"image_url": f"file://{img_file}"},
            )
            svg_text = result.content[0].text
            assert "<svg" in svg_text


@pytest.mark.asyncio
async def test_file_url_not_found(client, tmp_path):
    """file:// with non-existent path inside allowed dir raises ToolError."""
    with patch.object(image2svg_mcp.server, "_allow_local_files_path", tmp_path.resolve()):
        async with client:
            with pytest.raises(ToolError, match="File not found"):
                await client.call_tool(
                    "convert_image_to_svg",
                    {"image_url": f"file://{tmp_path}/nonexistent.png"},
                )


@pytest.mark.asyncio
async def test_file_url_relative_to_allowed_path(client, red_square_png_bytes, tmp_path):
    """file:// with an external path resolves relative to allowed dir if file exists there."""
    allowed = tmp_path / "allowed"
    subdir = allowed / "d" / "e"
    subdir.mkdir(parents=True)
    img_file = subdir / "f.png"
    img_file.write_bytes(red_square_png_bytes)

    with patch.object(image2svg_mcp.server, "_allow_local_files_path", allowed.resolve()):
        async with client:
            result = await client.call_tool(
                "convert_image_to_svg",
                {"image_url": "file:///d/e/f.png"},
            )
            svg_text = result.content[0].text
            assert "<svg" in svg_text


@pytest.mark.asyncio
async def test_file_url_outside_allowed_path(client, red_square_png_bytes, tmp_path):
    """file:// outside the allowed directory is rejected as not found."""
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    img_file = outside / "secret.png"
    img_file.write_bytes(red_square_png_bytes)

    with patch.object(image2svg_mcp.server, "_allow_local_files_path", allowed.resolve()):
        async with client:
            with pytest.raises(ToolError, match="File not found"):
                await client.call_tool(
                    "convert_image_to_svg",
                    {"image_url": f"file://{img_file}"},
                )


@pytest.mark.asyncio
async def test_file_url_path_traversal(client, red_square_png_bytes, tmp_path):
    """Path traversal via .. is blocked after normalization."""
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    img_file = outside / "secret.png"
    img_file.write_bytes(red_square_png_bytes)

    traversal_url = f"file://{allowed}/../outside/secret.png"
    with patch.object(image2svg_mcp.server, "_allow_local_files_path", allowed.resolve()):
        async with client:
            with pytest.raises(ToolError, match="File not found"):
                await client.call_tool(
                    "convert_image_to_svg",
                    {"image_url": traversal_url},
                )


@pytest.mark.asyncio
async def test_file_url_too_large(client, tmp_path):
    """file:// with a file exceeding 5MB raises ToolError."""
    big_file = tmp_path / "big.png"
    big_file.write_bytes(b"\x00" * (5 * 1024 * 1024 + 1))

    with patch.object(image2svg_mcp.server, "_allow_local_files_path", tmp_path.resolve()):
        async with client:
            with pytest.raises(ToolError, match="File too large"):
                await client.call_tool(
                    "convert_image_to_svg",
                    {"image_url": f"file://{big_file}"},
                )


def test_strip_data_uri_prefix():
    assert _strip_data_uri_prefix("data:image/png;base64,abc123") == "abc123"
    assert _strip_data_uri_prefix("data:image/jpeg;base64,xyz") == "xyz"
    assert _strip_data_uri_prefix("abc123") == "abc123"
    assert _strip_data_uri_prefix("") == ""
