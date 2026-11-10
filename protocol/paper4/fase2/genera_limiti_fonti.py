"""Regenerate protocol/paper4/fase2/LIMITI_FONTI.json from the repository at a given commit.

The structure of the file and its mapping are taken from the current LIMITI_FONTI.json and never changed: the list
and order of the files, `section_vi_support`, `required_for_section_vi_zip_check`, `role`, `version_note`,
`preregistration_commit`, `verification_note`, `intended_destination` and `paper_cross_references`. Only the fields
that identify the content are recomputed, all from git objects (the working tree is not read):

    inspected_head        the full hash of --at
    tag_at_head           the tags pointing at --at, sorted
    last_change_commit    the last commit at or before --at that changed the file
    blob                  the git blob of the file at --at
    sha256                the SHA-256 of that blob's content
    preregistration_blob, preregistration_sha256
                          the same for the file at its `preregistration_commit` (P4A), which is not changed

Usage, from the root of the repository:

    python protocol/paper4/fase2/genera_limiti_fonti.py                 # at HEAD, writes the file
    python protocol/paper4/fase2/genera_limiti_fonti.py --check         # at HEAD, exit 1 if the file differs
    python protocol/paper4/fase2/genera_limiti_fonti.py --at 2849887 --check
                                                                        # reproduces the file of 17ad609

To be run on the last commit before the tag; the commit that records the new file changes only this file, which is
not among the files it lists, so the recorded values stay valid at the tag.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = Path("protocol/paper4/fase2/LIMITI_FONTI.json")


def git(*args, binary=False):
    out = subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True).stdout
    return out if binary else out.decode().strip()


def identify(ref, path):
    """blob and sha256 of `path` at `ref`; refuses if the file is absent."""
    try:
        blob = git("rev-parse", f"{ref}:{path}")
    except subprocess.CalledProcessError:
        sys.exit(f"{path} does not exist at {ref}: refused")
    return blob, hashlib.sha256(git("cat-file", "blob", blob, binary=True)).hexdigest()


def generate(template, ref):
    head = git("rev-parse", "--verify", f"{ref}^{{commit}}")
    out = dict(template)
    out["inspected_head"] = head
    out["tag_at_head"] = sorted(t for t in git("tag", "--points-at", head).splitlines() if t)
    files = []
    for entry in template["files"]:
        e = dict(entry)
        p = e["path"]
        e["blob"], e["sha256"] = identify(head, p)
        e["last_change_commit"] = git("log", "-1", "--format=%H", head, "--", p)
        if "preregistration_commit" in e:
            e["preregistration_blob"], e["preregistration_sha256"] = identify(e["preregistration_commit"], p)
        files.append(e)
    out["files"] = files
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--at", default="HEAD", help="the commit to inspect (default HEAD)")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if the file differs")
    ap.add_argument("--template", type=Path, default=ROOT / TARGET,
                    help="the file whose structure and mapping are kept (default: the current LIMITI_FONTI.json)")
    a = ap.parse_args()
    template = json.loads(a.template.read_text())
    new = generate(template, a.at)
    text = json.dumps(new, indent=2) + "\n"
    kept = ("section_vi_support", "required_for_section_vi_zip_check", "role", "version_note", "preregistration_commit")
    assert [e["path"] for e in new["files"]] == [e["path"] for e in template["files"]]
    assert all(e.get(k) == t.get(k) for e, t in zip(new["files"], template["files"]) for k in kept)
    if a.check:
        same = (ROOT / TARGET).read_text() == text
        print(f"{TARGET} at {new['inspected_head'][:7]}: {'identical' if same else 'DIFFERS'}")
        for e, t in zip(new["files"], json.loads((ROOT / TARGET).read_text())["files"]):
            if e != t:
                print(f"  {e['path']}: " + ", ".join(k for k in e if e[k] != t.get(k)))
        sys.exit(0 if same else 1)
    (ROOT / TARGET).write_text(text)
    print(f"{TARGET} written at {new['inspected_head'][:7]} ({len(new['files'])} files; "
          f"tags {new['tag_at_head'] or 'none'})")


if __name__ == "__main__":
    main()
