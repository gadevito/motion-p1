#!/usr/bin/env python3
"""
Figure of E12-sexies for the paper: R×(h) and R_own(h) within 250 m, by city, with 95% intervals.
=================================================================================================
Reads only the frozen record `paper4/congelamenti/e12sexies_risultati.json` and writes a deterministic SVG
(no date, no random identifiers): `paper4/analysis/figures/e12sexies_persistence.svg`. No computation: every plotted
value and interval is a field of the record (R×: Rx_h, Rx_h_L, Rx_h_U; R_own: Rown_h, Rown_h_L, Rown_h_U; bin 0-250 m).
Cells without an interval in the record (Melbourne: fewer than 3 blocks in some seed) are drawn as hollow points
without bars; empty cells are not drawn; at h = 0 both ratios are 1 by definition.

Usage: python3 paper4/analysis/figure_e12sexies.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REC = ROOT / "paper4" / "congelamenti" / "e12sexies_risultati.json"
OUT = ROOT / "paper4" / "analysis" / "figures" / "e12sexies_persistence.svg"
BIN = "0-250 m"
LAGS = (0, 1, 2, 4, 8)                       # steps; minutes in the record's lags_minutes
CITIES = ("madrid", "london", "melbourne")
LEVELS = ("0.1", "0.2", "0.4", "0.6")
COLOURS = {"0.1": "#9ecae1", "0.2": "#4292c6", "0.4": "#2171b5", "0.6": "#08306b"}
W, H, PW, PH, X0, Y0 = 900, 290, 250, 190, 50, 30
YMIN, YMAX = -0.4, 1.0


def main():
    rec = json.loads(REC.read_text())
    mins = rec["lags_minutes"]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="11">',
         f'<rect width="{W}" height="{H}" fill="white"/>']

    def y(v):
        return round(Y0 + PH * (YMAX - v) / (YMAX - YMIN), 1)

    for c, city in enumerate(CITIES):
        x0 = X0 + c * (PW + 50)

        def x(i, off=0.0):
            return round(x0 + 10 + i * (PW - 20) / (len(LAGS) - 1) + off, 1)

        s.append(f'<text x="{x0 + PW / 2}" y="16" text-anchor="middle" font-weight="bold">{city.capitalize()}</text>')
        s.append(f'<line x1="{x0}" y1="{y(YMIN)}" x2="{x0}" y2="{y(YMAX)}" stroke="#888"/>')
        s.append(f'<line x1="{x0}" y1="{y(YMIN)}" x2="{x0 + PW}" y2="{y(YMIN)}" stroke="#888"/>')
        for v in (-0.4, 0.0, 0.5, 1.0):
            s.append(f'<text x="{x0 - 4}" y="{y(v) + 4}" text-anchor="end">{v:.1f}</text>')
        s.append(f'<line x1="{x0}" y1="{y(0)}" x2="{x0 + PW}" y2="{y(0)}" stroke="#ccc" stroke-dasharray="2,2"/>')
        s.append(f'<line x1="{x0}" y1="{y(0.5)}" x2="{x0 + PW}" y2="{y(0.5)}" stroke="#ccc" stroke-dasharray="2,2"/>')
        for i, m in enumerate(mins):
            s.append(f'<text x="{x(i)}" y="{y(YMIN) + 14}" text-anchor="middle">{m}</text>')
        s.append(f'<text x="{x0 + PW / 2}" y="{y(YMIN) + 28}" text-anchor="middle">lag h (min)</text>')
        for li, f in enumerate(LEVELS):
            e = rec["rows"][f"{city} {f}"][BIN]
            if "A_0" not in e:
                continue
            col = COLOURS[f]; off = (li - 1.5) * 4
            for key, dash in (("Rx", ""), ("Rown", ' stroke-dasharray="5,3"')):
                pts = [(x(i, off), y(e[f"{key}_{h}"])) for i, h in enumerate(LAGS) if e.get(f"{key}_{h}") is not None]
                s.append(f'<polyline fill="none" stroke="{col}" stroke-width="1.6"{dash} points="'
                         + " ".join(f"{a},{b}" for a, b in pts) + '"/>')
                for i, h in enumerate(LAGS):
                    v = e.get(f"{key}_{h}")
                    if v is None:
                        continue
                    lo, hi = e.get(f"{key}_{h}_L"), e.get(f"{key}_{h}_U")
                    if h == 0:                                   # 1 by definition
                        s.append(f'<circle cx="{x(i, off)}" cy="{y(v)}" r="2.2" fill="{col}"/>')
                    elif lo is not None and hi is not None:
                        s.append(f'<line x1="{x(i, off)}" y1="{y(max(lo, YMIN))}" x2="{x(i, off)}" y2="{y(min(hi, YMAX))}" '
                                 f'stroke="{col}" stroke-width="1"/>')
                        s.append(f'<circle cx="{x(i, off)}" cy="{y(v)}" r="2.2" fill="{col}"/>')
                    else:
                        s.append(f'<circle cx="{x(i, off)}" cy="{y(v)}" r="2.6" fill="white" stroke="{col}"/>')
    # legend
    lx = X0; ly = H - 14
    s.append(f'<line x1="{lx}" y1="{ly}" x2="{lx + 24}" y2="{ly}" stroke="#333" stroke-width="1.6"/>')
    s.append(f'<text x="{lx + 28}" y="{ly + 4}">R×(h): neighbour at t, hidden segment at t + h</text>')
    lx += 290
    s.append(f'<line x1="{lx}" y1="{ly}" x2="{lx + 24}" y2="{ly}" stroke="#333" stroke-width="1.6" stroke-dasharray="5,3"/>')
    s.append(f'<text x="{lx + 28}" y="{ly + 4}">R_own(h): hidden segment at t and t + h</text>')
    lx += 260
    for f in LEVELS:
        s.append(f'<rect x="{lx}" y="{ly - 5}" width="10" height="10" fill="{COLOURS[f]}"/>')
        s.append(f'<text x="{lx + 13}" y="{ly + 4}">{int(float(f) * 100)}%</text>'); lx += 50
    s.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(s) + "\n")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
