"""Neofetch-style info card -> info-card.svg (content from profile.config.json)."""
import json, os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.environ.get("STATIC") == "1"
W = 490
LINE_H = 24
KEY_COLORS = ["#ff7b72", "#ffa657", "#d2a8ff", "#79c0ff", "#7ee787", "#f2cc60"]


def main():
    with open(os.path.join(ROOT, "profile.config.json")) as f:
        cfg = json.load(f)
    rows = cfg["rows"]
    title = cfg.get("title", "dev@github")
    top = 62
    H = top + len(rows) * LINE_H + 52

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Profile info card">']
    o.append("<style>")
    o.append("text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;fill:#c9d1d9}")
    o.append(".k{font-weight:700}.dim{fill:#8b949e}")
    if not STATIC:
        o.append("@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:translateX(0)}}")
        o.append(".l{opacity:0;animation:in .45s ease-out forwards}")
    o.append("</style>")
    o.append(f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117"/>')
    o.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="none" stroke="#30363d"/>')
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        o.append(f'<circle cx="{20 + i*18}" cy="20" r="5.5" fill="{c}"/>')
    o.append(f'<text class="dim" x="{W//2}" y="24" text-anchor="middle" font-size="12">neofetch</text>')
    o.append(f'<text x="20" y="{top-10}"><tspan fill="#7ee787">{escape(title)}</tspan></text>')
    o.append(f'<text class="dim" x="20" y="{top+4}">{"-" * (len(title))}</text>')

    for i, (k, v) in enumerate(rows):
        y = top + 24 + i * LINE_H
        delay = 0.25 + i * 0.22
        cls = "" if STATIC else f' class="l" style="animation-delay:{delay:.2f}s"'
        col = KEY_COLORS[i % len(KEY_COLORS)]
        o.append(f'<text x="20" y="{y}"{cls}><tspan class="k" fill="{col}">{escape(k)}</tspan><tspan class="dim">: </tspan><tspan>{escape(v)}</tspan></text>')

    by = H - 22
    for i, c in enumerate(("#ff7b72", "#ffa657", "#f2cc60", "#7ee787", "#79c0ff", "#d2a8ff", "#c9d1d9")):
        o.append(f'<rect x="{20 + i*22}" y="{by}" width="18" height="10" rx="2" fill="{c}"/>')
    o.append("</svg>")
    with open(os.path.join(ROOT, "info-card.svg"), "w") as f:
        f.write("\n".join(o))
    print("wrote info-card.svg")


if __name__ == "__main__":
    main()
