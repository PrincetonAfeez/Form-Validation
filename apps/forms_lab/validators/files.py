""" File validation. """

from __future__ import annotations

from io import BytesIO

from django.core.exceptions import ValidationError

from .registry import register

try:
    import magic
except ImportError:  # pragma: no cover - optional dependency fallback
    magic = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is declared in requirements
    Image = None

MAX_FILE_SIZE = 5 * 1024 * 1024


def sniff_mime(file) -> str:
    current = file.tell() if hasattr(file, "tell") else 0
    head = file.read(2048)
    if hasattr(file, "seek"):
        file.seek(current)
    if magic:
        return magic.from_buffer(head, mime=True)
    if head.startswith(b"%PDF"):
        return "application/pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "image/gif"
    return getattr(file, "content_type", "application/octet-stream")


@register("file.magic_bytes", examples=("avatar.png", "resume.pdf"))
def validate_magic_bytes(file, allowed_mimes: set[str] | None = None) -> None:
    """Sniffs magic bytes instead of trusting the browser-provided content type."""
    allowed_mimes = allowed_mimes or {"image/png", "image/jpeg", "application/pdf"}
    mime = sniff_mime(file)
    if mime not in allowed_mimes:
        raise ValidationError("File type is not allowed.", code="bad_mime")


@register("file.image_dimensions", examples=("avatar<=1200x1200",))
def validate_image_dimensions(file, max_w: int = 1200, max_h: int = 1200) -> None:
    """Rejects images larger than the configured width and height."""
    if Image is None:
        return
    current = file.tell() if hasattr(file, "tell") else 0
    data = file.read()
    if hasattr(file, "seek"):
        file.seek(current)
    try:
        image = Image.open(BytesIO(data))
    except Exception as exc:
        if sniff_mime(file).startswith("image/"):
            raise ValidationError(
                "Could not read image file.",
                code="image_unreadable",
            ) from exc
        return
    width, height = image.size
    if width > max_w or height > max_h:
        raise ValidationError(
            f"Image must be at most {max_w}x{max_h}px.",
            code="image_dimensions",
        )


@register("file.size", examples=("max 5 MB",))
def validate_file_size(file, max_bytes: int = MAX_FILE_SIZE) -> None:
    """Rejects files over the demo's 5 MB per-file limit."""
    if getattr(file, "size", 0) > max_bytes:
        raise ValidationError("File must be 5 MB or smaller.", code="file_size")
