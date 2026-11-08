#!/usr/bin/env python3
r"""
Paper 4 — typeset the full draft (text and supplement) into one PDF, for the reading of the internal review.
=========================================================================================================
The Markdown files of `paper4/paper/` remain the text of record: their numbers are the ones checked by
`paper4/analysis/main.py` (step 3). This script converts them, unchanged, into `paper4/manuscript/main.tex`
(IEEEtran journal, the class and fonts of Paper 1) and compiles it with Tectonic (XeLaTeX engine).

  - order of the sections: SECTIONS below, as in `paper4/paper/paper_order.md`, with the lead of Part B;
  - the draft header of each file (everything above its first `---` line) is dropped;
  - the figure of E10-geo is the frozen SVG (`paper4/congelamenti/e10geo_curva.svg`), rasterised by headless
    Chrome into `paper4/manuscript/figures/e10geo_curva.png`;
  - citations: [key] becomes \cite{key} for the keys of `references.tex` (hand-written bibliography);
  - authors, affiliations and grant as in Paper 1; biographies after the references;
  - supplement, in one column after the biographies: S1, the register of corrections restricted to the items
    on which numbers of the paper depend (`protocol/paper4/REGISTRO_CORREZIONI.md`, items in SUPPLEMENT_ITEMS;
    the items on the traceability of the earlier report stay in the repository); S2, the frozen records and the
    provenance of the numbers (`paper4/paper/supplement_records.md`).

Usage, from the repository root:  python3 paper4/manuscript/build.py   (writes main.tex, main.pdf)
The LaTeX is generated: edit the Markdown, not main.tex. On Overleaf, main.tex compiles with XeLaTeX.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper4" / "paper"
OUT = ROOT / "paper4" / "manuscript"
SVG = ROOT / "paper4" / "congelamenti" / "e10geo_curva.svg"
REGISTER = ROOT / "protocol" / "paper4" / "REGISTRO_CORREZIONI.md"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# (file, level shift): level shift 0 maps "##" to \section, 1 maps "##" to \subsection (sections of Part B).
SECTIONS = [("section_introduction.md", 0), ("section_setting.md", 0), ("section_partB.md", 0),
            ("section_E11.md", 1), ("section_E9.md", 1), ("section_signal.md", 1), ("section_E10geo.md", 1),
            ("section_partA.md", 0), ("section_discussion.md", 0), ("section_limits.md", 0),
            ("section_conclusion.md", 0), ("section_availability.md", 0)]
UNNUMBERED = {"Data and Code Availability"}
SUPPLEMENT_ITEMS = {"1", "2", "3", "8", "9", "10", "11", "12", "13"}
BIBKEYS = set(re.findall(r"\\bibitem\{([^}]+)\}", (Path(__file__).resolve().parent / "references.tex").read_text()))
AUTHORS = ["Gabriele De Vito", "Gemma Catolino", "Dario Di Nucci", "Fabio Palomba", "Carmine Gravino",
           "Andrea De Lucia", "Filomena Ferrucci"]
LEVELS = ["section", "subsection", "subsubsection", "paragraph"]

# Characters outside the text font, set in math.
MATHCHARS = {"≥": r"$\geq$", "≤": r"$\leq$", "→": r"$\rightarrow$", "←": r"$\leftarrow$", "×": r"$\times$",
             "±": r"$\pm$", "≈": r"$\approx$", "ρ": r"$\rho$", "σ": r"$\sigma$", "Δ": r"$\Delta$", "≠": r"$\neq$",
             "∈": r"$\in$", "⁻": r"$^{-}$", "¹": r"$^{1}$", "⁰": r"$^{0}$", "√": r"$\surd$", "∞": r"$\infty$",
             "≪": r"$\ll$", "≫": r"$\gg$", "·": r"$\cdot$", "τ": r"$\tau$", "μ": r"$\mu$", "α": r"$\alpha$",
             "β": r"$\beta$", "λ": r"$\lambda$", "✓": r"$\checkmark$", "↔": r"$\leftrightarrow$"}
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
           "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}", "<": r"\textless{}", ">": r"\textgreater{}"}


def sha(p, n=16):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]


def esc(t):
    out = []
    for ch in t:
        out.append(SPECIAL.get(ch) or MATHCHARS.get(ch) or ch)
    return "".join(out)


def code(t):
    """Inline code: monospaced, breakable after / _ . | and -."""
    s = esc(t)
    for a in ["/", r"\_", ".", "|", "-"]:
        s = s.replace(a, a + r"\allowbreak{}")
    return r"\texttt{" + s + "}"


def inline(t):
    """Markdown inline markup to LaTeX: `code`, **bold**, *italic*; everything else escaped."""
    parts = re.split(r"(`[^`]+`)", t)
    out = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            out.append(code(p[1:-1])); continue
        s = esc(p)
        s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
        s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", s)
        s = re.sub(r'"(\S[^"]*?)"', r"``\1''", s)
        s = re.sub(r"\[([a-z]+\d{4}[a-z0-9]*)\]", lambda m: r"~\cite{" + m.group(1) + "}" if m.group(1) in BIBKEYS
                   else m.group(0), s)
        out.append(s)
    return "".join(out)


def body(md):
    """The text below the first `---` line (the draft header is dropped)."""
    lines = md.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip() == "---":
            return lines[i + 1:]
    return lines


def split_row(r):
    """Cells of a pipe-table row; a | inside backticks belongs to the cell."""
    cells, cur, tick = [], "", False
    for ch in r.strip().strip("|"):
        if ch == "`":
            tick = not tick
        if ch == "|" and not tick:
            cells.append(cur.strip()); cur = ""
        else:
            cur += ch
    return cells + [cur.strip()]


FLOATING = True          # False in the supplement (one column): tables are set in place


def table(rows, caption=None):
    cells = [split_row(r) for r in rows]
    head, data = cells[0], [r for r in cells[2:]]
    n = len(head)
    # width of a column: its longest data cell, or the longest word of its header (headers wrap)
    width = [max([len(r[j]) for r in data if j < len(r)] + [max(len(w) for w in head[j].split() or [""])])
             + 2 for j in range(n)]
    total = sum(width)
    wide = total > 70 or n > 4
    env = "table*" if wide else "table"
    tw = r"\textwidth" if wide else r"\columnwidth"
    # column widths proportional to content, bounded; the first column left-aligned, the others too
    w = [max(0.06, min(0.6, x / total)) for x in width]
    k = sum(w); w = [x / k for x in w]
    spec = "".join(r">{\raggedright\arraybackslash\hsize=" + f"{x * n:.3f}" + r"\hsize}X" for x in w)
    if not FLOATING:
        env, tw = "center", r"\textwidth"
    out = ([rf"\begin{{{env}}}[!t]"] if FLOATING else [r"\begin{center}"]) + \
          [r"\centering\footnotesize", r"\renewcommand{\arraystretch}{1.15}"]
    if caption and FLOATING:
        out.append(r"\caption{" + inline(caption) + "}")
    # in place (supplement): the section heading is the caption
    out += [rf"\begin{{tabularx}}{{{tw}}}{{{spec}}}", r"\toprule",
            " & ".join(r"\textbf{" + inline(h) + "}" for h in head) + r" \\", r"\midrule"]
    for r in data:
        r = (r + [""] * n)[:n]
        out.append(" & ".join(inline(c) for c in r) + r" \\")
    out += [r"\bottomrule", r"\end{tabularx}", rf"\end{{{env}}}"]
    return out


def lists(block):
    """A block of list lines ('- ', '1. ', with indented continuations and nested '  - ') to LaTeX."""
    out, stack = [], []          # stack of (indent, env)
    item = None

    def flush():
        nonlocal item
        if item is not None and item[0] == "\\par ":
            out.append(" ".join(x if x == "\\par " else inline(x) for x in item))
            item = None
        if item is not None:
            while item and item[-1] == "\\par ":
                item.pop()
            out.append(r"\item " + " ".join(x if x == "\\par " else inline(x) for x in item))
            item = None

    for ln in block:
        m = re.match(r"^(\s*)(- |\d+\. )(.*)$", ln)
        if m:
            flush()
            ind, mark, text = len(m.group(1)), m.group(2), m.group(3)
            env = "enumerate" if mark[0].isdigit() else "itemize"
            while stack and stack[-1][0] > ind:
                out.append(rf"\end{{{stack.pop()[1]}}}")
            if not stack or stack[-1][0] < ind:
                out.append(rf"\begin{{{env}}}")
                stack.append((ind, env))
            item = [text]
        elif not ln.strip():
            if item is not None:
                item.append("\\par ")
        elif len(stack) > 1 and len(ln) - len(ln.lstrip()) <= stack[-1][0]:
            # continuation of the parent item after a nested list: close the nested list, new paragraph
            flush()
            out.append(rf"\end{{{stack.pop()[1]}}}")
            item = ["\\par ", ln.strip()]
        else:
            if item is None:
                item = []
            item.append(ln.strip())
    flush()
    while stack:
        out.append(rf"\end{{{stack.pop()[1]}}}")
    return out


def convert(lines, shift):
    out, i, pending_caption, heading = [], 0, None, ""
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1; continue
        m = re.match(r"^(#{2,5}) (.*)$", ln)
        if m:
            lvl = len(m.group(1)) - 2 + shift
            star = "*" if m.group(2).strip() in UNNUMBERED else ""
            out.append(rf"\{LEVELS[min(lvl, 3)]}{star}{{{inline(m.group(2))}}}")
            heading = m.group(2); i += 1; continue
        block = []
        LIST = r"^\s*(- |\d+\. )"
        is_list = bool(re.match(LIST, ln))
        while i < len(lines) and not re.match(r"^#{2,5} ", lines[i]):
            cur = lines[i]
            if not cur.strip():
                # a list goes on across a blank line when the next line is an item or an indented continuation
                nxt = next((x for x in lines[i + 1:] if x.strip()), "")
                if is_list and (re.match(LIST, nxt) or nxt.startswith("  ")):
                    block.append(""); i += 1; continue
                break
            if block and not is_list and not block[0].startswith(("|", ">")) and re.match(LIST, cur):
                break                                   # a list right after a paragraph line starts a new block
            block.append(cur); i += 1
            if block[0].startswith("|") and not (i < len(lines) and lines[i].startswith("|")):
                break
        if block[0].startswith("|"):
            cap = pending_caption or heading; pending_caption = None
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            note = []
            if j < len(lines) and lines[j].startswith("*") and not lines[j].startswith("**"):
                while j < len(lines) and lines[j].strip():
                    note.append(lines[j].strip()); j += 1
                note = " ".join(note)
                if note.endswith("*") and not note.endswith("**"):
                    cap = cap + ". " + note[1:-1]; i = j
            out += table(block, cap)
        elif block[0].startswith(">"):
            out += [r"\begin{quote}", inline(" ".join(b.lstrip("> ").strip() for b in block)), r"\end{quote}"]
        elif re.match(r"^\s*(- |\d+\. )", block[0]):
            out += lists(block)
        elif block[0].startswith("**Figure"):
            text = " ".join(b.strip() for b in block)
            text = re.sub(r"\s*\(`paper4/congelamenti/e10geo_curva\.svg`\)\s*$", "", text)
            cap = re.sub(r"^\*\*Figure — (.+?)\*\*", r"\1", text)
            out += [r"\begin{figure*}[!t]", r"\centering",
                    r"\includegraphics[width=\textwidth]{figures/e10geo_curva.png}",
                    r"\caption{" + inline(cap) + " Frozen figure \\texttt{e10geo\\_curva.svg} (" + sha(SVG) + ").}",
                    r"\label{fig:e10geo}", r"\end{figure*}"]
        else:
            out.append(inline(" ".join(b.strip() for b in block)))
        out.append("")
    return out


def front():
    md = body((PAPER / "section_abstract.md").read_text())
    sec, cur = {}, None
    for ln in md:
        if ln.startswith("## "):
            cur = ln[3:].strip(); sec[cur] = []
        elif cur:
            sec[cur].append(ln)
    j = lambda k: " ".join(x.strip() for x in sec[k] if x.strip())
    return j("Title"), j("Abstract"), j("Keywords")


def supplement():
    md = REGISTER.read_text().splitlines()
    rows = [ln for ln in md if ln.startswith("|")]
    intro = []
    for ln in md[1:]:
        if ln.startswith("|"):
            break
        intro.append(ln)
    out = [r"\clearpage", r"\onecolumn",
           r"\begin{center}\Large Supplementary material\end{center}",
           r"\section*{S1. Register of corrections}",
           inline("Corrections made during the study on which numbers of the paper depend: defects of the earlier "
                  "pipeline corrected in this one (items 1–3) and defects of the pipeline of this study found and "
                  "corrected before any accepted number (items 8–13). Items 4–7 and 14–20 concern the traceability "
                  "of the earlier report [motion2026uc04]: no number of this paper depends on them, and they are "
                  "listed in the register in the repository. Source: `protocol/paper4/REGISTRO_CORREZIONI.md` (" +
                  sha(REGISTER) + ")."), ""]
    cells = [split_row(r) for r in rows]
    head, data = cells[0], [r for r in cells[2:] if r[0] in SUPPLEMENT_ITEMS]
    spec = (r">{\raggedright\arraybackslash}p{0.03\textwidth}>{\raggedright\arraybackslash}p{0.27\textwidth}"
            r">{\raggedright\arraybackslash}p{0.38\textwidth}>{\raggedright\arraybackslash}p{0.11\textwidth}"
            r">{\raggedright\arraybackslash}p{0.13\textwidth}")
    out += [r"{\scriptsize", r"\begin{longtable}{" + spec + "}", r"\toprule",
            " & ".join(r"\textbf{" + inline(h) + "}" for h in head) + r" \\", r"\midrule", r"\endhead"]
    for r in data:
        r = (r + [""] * 5)[:5]
        out.append(" & ".join(inline(c) for c in r) + r" \\ \addlinespace")
    out += [r"\bottomrule", r"\end{longtable}", "}"]
    global FLOATING
    FLOATING = False
    rec = body((PAPER / "supplement_records.md").read_text())
    rec = [ln.replace("## Frozen records and provenance", "## S2. Frozen records and provenance") for ln in rec]
    UNNUMBERED.add("S2. Frozen records and provenance")
    out += convert(rec, 0)
    return out


PREAMBLE = r"""\documentclass[lettersize,journal]{IEEEtran}
\usepackage{amsmath,amssymb}
\usepackage{fontspec}
\setmainfont{texgyretermes}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
\usepackage[warnings-off={mathtools-colon,mathtools-overbracket}]{unicode-math}
\setmathfont{texgyretermes-math.otf}
\usepackage{array,booktabs,tabularx,longtable}
\usepackage{graphicx}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{fancyhdr}
\renewcommand{\tabularxcolumn}[1]{p{#1}}
\setlength{\tabcolsep}{3pt}
\emergencystretch=2em
% Generated by paper4/manuscript/build.py from paper4/paper/*.md: edit the Markdown, not this file.
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True); (OUT / "figures").mkdir(exist_ok=True)
    png = OUT / "figures" / "e10geo_curva.png"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=3",
                    "--window-size=800,250", f"--screenshot={png}", SVG.as_uri()], check=True,
                   capture_output=True)
    title, abstract, keywords = front()
    tex = [PREAMBLE, r"\begin{document}", r"\title{" + inline(title) + "}",
           r"\author{" + ", ".join(AUTHORS[:-1]) + ", and " + AUTHORS[-1] + "%\n"
           r"\thanks{Manuscript received Month DD, 2026. This work was supported by the MOTION project, funded by the "
           r"Fondo per la Crescita Sostenibile -- Accordi per l'innovazione (D.M. 31 December 2021, D.M. 11 May 2023 "
           r"and D.D. 11 August 2023), project F/350228/01-05/X60, CUP B99J23006570007.}%" + "\n"
           r"\thanks{The authors are with the Department of Computer Science, University of Salerno, Fisciano (SA), "
           r"Italy (e-mail: \{gadevito, gcatolino, ddinucci, fpalomba, gravino, adelucia, fferrucci\}@unisa.it). "
           r"Corresponding author: Gabriele De Vito.}%" + "\n"
           r"\thanks{Draft of 2026-11-08 for the internal review, typeset from \texttt{paper4/paper/*.md}; every "
           r"number is checked against the frozen records. [ref:~\ldots] marks a reference still to be chosen.}}",
           r"\markboth{IEEE Transactions on Intelligent Transportation Systems}"
           r"{De Vito \MakeLowercase{\textit{et al.}}: What a Traffic Sensor Buys}",
           r"\maketitle", r"\begin{abstract}", r"\input{sections/abstract}", r"\end{abstract}",
           r"\begin{IEEEkeywords}", inline(keywords), r"\end{IEEEkeywords}", ""]
    # one LaTeX file per section, as in Paper 1 (sections/<name>.tex), all generated from the Markdown
    sec = OUT / "sections"; sec.mkdir(exist_ok=True)
    for old in sec.glob("*.tex"):
        old.unlink()
    head = "% Generated by paper4/manuscript/build.py from paper4/paper/{} ({}): edit the Markdown, not this file.\n"
    (sec / "abstract.tex").write_text(head.format("section_abstract.md", sha(PAPER / "section_abstract.md"))
                                      + inline(abstract) + "\n")
    for fn, shift in SECTIONS:
        name = fn.removeprefix("section_").removesuffix(".md")
        (sec / f"{name}.tex").write_text(head.format(fn, sha(PAPER / fn))
                                         + "\n".join(convert(body((PAPER / fn).read_text()), shift)) + "\n")
        tex.append(r"\input{sections/" + name + "}")
    # bibliography in order of first citation (IEEE), from the hand-written references.tex
    order = []
    for t in [(sec / "abstract.tex").read_text()] + [(sec / (fn.removeprefix("section_").removesuffix(".md") + ".tex"))
                                                     .read_text() for fn, _ in SECTIONS]:
        for k in re.findall(r"\\cite\{([^}]+)\}", t):
            if k not in order:
                order.append(k)
    entries = re.split(r"\n(?=\\bibitem\{)", (OUT / "references.tex").read_text())
    byk = {re.match(r"\\bibitem\{([^}]+)\}", e).group(1): e.strip() for e in entries if e.startswith("\\bibitem")}
    (OUT / "bibliography.tex").write_text("% Generated by build.py: the entries of references.tex cited in the text, in "
                                         "order of first citation.\n" + "\n\n".join(byk[k] for k in order) + "\n")
    unused = sorted(set(byk) - set(order))
    if unused:
        print("references not cited:", ", ".join(unused))
    tex += ["", r"\begin{thebibliography}{99}", r"\footnotesize", r"\input{bibliography}", r"\end{thebibliography}", ""]
    (sec / "biographies.tex").write_text("\n".join(
        r"\begin{IEEEbiographynophoto}{" + a + "}\nBiography to be supplied.\n\\end{IEEEbiographynophoto}"
        for a in AUTHORS) + "\n")
    tex.append(r"\input{sections/biographies}")
    (sec / "supplement.tex").write_text(head.format("supplement_records.md and the register", "-")
                                        + "\n".join(supplement()) + "\n")
    tex += [r"\input{sections/supplement}", r"\end{document}"]
    (OUT / "main.tex").write_text("\n".join(tex) + "\n")
    r = subprocess.run(["tectonic", "-X", "compile", "--keep-logs", "main.tex"], cwd=OUT, capture_output=True,
                       text=True)
    log = r.stdout + r.stderr
    missing = sorted(set(re.findall(r"Missing character: There is no (\S+)", log)))
    print(log[-1500:] if r.returncode else "compiled: paper4/manuscript/main.pdf")
    if missing:
        print("missing glyphs:", " ".join(missing))
    if r.returncode == 0:
        overleaf()
    return r.returncode


def overleaf():
    """paper4/manuscript/paper4_overleaf.zip: what Overleaf needs to compile main.tex (compiler: XeLaTeX)."""
    import zipfile
    (OUT / "latexmkrc").write_text("# Overleaf and latexmk: the manuscript uses fontspec and unicode-math, "
                                   "so it compiles with XeLaTeX\n$pdf_mode = 5;\n")
    files = ["main.tex", "references.tex", "bibliography.tex", "latexmkrc", "IEEEtran.cls"] + \
            [f"sections/{f.name}" for f in sorted((OUT / "sections").glob("*.tex"))] + \
            [f"figures/{f.name}" for f in sorted((OUT / "figures").glob("*.png"))]
    z = OUT / "paper4_overleaf.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(OUT / f, f)
    print(f"overleaf package: {z.relative_to(ROOT)} ({len(files)} files)")


if __name__ == "__main__":
    sys.exit(main())
