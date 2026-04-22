
import io
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from django.core.files.base import ContentFile


def overlay_text_on_image_file(content_file, text):
    content_file.seek(0)

    # Open image
    image = Image.open(io.BytesIO(content_file.read())).convert("RGBA")
    width, height = image.size

    # Load font
    base_dir = Path(__file__).resolve().parent.parent
    font_path = base_dir / "email_config" / "templates" / "font" / "Poppins" / "Poppins-Bold.ttf"

    font_size = max(12, width // 25)
    try:
        font = ImageFont.truetype(str(font_path), font_size)
    except:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(image)

    # Wrap text
    lines = []
    for line in text.split("\n"):
        lines.extend(textwrap.wrap(line, width=30))

    # Calculate line height once
    bbox = draw.textbbox((0, 0), "Ay", font=font)
    line_height = bbox[3] - bbox[1] + 5
    total_text_height = line_height * len(lines)

    gradient_height = total_text_height + 20

    # ✅ Create transparent gradient using numpy (FAST)
    gradient = np.zeros((gradient_height, width, 4), dtype=np.uint8)

    for y in range(gradient_height):
        alpha = int(180 * (y / gradient_height))  # fade from transparent → dark
        gradient[y, :, 3] = alpha  # only alpha channel

    gradient_img = Image.fromarray(gradient, mode="RGBA")

    # Paste gradient at bottom
    image.paste(gradient_img, (0, height - gradient_height), gradient_img)

    # Draw text
    x = 10
    y = height - gradient_height + 10

    for line in lines:
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
        y += line_height

    # Save output (keeps transparency)
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)

    return ContentFile(output.read(), name=content_file.name)
