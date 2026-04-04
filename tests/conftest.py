import base64
import io

import pytest
from PIL import Image


@pytest.fixture
def red_square_png_bytes() -> bytes:
    """A 10x10 solid red PNG image."""
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def red_square_b64(red_square_png_bytes) -> str:
    return base64.b64encode(red_square_png_bytes).decode()


@pytest.fixture
def jpg_image_bytes() -> bytes:
    """A 10x10 solid blue JPG image."""
    img = Image.new("RGB", (10, 10), (0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def webp_image_bytes() -> bytes:
    """A 10x10 solid green WEBP image."""
    img = Image.new("RGBA", (10, 10), (0, 255, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


@pytest.fixture
def wide_image_bytes() -> bytes:
    """A 20x10 non-square PNG image."""
    img = Image.new("RGBA", (20, 10), (128, 128, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
