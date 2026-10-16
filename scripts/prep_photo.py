"""Prep a portrait for ASCII conversion: isolate subject, boost local contrast, composite on white.

Usage:
    python scripts/prep_photo.py source-photo.jpg [--crop x0,y0,x1,y1]
Writes source-prepped.png (grayscale).

Background removal uses rembg when it is installed and its model can be loaded;
otherwise it falls back to OpenCV GrabCut so the script works offline.
"""
import argparse, os
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def subject_alpha(rgb):
    """Return a float alpha mask (1 = subject) for an RGB uint8 image."""
    try:
        from rembg import remove
        cut = np.array(remove(Image.fromarray(rgb)))
        return cut[:, :, 3] / 255.0
    except Exception as e:  # rembg missing, or model download blocked
        print(f"rembg unavailable ({type(e).__name__}); using GrabCut fallback")
    h, w = rgb.shape[:2]
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    mask = np.zeros((h, w), np.uint8)
    rect = (int(w * 0.04), int(h * 0.03), int(w * 0.92), int(h * 0.95))
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(bgr, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    # Drop saturated-blue pixels (coloured logos/signs behind the subject).
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    blue = ((hsv[:, :, 0] > 95) & (hsv[:, :, 0] < 130) & (hsv[:, :, 1] > 150) & (hsv[:, :, 2] > 110)).astype(np.uint8) * 255
    blue = cv2.dilate(blue, np.ones((11, 11), np.uint8))
    m[blue > 0] = 0
    # Keep only the largest connected region (the person).
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        m = np.where(lab == keep, 255, 0).astype(np.uint8)
    m = cv2.GaussianBlur(m, (0, 0), 2)
    return m / 255.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--crop", help="x0,y0,x1,y1 in source pixels")
    args = ap.parse_args()

    img = Image.open(args.photo).convert("RGB")
    if args.crop:
        img = img.crop(tuple(int(v) for v in args.crop.split(",")))
    rgb = np.array(img)
    alpha = subject_alpha(rgb)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray).astype(np.float32)
    out = gray * alpha + 255.0 * (1 - alpha)  # background -> pure white (blank end of ramp)
    Image.fromarray(out.astype(np.uint8), "L").save(os.path.join(ROOT, "source-prepped.png"))
    print("wrote source-prepped.png")


if __name__ == "__main__":
    main()
