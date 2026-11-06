"""
JARVIS Arc Reactor Icon Generator (Phase 9 & 10)
Provides ultra-high resolution, multi-tier Windows .ico and PNG icons
featuring the authentic Mark 85 / Bleeding Edge Arc Reactor Core emblem.
"""

import os
from PIL import Image

ICON_PATH = os.path.join(os.path.dirname(__file__), "jarvis.ico")
MASTER_LOGO_PNG = os.path.join(os.path.dirname(__file__), "jarvis_logo.png")

def get_icon_path() -> str:
    """Ensure icon exists on disk and return its absolute path."""
    if not os.path.exists(ICON_PATH) or os.path.getsize(ICON_PATH) == 0:
        generate_arc_reactor_icon(ICON_PATH)
    return ICON_PATH

def generate_arc_reactor_icon(target_path: str = ICON_PATH) -> str:
    """
    Generate or export the high-definition multi-resolution Windows .ico file.
    Embedded mipmap sizes: 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256.
    """
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    if os.path.exists(MASTER_LOGO_PNG):
        base_img = Image.open(MASTER_LOGO_PNG).convert("RGBA")
    else:
        # Fallback: if master png is not found, load from padded scratch or create
        from PIL import ImageDraw
        base_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        d = ImageDraw.Draw(base_img)
        d.ellipse([8, 8, 248, 248], fill=(3, 7, 18, 255), outline=(0, 240, 255, 255), width=8)

    ico_images = [base_img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    ico_images[-1].save(
        target_path,
        format="ICO",
        sizes=[(s[0], s[1]) for s in sizes]
    )
    return target_path

if __name__ == "__main__":
    path = generate_arc_reactor_icon()
    print(f"Arc Reactor Icon verified at: {path}")
