"""Збереження та показ фотографій страв у межах папки проєкту."""
from pathlib import Path
from uuid import uuid4

import customtkinter as ctk
from PIL import Image, ImageOps, UnidentifiedImageError

PROJECT_DIR = Path(__file__).resolve().parent.parent
PHOTOS_DIR = PROJECT_DIR / "assets" / "menu_photos"
MAX_SOURCE_SIZE = 12 * 1024 * 1024  # 12 MiB
Image.MAX_IMAGE_PIXELS = 30_000_000


def resolve_photo_path(relative_path):
    if not relative_path:
        return None
    try:
        candidate = (PROJECT_DIR / relative_path).resolve()
        if candidate.is_relative_to(PHOTOS_DIR.resolve()) and candidate.is_file():
            return candidate
    except (OSError, ValueError):
        pass
    return None


def store_photo(file_path):
    """Копіює обраний файл як PNG; повертає відносний шлях для SQLite."""
    source = Path(file_path)
    if not source.is_file() or source.stat().st_size > MAX_SOURCE_SIZE:
        raise ValueError("Виберіть зображення розміром до 12 МБ")
    try:
        with Image.open(source) as original:
            if original.format not in ("JPEG", "PNG", "WEBP", "BMP", "GIF"):
                raise ValueError("Підтримуються JPG, PNG, WEBP, BMP або GIF")
            original.load()
            photo = ImageOps.exif_transpose(original).convert("RGBA")
            photo.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
            dest = PHOTOS_DIR / f"{uuid4().hex}.png"
            photo.save(dest, format="PNG", optimize=True)
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError("Не вдалося відкрити зображення") from exc
    return dest.relative_to(PROJECT_DIR).as_posix()


def load_thumbnail(path, size=(44, 44), *, selected=False):
    """CTkImage; selected=True дозволяє показати нове, ще не збережене фото."""
    if not path:
        return None
    source = Path(path) if selected else resolve_photo_path(path)
    if not source or not source.is_file():
        return None
    try:
        with Image.open(source) as img:
            img.load()
            preview = ImageOps.exif_transpose(img).convert("RGBA")
            preview.thumbnail(size, Image.Resampling.LANCZOS)
            # Прозоре поле потрібного розміру; фото по центру без розтягування.
            canvas = Image.new("RGBA", size, (255, 255, 255, 0))
            x = (size[0] - preview.width) // 2
            y = (size[1] - preview.height) // 2
            canvas.alpha_composite(preview, (x, y))
            return ctk.CTkImage(light_image=canvas, dark_image=canvas, size=size)
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError):
        return None
