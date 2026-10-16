"""Prep a portrait for ASCII conversion: remove bg, boost local contrast, composite on white.
Usage: python scripts/prep_photo.py source-photo.jpg  ->  source-prepped.png
"""
import sys, os
import numpy as np
import cv2
from PIL import Image
from rembg import remove

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(path):
    img = Image.open(path).convert("RGBA")
    cut = remove(img)  # RGBA with transparent background
    rgba = np.array(cut)
    alpha = rgba[:, :, 3] / 255.0
    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)
    out = gray * alpha + 255.0 * (1 - alpha)  # background -> pure white
    Image.fromarray(out.astype(np.uint8), "L").save(os.path.join(ROOT, "source-prepped.png"))
    print("wrote source-prepped.png")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: prep_photo.py <photo>")
    main(sys.argv[1])
