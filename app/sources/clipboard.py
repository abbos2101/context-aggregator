import tempfile
from pathlib import Path

from AppKit import NSPasteboard
from Foundation import NSURL

# media_type -> file extension
_IMAGE_EXTS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/tiff": ".tiff",
    "image/gif": ".gif",
}

_CLIP_DIR = Path(tempfile.gettempdir()) / "context-ai-clipboard"


class ClipboardError(Exception):
    pass


# Rasm va/yoki matnni macOS clipboardga FILE-URL sifatida qo'yadi.
# Har biri vaqtinchalik faylga yoziladi (rasm + matn .txt), clipboardga
# birga qo'yiladi. Paste qilinganda ikkala fayl bir vaqtda tushadi.
# Returns: ["text"], ["image"] yoki ["image", "text"].
def copy_to_clipboard(
    text: str | None,
    image_bytes: bytes | None,
    image_media_type: str | None,
) -> list[str]:
    if not text and image_bytes is None:
        raise ClipboardError("nothing to copy")

    _CLIP_DIR.mkdir(parents=True, exist_ok=True)

    urls: list = []
    copied: list[str] = []

    if image_bytes is not None:
        ext = _IMAGE_EXTS.get((image_media_type or "").lower())
        if ext is None:
            supported = ", ".join(sorted(_IMAGE_EXTS))
            raise ClipboardError(
                f"unsupported image type: {image_media_type} (supported: {supported})"
            )
        img_path = _CLIP_DIR / f"clip_image{ext}"
        img_path.write_bytes(image_bytes)
        urls.append(NSURL.fileURLWithPath_(str(img_path)))
        copied.append("image")

    if text:
        txt_path = _CLIP_DIR / "clip_text.txt"
        txt_path.write_text(text, encoding="utf-8")
        urls.append(NSURL.fileURLWithPath_(str(txt_path)))
        copied.append("text")

    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    if not pb.writeObjects_(urls):
        raise ClipboardError("pasteboard writeObjects failed")

    return copied
