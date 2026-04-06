# image2svg-mcp

[![PyPI](https://img.shields.io/pypi/v/image2svg-mcp)](https://pypi.org/project/image2svg-mcp/)
[![Docker](https://github.com/botmonster/image2svg-mcp/actions/workflows/docker.yml/badge.svg)](https://github.com/botmonster/image2svg-mcp/actions/workflows/docker.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Tests](https://github.com/botmonster/image2svg-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/botmonster/image2svg-mcp/actions/workflows/tests.yml)

An MCP server that converts raster images (PNG, JPG, WEBP) to scalable SVG vector graphics.

## Features

- Accepts images as **base64-encoded data** or **URL**
- Supports PNG, JPG, JPEG, WEBP, TIFF, and other common raster formats
- Full control over vectorization parameters (color precision, speckle filtering, tracing mode, etc.)
- Handles `data:image/...;base64,` URI prefixes automatically
- Streams URL downloads with a 5 MB size limit
- Optional `file://` URL support for local images (opt-in via `--allow-local-files-path`)

## Usage

To see it in action check [converting image to svg online](https://botmonster.com/image2svg/).

### Claude Code & Claude Desktop

Add to your `settings.json`:


```json
{
  "mcpServers": {
    "image2svg": {
      "command": "uvx",
      "args": ["image2svg-mcp"]
    }
  }
}
```
for **Claude Code** add using command line:
```bash
claude mcp add image2svg --scope user -- uvx image2svg-mcp
```
with access to local files:
```bash
claude mcp add image2svg --scope user -- uvx image2svg-mcp --allow-local-files-path /home/user/images
```

### Docker

Run as an HTTP server:

```bash
docker run -p 8000:8000 ghcr.io/botmonster/image2svg-mcp
```

With local file access:

```bash
docker run -p 8000:8000 -v /home/user/images:/images ghcr.io/botmonster/image2svg-mcp --allow-local-files-path /images
claude mcp add image2svg --transport http --scope user http://localhost:8000/mcp
```

This enables prompts like:

> Convert this local file to SVG: file://logo.png

Only files inside the specified directory (and its subdirectories) are accessible. Paths are normalized to prevent directory traversal. Without this flag, `file://` URLs are rejected.

## Example Prompts

Here are some examples of what you can tell an LLM to do with this tool:

### 1. Simple image-to-SVG conversion

> Generate an image of a sunset over mountains, then convert it to SVG.

The LLM will generate a raster image and then use the `convert_image_to_svg` tool with default settings to produce a clean vector version.

### 2. Fine-tuned conversion with specific parameters

> Create a logo with a blue circle and a white star inside it. Now convert it to SVG using binary colormode for crisp edges and set filter_speckle to 10 to remove noise.

This uses `colormode: "binary"` for black/white line art style output, which works great for logos and icons. The higher `filter_speckle` value removes small artifacts.

### 3. Convert from URL with minimalist style

> Convert this image to a simplified SVG with low color precision for a minimalist poster look: https://example.com/photo.png

Using `color_precision: 3` reduces the number of colors dramatically, producing an artistic posterized vector effect. Great for stylized illustrations.

### 4. Convert a base64 image directly

> Convert this base64 image to SVG: iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAO0lEQVR4nGP8z8Dwn4EIwESMIqwKGRn+MzBisYQJXRE2NopCbKYgi5Huxv8MjBiSyGJMuCTQNTJSPRwBCjYOD5JU5rIAAAAASUVORK5CYII=

This is a 10x10 red square with a blue circle in the middle. Useful for testing the tool with inline image data — no URL needed.

## Tool Parameters

| Parameter | Type | Default | Range | Description |
|---|---|---|---|---|
| `image_base64` | string | - | - | Base64-encoded image data. Provide this OR `image_url`. |
| `image_url` | string | - | - | URL to fetch the image from (`http://`, `https://`, or `file://` when enabled). Provide this OR `image_base64`. |
| `colormode` | string | `"color"` | `color`, `binary` | Full color or black/white line art |
| `mode` | string | `"spline"` | `spline`, `polygon`, `none` | Tracing mode: smooth curves, straight edges, or pixel-perfect |
| `filter_speckle` | int | `4` | 0-128 | Remove speckles of N pixels or fewer |
| `color_precision` | int | `6` | 1-12 | Color quantization bits. Lower = fewer colors, simpler SVG |
| `layer_difference` | int | `16` | 0-128 | Color difference for merging layers |
| `corner_threshold` | int | `60` | 0-180 | Angle threshold for corner detection (degrees) |
| `length_threshold` | float | `4.0` | 3.5-10.0 | Minimum path segment length |
| `splice_threshold` | int | `45` | 0-180 | Angle threshold for splicing splines |
| `path_precision` | int | `8` | 1-12 | Decimal precision for SVG coordinates |
| `hierarchical` | string | `"stacked"` | `stacked`, `cutout` | Layer arrangement mode |
| `max_iterations` | int | `10` | 1-100 | Max curve fitting iterations |

## Development

### Installation

```bash
git clone https://github.com/botmonster/image2svg-mcp.git
cd image2svg-mcp
uv sync
```

### Run tests

```bash
uv run pytest tests/ -v
```

### Run the MCP Inspector

```bash
uv run fastmcp dev inspector src/image2svg_mcp/server.py:mcp
```

## License

Apache 2.0 - see [LICENSE](LICENSE)
