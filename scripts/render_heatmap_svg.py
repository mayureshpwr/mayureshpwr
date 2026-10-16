"""Render data/contributions.json -> contrib-heatmap.svg (53x7 rounded boxes, diagonal reveal)."""
import json, os, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BOX, GAP = 13, 3
STEP = BOX + GAP
LEFT, TOP = 34, 34
STATIC = os.environ.get("STATIC") == "1"


def level_for(count, raw_level):
    # GitHub gives levels 0-4; promote the very top days to a neon level 5.
    return 5 if raw_level >= 4 and count >= 10 else raw_level


def main():
    with open(os.path.join(ROOT, "data", "contributions.json")) as f:
        data = json.load(f)
    days = data["days"]
    st = data["stats"]
    first = dt.date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # Sunday = row 0

    cells = []
    month_marks = {}
    for i, d in enumerate(days):
        idx = i + offset
        col, row = divmod(idx, 7)
        date = dt.date.fromisoformat(d["date"])
        if date.day <= 7 and row == 0 or (i == 0):
            month_marks.setdefault(col, date.strftime("%b"))
        cells.append((col, row, d, date))
    ncols = max(c[0] for c in cells) + 1

    width = LEFT + ncols * STEP + 14
    height = TOP + 7 * STEP + 56
    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="Contribution heatmap">')
    o.append("<style>")
    o.append("text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#8b949e;font-size:10px}")
    o.append(".t{fill:#c9d1d9;font-size:11px}")
    if not STATIC:
        o.append("@keyframes drop{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}")
        o.append(".c{opacity:0;animation:drop .35s ease-out forwards}")
    o.append("</style>")
    o.append(f'<rect width="{width}" height="{height}" rx="10" fill="#0d1117"/>')
    o.append(f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="10" fill="none" stroke="#30363d"/>')

    for col, name in month_marks.items():
        o.append(f'<text x="{LEFT + col*STEP}" y="{TOP-10}">{name}</text>')
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(f'<text x="8" y="{TOP + r*STEP + 10}">{name}</text>')

    for col, row, d, date in cells:
        lvl = level_for(d["count"], d["level"])
        x, y = LEFT + col * STEP, TOP + row * STEP
        delay = (col + row) * 0.018
        cls = "" if STATIC else f' class="c" style="animation-delay:{delay:.3f}s"'
        title = f'{d["count"]} contributions on {date.isoformat()}'
        o.append(f'<rect x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="3" fill="{PALETTE[lvl]}"{cls}><title>{title}</title></rect>')

    # legend
    ly = TOP + 7 * STEP + 14
    lx = width - 14 - (6 * STEP) - 70
    o.append(f'<text x="{lx}" y="{ly+10}">Less</text>')
    for i, c in enumerate(PALETTE):
        o.append(f'<rect x="{lx + 32 + i*STEP}" y="{ly}" width="{BOX}" height="{BOX}" rx="3" fill="{c}"/>')
    o.append(f'<text x="{lx + 32 + 6*STEP + 4}" y="{ly+10}">More</text>')

    # footer stats
    fy = height - 14
    o.append(f'<text class="t" x="{LEFT}" y="{ly+10}">{st["total"]:,} contributions in the last year</text>')
    o.append(f'<text x="{LEFT}" y="{fy}">streak {st["current_streak"]}d · longest {st["longest_streak"]}d · best day {st["best_day"]["count"]} ({st["best_day"]["date"]})</text>')
    o.append("</svg>")

    with open(os.path.join(ROOT, "contrib-heatmap.svg"), "w") as f:
        f.write("\n".join(o))
    print("wrote contrib-heatmap.svg", width, "x", height)


if __name__ == "__main__":
    main()
