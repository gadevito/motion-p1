#!/usr/bin/env python3
"""Phase 1 of P0 — inventory of the sources (P0 §3, §8 phase 1).

Reads the two branches at the commits declared in the signature of P0, through
`git show <commit>:<path>` only (the working tree is never read), and writes:

  protocol/processo/corpus/inventory.json   every source with path, branch, commit,
                                            sha256, class, and the number of candidate
                                            items it yields where the rule is mechanical
  protocol/processo/corpus/INVENTORY.md     the same, as tables, with the sha256 of the json

Candidate items are counted only where P0 gives a mechanical rule:
  registers      rows `| <n> |` of the two registers of corrections
  deviations     numbered or bulleted items under a heading containing
                 Deviation/Deviazion in a protocol file
  git search     commits of the branch whose message contains one of the P0 keywords
  tag diffs      files changed between consecutive tags, restricted to the P0 paths
Frozen records and regeneration reports are listed with fingerprints; their flags
are extracted in phase 2, not counted here.

Changes
  2026-11-10, after the first run (executor's report on commit 73cc5c6):
    - deviations: besides items under a Deviation(s) heading, paragraphs that start with
      "Deviazione"/"Deviation" or contain "deviazione dal"/"deviazioni dal"/"deviation from"
      are counted (the Paper 1 protocols declare deviations in the body, not under a heading);
      the rule of each file says which pattern matched;
    - class "protocol" restricted to the experiment protocols (`E<n>…md`, `P4A.md`);
      `PROTOCOLLO.md` listed as "method standard" (no count); `RISCRITTURA_STORIA.md` listed as
      "history aid"; summaries, phase reports and analysis notes under protocol/ excluded;
    - incident cards: only `I<n>.md`, not the README.

Usage (from the OR3 working copy; both commits share the object store):
  python3 protocol/processo/analisi/inventory.py --main aa9f478b3fa8 --paper4 ef31396c28cf \
      --out protocol/processo/corpus
"""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

KEYWORDS = ["voce", "item", "correzion", "correct", "difetto", "defect", "fix",
            "rettific", "ritir", "retract", "deviaz", "deviation"]
DIFF_PATHS = ["protocol/", "paper4/", "analysis/", "evoluzione/", "CONGELAMENTO_"]
DEV_HEADING = re.compile(r"^#{1,6}\s.*(deviation|deviazion)", re.I)
REG_ROW = re.compile(r"^\|\s*\d+[a-z]?\s*\|")
ITEM = re.compile(r"^\s*(\d+[\.\)]|[-*])\s+\S")


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def show(commit, path):
    return subprocess.run(["git", "show", f"{commit}:{path}"], check=True,
                          capture_output=True).stdout


def sha(b):
    return hashlib.sha256(b).hexdigest()


def tree(commit):
    out = git("ls-tree", "-r", "--name-only", commit)
    return [l for l in out.splitlines() if l]


def count_register_rows(text):
    return sum(1 for l in text.splitlines() if REG_ROW.match(l))


DEV_TEXT = re.compile(r"^\s*(?:[-*]\s+|\d+[.)]\s+)?(?:\*\*|\*|_)?\s*deviazion|^\s*(?:[-*]\s+|\d+[.)]\s+)?(?:\*\*|\*|_)?\s*deviation", re.I)
DEV_INLINE = re.compile(r"deviazion[ei] dal|deviation from", re.I)


def count_deviation_items(text):
    """Returns (count under headings, count by text pattern outside those sections)."""
    n_head, n_text, inside, level = 0, 0, False, 0
    for l in text.splitlines():
        m = re.match(r"^(#{1,6})\s", l)
        if m:
            if inside and len(m.group(1)) <= level:
                inside = False
            if DEV_HEADING.match(l):
                inside, level = True, len(m.group(1))
            continue
        if re.match(r"^\s*(-|\*)\s*(None|Nessuna)\.?\s*$", l):
            continue
        if inside:
            if ITEM.match(l):
                n_head += 1
        elif DEV_TEXT.match(l) or DEV_INLINE.search(l):
            n_text += 1
    return n_head, n_text


def cited_json(text):
    return sorted(set(re.findall(r"`?([\w./-]+\.json)`?", text)))


def classify(path, branch):
    p = path
    if p in ("protocol/REGISTRO_CORREZIONI.md", "protocol/paper4/REGISTRO_CORREZIONI.md"):
        return "register"
    if re.fullmatch(r"protocol/processo/incidenti/I\d+\.md", p):
        return "incident card"
    if p == "protocol/RISCRITTURA_STORIA.md":
        return "history aid"
    if p in ("protocol/PROTOCOLLO.md", "protocol/paper4/PROTOCOLLO.md"):
        return "method standard"
    if p.startswith(("protocol/revisioni/", "protocol/paper4/revisioni/")):
        return "internal review observation"
    if re.fullmatch(r"protocol/(paper4/)?(E\d+[A-Za-z]*|P4A)\.md", p):
        return "protocol"
    if (p.startswith("CONGELAMENTO_") or p.startswith("paper4/congelamenti/")) and p.endswith(".md"):
        return "frozen record"
    if (p.startswith(("analysis/rigenerazione/", "paper4/analysis/reports/", "protocol/spark/CONFRONTO_"))
            or p in ("analysis/CONFRONTO.md", "paper4/analysis/CONFRONTO.md")):
        return "regeneration report"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", required=True, help="commit of branch main declared in P0")
    ap.add_argument("--paper4", required=True, help="commit of branch paper4 declared in P0")
    ap.add_argument("--out", default="protocol/processo/corpus")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    entries, searches = [], []
    for branch, commit in (("main", a.main), ("paper4", a.paper4)):
        full = git("rev-parse", commit).strip()
        files = tree(full)
        listed = set()
        for path in files:
            cls = classify(path, branch)
            if not cls:
                continue
            # paper4 branch: only Paper 4 sources; main: everything but paper4/ and protocol/paper4/
            if branch == "main" and (path.startswith("paper4/") or path.startswith("protocol/paper4/")):
                continue
            if branch == "paper4" and not (path.startswith("paper4/") or path.startswith("protocol/paper4/")):
                continue
            b = show(full, path)
            e = {"branch": branch, "commit": full[:12], "path": path, "sha256": sha(b),
                 "class": cls, "candidate_items": None, "rule": None}
            text = b.decode("utf-8", "replace")
            if cls == "register":
                e["candidate_items"] = count_register_rows(text); e["rule"] = "rows `| n |`"
            elif cls == "protocol":
                nh, nt = count_deviation_items(text)
                e["candidate_items"] = nh + nt
                e["rule"] = f"heading items {nh}; text pattern {nt}"
            elif cls in ("method standard", "history aid"):
                e["rule"] = "listed; not a source of candidate items"
            elif cls == "frozen record":
                e["rule"] = "listed; flags extracted in phase 2"
                js = [j for j in cited_json(text) if j in files]
                e["cited_json"] = [{"path": j, "sha256": sha(show(full, j))} for j in js]
            elif cls == "regeneration report":
                e["rule"] = "listed; flags extracted in phase 2"
            entries.append(e); listed.add(path)

        # git search (a): keywords in commit messages of the branch
        log = git("log", "--format=%H%x1f%cI%x1f%s%x1f%b%x1e", full)
        hits = []
        for rec in log.split("\x1e"):
            if not rec.strip():
                continue
            h, d, s, body = (rec.strip("\n").split("\x1f") + ["", "", "", ""])[:4]
            msg = (s + "\n" + body).lower()
            kws = [k for k in KEYWORDS if k in msg]
            if kws:
                hits.append({"commit": h[:12], "date": d, "subject": s, "keywords": kws})
        searches.append({"branch": branch, "commit": full[:12], "kind": "commit messages",
                         "keywords": KEYWORDS, "candidate_items": len(hits), "hits": hits})

        # git search (b): diffs between consecutive tags
        if branch == "main":
            tags = [t for t in git("tag", "-l", "paper1-freeze-*", "--sort=creatordate").split() if t]
        else:
            tags = [t for t in git("tag", "-l", "paper4-freeze-*", "--sort=creatordate").split() if t]
        diffs = []
        for t0, t1 in zip(tags, tags[1:]):
            changed = [f for f in git("diff", "--name-only", t0, t1).splitlines()
                       if any(f.startswith(p) for p in DIFF_PATHS)]
            diffs.append({"from": t0, "to": t1, "files_changed": len(changed), "files": changed})
        searches.append({"branch": branch, "commit": full[:12], "kind": "diffs between consecutive tags",
                         "paths": DIFF_PATHS, "tags": tags,
                         "candidate_items": sum(d["files_changed"] for d in diffs), "diffs": diffs})

    inv = {"p0": {"main": a.main, "paper4": a.paper4}, "sources": entries, "git_search": searches}
    js = json.dumps(inv, indent=1, ensure_ascii=False, sort_keys=True).encode()
    (out / "inventory.json").write_bytes(js)
    jsha = sha(js)

    lines = ["# Inventory of the sources (P0 §3, phase 1)", "",
             f"Branches at the commits declared in P0: `main` {a.main}, `paper4` {a.paper4}. "
             f"Read through `git show`; the working tree was not read. `inventory.json` sha256 `{jsha}`.", "",
             "## Sources", "", "| Branch | Class | Path | sha256 (16) | Candidate items | Rule |",
             "| --- | --- | --- | --- | --- | --- |"]
    for e in sorted(entries, key=lambda e: (e["branch"], e["class"], e["path"])):
        ci = "" if e["candidate_items"] is None else str(e["candidate_items"])
        lines.append(f"| {e['branch']} | {e['class']} | `{e['path']}` | `{e['sha256'][:16]}` | {ci} | {e['rule'] or ''} |")
    lines += ["", "## Git search", ""]
    for s_ in searches:
        lines.append(f"- `{s_['branch']}` {s_['commit']}, {s_['kind']}: **{s_['candidate_items']}** candidate items"
                     + (f" ({len(s_['tags'])} tags)" if "tags" in s_ else ""))
    tot = {}
    for e in entries:
        if e["candidate_items"] is not None:
            tot[e["class"]] = tot.get(e["class"], 0) + e["candidate_items"]
    lines += ["", "## Totals of mechanically counted candidate items", ""]
    for k, v in sorted(tot.items()):
        lines.append(f"- {k}: {v}")
    for s_ in searches:
        lines.append(f"- git search, {s_['branch']}, {s_['kind']}: {s_['candidate_items']}")
    lines += ["", "Frozen records and regeneration reports are listed above with fingerprints; the flags they "
              "contain are extracted in phase 2 and are not counted here. Candidate items are not problems: "
              "separation, deduplication and status are decided in phase 3 (P0 §4, §8)."]
    (out / "INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"sources {len(entries)}; inventory.json sha256 {jsha}")


if __name__ == "__main__":
    sys.exit(main())
