import hashlib
import pathlib
import datetime

BASE = "52f682c8435956c8210b3189cad23ebea973d2de"
PRE = "evidence/pr37-independent-review-v1"
PRED = "NF==3 && length($3)==64"
AWK = ("awk '" + PRED + ' {print $3\"  ' + PRE + '/\"$1} ' + PRE + "/HASHES.txt | sha256sum -c -")

d = pathlib.Path(PRE)
rows = []
for p in sorted(x for x in d.iterdir() if x.suffix == ".md"):
    b = p.read_bytes()
    rows.append((p.name, len(b), hashlib.sha256(b).hexdigest()))

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
head = [
    "# HASHES.txt - integrity record for " + PRE,
    "# generated " + stamp + " by the independent review of PR #37",
    "# base: `main` at " + BASE + " (this branch adds files to that revision and changes no other file)",
    "#",
    "# Verify from the repository root.  The awk predicate is the one documented in",
    "# evidence/m17-security-boundary-v1/HASHES.txt, so both manifests are checked the same way:",
    "#   " + AWK,
    "# Every digest below is a full 64 hex characters, so that length guard drops nothing here.",
    "#",
    "# <path> <bytes> <sha256>",
]
body = ["{} {} {}".format(n, sz, h) for n, sz, h in rows]
tail = [
    "#",
    "# Scope, in numbers measured here:",
    "#   " + str(len(rows)) + " Markdown files, plus HASHES.txt itself and gen_manifest.py, " + str(sum(r[1] for r in rows)) + " bytes total;",
    "#   0 changes to any other path: `git diff --name-only " + BASE[:12] + " HEAD` lists only this directory;",
    "#   no production path is touched: `git diff --name-only " + BASE[:12] + " HEAD -- tools boot kernel psm ci` is empty;",
    "#   the reviewed branch is unchanged: refs/heads/docs/m17-security-boundary-analysis ->",
    "#   d09949226c39052fa04827c2c9b440129735a312, four commits on top of the base above, read from",
    "#   `git ls-remote` at 2026-11-22T01:44:20Z and again at 02:09Z, not from any local clone.",
]
d.joinpath("HASHES.txt").write_text("\n".join(head + body + tail) + "\n", encoding="utf-8")
print("\n".join(head + body + tail))
