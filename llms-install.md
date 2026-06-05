# LLM Installation Guide — image2svg-mcp

This guide is for an AI agent (Cline, Claude, etc.) installing this MCP server for a user.
The server converts raster images (PNG, JPG, WEBP, TIFF) to SVG vector graphics.

## Prerequisites

The server runs via `uvx`, which is part of [uv](https://docs.astral.sh/uv/). If `uvx` is not
available, install uv first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

`uvx image2svg-mcp` fetches the published PyPI package on first run — no manual clone or build.

## Install (stdio, default)

Add this block to the host's MCP servers configuration (e.g. Cline's `cline_mcp_settings.json`,
or `settings.json` for Claude):

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

No API keys, tokens, or environment variables are required.

## Optional: local file access

By default the server only accepts images as base64 data or `http(s)://` URLs. To let it read
local images via `file://` URLs, pass a directory to allow. Only files inside that directory
(and its subdirectories) become accessible; paths are normalized to block directory traversal.

```json
{
  "mcpServers": {
    "image2svg": {
      "command": "uvx",
      "args": ["image2svg-mcp", "--allow-local-files-path", "/absolute/path/to/images"]
    }
  }
}
```

## Verify

After the host reloads its MCP config, confirm the server exposes one tool:

- `convert_image_to_svg` — converts a raster image to SVG. Accepts `image_base64` **or**
  `image_url`, plus optional tracing parameters (`colormode`, `mode`, `filter_speckle`,
  `color_precision`, etc.). Returns the SVG document as a string.

A quick functional check — ask the model to run:

> Convert this base64 image to SVG: iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAO0lEQVR4nGP8z8Dwn4EIwESMIqwKGRn+MzBisYQJXRE2NopCbKYgi5Huxv8MjBiSyGJMuCTQNTJSPRwBCjYOD5JU5rIAAAAASUVORK5CYII=

A successful install returns `<svg ...>...</svg>` content.

## Docker alternative (HTTP transport)

If the host prefers HTTP instead of stdio:

```bash
docker run -p 8000:8000 ghcr.io/botmonster/image2svg-mcp
```

Then point the host at `http://localhost:8000/mcp` using the HTTP transport.
