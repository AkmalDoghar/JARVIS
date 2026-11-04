"""
JARVIS Arc Reactor Icon Generator (Phase 9 & 10)
Generates high-resolution multi-size Windows .ico files dynamically
using Pillow with Iron Man Arc Reactor styling.
"""

import os
from PIL import Image, ImageDraw

ICON_PATH = os.path.join(os.path.dirname(__file__), "jarvis.ico")

def generate_arc_reactor_icon(target_path: str = ICON_PATH) -> str:
    """
    Generate a sleek, futuristic cyan Arc Reactor icon and save as a multi-resolution Windows .ico.
    """
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
    images = []

    for width, height in sizes:
        # Transparent canvas
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Scale factor relative to 64x64 baseline
        scale = width / 64.0

        # 1. Outer Dark Halo Ring
        margin = int(2 * scale)
        draw.ellipse(
            [margin, margin, width - margin, height - margin],
            fill=(2, 6, 23, 240), # Dark slate navy #020617
            outline=(6, 182, 212, 255), # Cyan border
            width=max(1, int(2 * scale))
        )

        # 2. Glowing Inner Concentric Ring
        inner_m = int(10 * scale)
        draw.ellipse(
            [inner_m, inner_m, width - inner_m, height - inner_m],
            outline=(34, 211, 238, 220), # Electric cyan #22d3ee
            width=max(1, int(2 * scale))
        )

        # 3. Arc Reactor Slices (3 radial ticks)
        center_x = width // 2
        center_y = height // 2
        tick_len = int(6 * scale)
        
        # 4. Central Glowing Core
        core_m = int(22 * scale)
        draw.ellipse(
            [core_m, core_m, width - core_m, height - core_m],
            fill=(56, 189, 248, 255), # Vibrant Sky Blue
            outline=(255, 255, 255, 255), # White hot center
            width=max(1, int(1 * scale))
        )

        # 5. Pure white center spark
        spark_m = int(27 * scale)
        draw.ellipse(
            [spark_m, spark_m, width - spark_m, height - spark_m],
            fill=(255, 255, 255, 255)
        )

        images.append(img)

    # Save primary 64x64 image with all lower and higher resolutions embedded
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    images[-1].save(
        target_path,
        format="ICO",
        sizes=[(s[0], s[1]) for s in sizes]
    )
    return target_path

def get_icon_path() -> str:
    """Ensure icon exists on disk and return its absolute path."""
    if not os.path.exists(ICON_PATH) or os.path.getsize(ICON_PATH) == 0:
        generate_arc_reactor_icon(ICON_PATH)
    return ICON_PATH

if __name__ == "__main__":
    path = generate_arc_reactor_icon()
    print(f"Arc Reactor Icon created at: {path}")

