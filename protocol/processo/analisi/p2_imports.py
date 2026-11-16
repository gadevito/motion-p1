#!/usr/bin/env python3
"""P2 — static import check of an export zip (P0 §10).

Parses every .py in the zip, collects the top-level names it imports, and sorts them into:
  stdlib             ignored
  inside the zip     a module or package of the same name is in the zip
  EXCLUDED by export a module or package of that name exists in the EXCLUDED list -> the
                     reviewers would get code that cannot run: widen the scope or justify
  third party        everything else (numpy, torch, ...): must be covered by the pyproject files

Usage: python3 p2_imports.py ../p2-export/P2_paper1_<tag>.zip ../p2-export/P2_paper1_EXCLUDED.txt
"""
import ast, sys, zipfile
from pathlib import PurePosixPath

zpath, expath = sys.argv[1], sys.argv[2]
excluded = [l.strip() for l in open(expath, encoding="utf-8") if l.strip()]
with zipfile.ZipFile(zpath) as z:
    names = [n for n in z.namelist() if not n.endswith("/")]
    local = set()
    for n in names:
        parts = PurePosixPath(n).parts
        local.update(parts[:-1])
        if n.endswith(".py"):
            local.add(PurePosixPath(n).stem)
    ex_names = set()
    for n in excluded:
        parts = PurePosixPath(n).parts
        ex_names.update(parts[:-1])
        if n.endswith(".py"):
            ex_names.add(PurePosixPath(n).stem)
    imports = {}
    bad = []
    for n in names:
        if not n.endswith(".py"):
            continue
        try:
            tree = ast.parse(z.read(n), filename=n)
        except SyntaxError as e:
            bad.append(f"{n}: {e}"); continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imports.setdefault(a.name.split(".")[0], set()).add(n)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                imports.setdefault(node.module.split(".")[0], set()).add(n)
std = set(sys.stdlib_module_names)
groups = {"inside the zip": [], "EXCLUDED by export": [], "third party": []}
for name, users in sorted(imports.items()):
    if name in std:
        continue
    g = "inside the zip" if name in local else ("EXCLUDED by export" if name in ex_names else "third party")
    groups[g].append((name, len(users), sorted(users)[:3]))
print(f"{zpath}: {len(names)} files, {sum(1 for n in names if n.endswith('.py'))} python")
for g, rows in groups.items():
    print(f"\n[{g}] {len(rows)}")
    for name, k, ex in rows:
        print(f"  {name:28s} used by {k:3d} file(s)  e.g. {', '.join(ex)}")
if bad:
    print("\n[syntax errors]"); [print("  " + b) for b in bad]
