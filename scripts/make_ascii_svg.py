"""Convert source-prepped.png -> avi-ascii.svg (monochrome ASCII that prints row by row)."""
import os, sys
from xml.sax.saxutils import escape
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)
COLS = 100
CHAR_ASPECT = 0.5       # glyphs are ~2x taller than wide
FONT = 7.0
CW = FONT * 0.6         # monospace advance
LH = FONT * 1.15
COLOR = "#c9d1d9"
STATIC = os.environ.get("STATIC") == "1"


def main(src, out):
    im = Image.open(src).convert("L")
    w, h = im.size
    rows = max(1, round(COLS * (h / w) * CHAR_ASPECT))
    im = im.resize((COLS, rows), Image.LANCZOS)
    px = im.load()
    lines = []
    for y in range(rows):
        s = ""
        for x in range(COLS):
            b = px[x, y] / 255.0
            s += RAMP[min(len(RAMP) - 1, int((1 - b) * len(RAMP)))]
        lines.append(s.rstrip())

    width = COLS * CW
    height = rows * LH + 8
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" width="{width:.0f}" height="{height:.0f}" role="img" aria-label="ASCII portrait">']
    o.append(f'<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:{FONT}px;fill:{COLOR};white-space:pre}}</style>')
    o.append(f'<rect width="{width:.1f}" height="{height:.1f}" fill="#0d1117"/>')
    dur = 0.55
    for i, line in enumerate(lines):
        y = 4 + (i + 1) * LH - 2
        begin = i * 0.07
        if STATIC:
            o.append(f'<text x="0" y="{y:.1f}" xml:space="preserve">{escape(line)}</text>')
            continue
        cid = f"c{i}"
        o.append(f'<clipPath id="{cid}"><rect x="0" y="{y-LH:.1f}" width="0" height="{LH+2:.1f}">'
                 f'<animate attributeName="width" from="0" to="{width:.1f}" begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/></rect></clipPath>')
        o.append(f'<text x="0" y="{y:.1f}" xml:space="preserve" clip-path="url(#{cid})">{escape(line)}</text>')
        # block cursor riding the wipe edge
        o.append(f'<rect x="0" y="{y-LH+2:.1f}" width="{CW:.1f}" height="{LH-2:.1f}" fill="{COLOR}" opacity="0">'
                 f'<animate attributeName="x" from="0" to="{width:.1f}" begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/>'
                 f'<animate attributeName="opacity" values="0;0.9;0.9;0" keyTimes="0;0.02;0.98;1" begin="{begin:.2f}s" dur="{dur}s" fill="freeze"/></rect>')
    o.append("</svg>")
    with open(out, "w") as f:
        f.write("\n".join(o))
    print(f"wrote {out} ({COLS}x{rows})")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source-prepped.png")
    main(src, os.path.join(ROOT, "avi-ascii.svg"))
