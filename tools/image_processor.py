#!/usr/bin/env python3
"""
Image Processor for Story Core Visual Novel
Handles image scaling, aspect ratio correction, and normalization for BetterHud portraits.
Target display resolution in BetterHud layout: 64 wide x 72 high.
Supports input resolutions: 64x64, 128x128, 256x256, 512x512, or arbitrary aspect ratios.
"""

import os
from PIL import Image

TARGET_WIDTH = 64
TARGET_HEIGHT = 72

def process_portrait(input_path: str, output_path: str) -> dict:
    """
    Takes any input image (PNG) and normalizes it to exactly 64x72 pixels.
    - Preserves alpha transparency.
    - If the aspect ratio does not match 64:72 (8:9), it fits inside while centering and padding with transparent pixels.
    - Uses nearest neighbor / lanczos depending on whether input is pixel art or hi-res, keeping lines sharp.
    Returns metadata dict with original and processed sizes.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input image not found: {input_path}")

    with Image.open(input_path) as im:
        im = im.convert("RGBA")
        orig_w, orig_h = im.size

        target_ratio = TARGET_WIDTH / TARGET_HEIGHT
        current_ratio = orig_w / orig_h

        # Calculate bounding box to fit inside 64x72 while preserving proportions
        if current_ratio > target_ratio:
            # Image is wider than 8:9 -> fit to width
            new_w = TARGET_WIDTH
            new_h = int(round(TARGET_WIDTH / current_ratio))
        else:
            # Image is taller or equal -> fit to height
            new_h = TARGET_HEIGHT
            new_w = int(round(TARGET_HEIGHT * current_ratio))

        # Choose resampling filter:
        # If downsizing by integer multiple or small pixel art, NEAREST preserves crisp pixel art
        if orig_w % TARGET_WIDTH == 0 and orig_h % TARGET_HEIGHT == 0:
            resample_mode = Image.Resampling.NEAREST
        elif orig_w <= TARGET_WIDTH * 2:
            resample_mode = Image.Resampling.NEAREST
        else:
            resample_mode = Image.Resampling.LANCZOS

        resized = im.resize((new_w, new_h), resample=resample_mode)

        # Create transparent canvas 64x72
        canvas = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))

        # Bottom-center align: portraits look best anchored to bottom of frame
        paste_x = (TARGET_WIDTH - new_w) // 2
        paste_y = TARGET_HEIGHT - new_h

        canvas.paste(resized, (paste_x, paste_y), mask=resized)

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        canvas.save(output_path, "PNG", optimize=True)

        return {
            "original_size": (orig_w, orig_h),
            "processed_size": (TARGET_WIDTH, TARGET_HEIGHT),
            "paste_pos": (paste_x, paste_y),
            "resample_mode": "NEAREST" if resample_mode == Image.Resampling.NEAREST else "LANCZOS"
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        info = process_portrait(sys.argv[1], sys.argv[2])
        print(f"Processed: {info}")
    else:
        print("Usage: python image_processor.py <input_png> <output_png>")
