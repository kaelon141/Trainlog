import io
import json
import os

import cairosvg
from flask import send_from_directory
from PIL import Image


def convert_svg_to_png(svg_content):
    # Convert SVG content to PNG byte stream
    png_output = io.BytesIO()
    cairosvg.svg2png(
        bytestring=svg_content, write_to=png_output, output_width=30, output_height=20
    )
    png_output.seek(0)
    return Image.open(png_output)


def generate_sprite(folder):
    svg_dir = os.path.join(folder, "images/flags")
    sprite_folder = os.path.join(folder, "images/flags/sprite")
    sprite_path = os.path.join(sprite_folder, "sprite.png")
    positions_path = os.path.join(sprite_folder, "positions.json")

    # Check if sprite needs to be regenerated
    sprite_mtime = os.path.getmtime(sprite_path) if os.path.exists(sprite_path) else 0
    regenerate = False

    for filename in os.listdir(svg_dir):
        if filename.endswith(".svg"):
            filepath = os.path.join(svg_dir, filename)
            file_mtime = os.path.getmtime(filepath)
            if file_mtime > sprite_mtime:
                regenerate = True
                break

    if not regenerate:
        return send_from_directory(sprite_folder, "sprite.png")

    # List to hold all PNG images and their corresponding country codes
    png_images = []
    country_codes = []

    for filename in sorted(os.listdir(svg_dir)):
        if filename.endswith(".svg"):
            filepath = os.path.join(svg_dir, filename)
            country_code = os.path.splitext(filename)[0]
            with open(filepath, "r", encoding="utf-8") as svg_file:
                svg_content = svg_file.read()
                png_image = convert_svg_to_png(svg_content)
                png_images.append(png_image)
                country_codes.append(country_code)

    # Determine the size of the sprite image
    if not png_images:
        return "No SVG files found.", 404

    fixed_height = 20
    fixed_width = 30  # 3:2 aspect ratio for each flag
    total_height = len(png_images) * fixed_height

    # Create a new blank image with the calculated size
    sprite_image = Image.new("RGBA", (fixed_width, total_height), (255, 255, 255, 0))

    # Dictionary to store the positions of each flag
    positions = {}

    # Paste all PNG images into the sprite image
    y_offset = 0
    for country_code, image in zip(country_codes, png_images):
        sprite_image.paste(image, (0, y_offset))
        positions[country_code] = {"x": 0, "y": y_offset}
        y_offset += fixed_height

    # Save the sprite image to disk
    os.makedirs(sprite_folder, exist_ok=True)
    sprite_image.save(sprite_path)

    # Save the positions to a JSON file
    with open(positions_path, "w", encoding="utf-8") as positions_file:
        json.dump(positions, positions_file, indent=4)

    return send_from_directory(sprite_folder, "sprite.png")
