# PR #37 — additive correction proposal, 2026-11-22

Companion to `PR37-INDEPENDENT-REVIEW-20261122.md` (same directory). That file carries the
measurements; this one carries only the text, so that whoever owns `docs/m17-security-boundary-analysis`
can take or leave each item without re-deriving anything.

**Why this is a proposal and not a commit on #37's branch.** The review that produced these findings
was instructed not to edit that branch, and it did not: `docs/m17-security-boundary-analysis` is still
at `d09949226c39052fa04827c2c9b440129735a312` with its four commits unchanged, and nothing was pushed
to it. `main` at `52f682c8435956c8210b3189cad23ebea973d2de` — the base both branches share — does not
contain `docs/playstation/SECURITY_BOUNDARY.md` at all:

```
$ git ls-files docs/playstation/SECURITY_BOUNDARY.md          # at main, this clone
  (no output)
$ git grep -l 'SECURITY_BOUNDARY' 52f682c8
docs/architecture/roadmap.json
```

So no correction can be applied "against main" in the ordinary sense: there is nothing here to patch,
and adding the file here would duplicate it. The honest shape is additive — a branch off verified
`main` carrying the proposed edits as text, which the branch owner applies to `d099492` (or a reviewer
applies later as a follow-up commit) and which costs nothing if #37 merges as-is and is corrected
afterwards.

Each item below gives the file, the line at `d099492`, the text as published, the replacement, and
the measurement that justifies it. Nothing here alters a conclusion, a count, a classification of a
step, or the boundary itself.

## C1 — F1: name the module that enforces the vocabulary (`psm/registry.py` → `psm/contract.py`)

`docs/playstation/SECURITY_BOUNDARY.md`, §0, line 34.

As published:

```
machine-checkable meaning here — the rule engine in `psm/registry.py` rejects any other value — so
```

Proposed:

```
machine-checkable meaning here — the rule engine in `psm/contract.py` rejects any other value, over
the data declared in `psm/registry.py` — so
```

Measurement: `grep -cE '^(def |class |    def )' psm/registry.py` = **0**; the module declares
`SOURCES`, `CLAIMS`, `DECISIONS` and instantiates `Contract` at `psm/registry.py:543`. The vocabulary
is `psm/contract.py:36` (`CLASSIFICATIONS = ("PUBLIC", "INFERRED", "UNKNOWN", "RESTRICTED")`) and the
rejection is in `Contract.problems()` (`psm/contract.py:114`, check at `:142–143`), reached by
`python3 -m psm.contract` (`Makefile:293`, inside `psm`, inside `check`).

Why the extra half-clause instead of a bare rename: `psm/registry.py` is genuinely involved — it is
the data the rules run over, and M10's own roadmap string ("`psm/` — evidence registry, rule engine,
…") and `PS5_PLATFORM_CONTRACT.md:7` both name the two things adjacently, which is where the slip came
from. Keeping both names, each with its correct role, prevents the next reader from re-fusing them.

## C2 — F2: qualify the test id so it resolves

`docs/playstation/SECURITY_BOUNDARY.md`, §4 table, line 287.

As published (tail of the row):

```
and `tests/test_psm_registry.py::test_security_is_restricted_and_has_no_interface` enforces that in code |
```

Proposed:

```
and `tests/test_psm_registry.py::RegistryRulesTest::test_security_is_restricted_and_has_no_interface`
enforces that in code |
```

Measurement: the function is a method of `RegistryRulesTest` (`tests/test_psm_registry.py:30`, method
at `:82`). `python3 -m unittest tests.test_psm_registry.test_security_is_restricted_and_has_no_interface`
exits **1** with an error; the qualified dotted form exits **0** (`Ran 1 test … OK`). The repository's
test runner is `unittest`, not `pytest` (`pytest` is not installed here), so the `file::test` shape has
no lenient interpretation to fall back on. The PR's own transcript already uses the qualified form, at
`evidence/m17-security-boundary-v1/VERIFICATION-20261122.log:146`, so this also removes a
disagreement between the deliverable and its evidence.

## C3 — F3: source the Safe-Mode detail, or drop the operational half

`docs/playstation/SECURITY_BOUNDARY.md`, §2, line 110, the `Requirement` cell of row S10.

As published:

```
the console only accepts the file when entered through its own Safe Mode procedure (power-button sequence, `PS5/UPDATE/PS5UPDATE.PUP`)
```

Proposed (preferred — keeps the requirement, removes the unsourced detail):

```
the console only accepts the file when entered through its own service-mode update procedure; the entry sequence and the on-device path are Sony-side UI facts, not requirements PC5 can satisfy |
```

Alternative, if the detail is to stay: cite it in §9 by URL (Sony's published support page) and date of
retrieval, exactly as the four emulator sources are cited, and re-tag the row's support column to name
that source rather than "Sony's support instructions" in the abstract.

Measurement: `evidence/m17-security-boundary-v1/FALSIFIER-SOURCE-EXTRACTS-20261122.md` — the PR's own
extract file — contains no power-button sequence and no `PS5/UPDATE/…` path; its only relevant lines are
`:100` (the phrase "safe mode" inside a sentence about a third-party repository) and `:127` (Sony's
"official update file provided" quote). Repository-wide, both strings appear only in
`SECURITY_BOUNDARY.md` itself. And §2's own rule at `:84` says "**No step is described by mechanism.**" —
the parenthetical is the one place in §2 that reads as a mechanism.

Scope note, so this is not over-read as a request to soften the row: the *verdict* is unaffected either
way. S10's `PC?` value (`n/a`) and its conclusion (acceptance is gated console-side) follow from
`docs/FIRMWARE_ANALYSIS.md` §2 and `docs/PS5_SYSTEM_SOFTWARE_TARGET.md` §5, which the file cites.

## C4 — F4(a): make the cross-reference name its list

`docs/playstation/SECURITY_BOUNDARY.md`, §5, line 299.

As published:

```
roadmap forbids those five as destination evidence, and this document inherits the prohibition.
```

Proposed:

```
roadmap forbids destination evidence of exactly those five classes — its `must_not_be_satisfied_by` list, and the sentence above is this document's own restatement of it — and this document inherits the prohibition.
```

Measurement: `product.destination.must_not_be_satisfied_by` in `docs/architecture/roadmap.json` has
exactly **5** items; the sentence immediately before `:299` enumerates **6** artefacts (emulator, stub,
mock, firmware map, boot log, `make check`). Both counts are individually right, which is the
problem: the reader cannot tell which the "those" refers to. No wording change is needed to the list
itself.

## C5 — F4(b): describe the quoted line as what it is

`docs/playstation/SECURITY_BOUNDARY.md`, §6, line 327.

As published:

```
`tools/presentation.py` line 686 prints "analysed, decrypted or executed | **no**, in any sense").
```

Proposed:

```
`tools/presentation.py` line 686 renders the table row "analysed, decrypted or executed | **no**, in any sense" as part of the generated status document).
```

Measurement: `sed -n '686p' tools/presentation.py` is
`    lines.append("| analysed, decrypted or executed | **no**, in any sense |")`. The quote is accurate
as a substring; the verb is not what the line does. The other four citations in the same clause
(`tools/firmware.py:13,166,219`, `tools/pc5ctl.py:8`) are genuine refusal statements and need no
change, and the clause's count is right: `grep -rn 'decrypt' tools psm kernel | wc -l` = **5**.

## C6 — F6(a): state the meaning of "no crypto library"

`docs/playstation/SECURITY_BOUNDARY.md`, §6, lines 324–325.

As published:

```
`tools/`, `psm/`, `kernel/` for crypto primitives and library imports on 2026-11-22 found no crypto
library imported anywhere in them, and the only occurrences of the words `decrypt` in `tools/` are
```

Proposed:

```
`tools/`, `psm/`, `kernel/` for crypto primitives and library imports on 2026-11-22 found no cipher,
MAC, key-derivation, signature or TLS import anywhere in them — the only cryptographic-adjacent import
is `hashlib`, in 10 files under `tools/`, used for SHA-256 integrity records — and the only
occurrences of the words `decrypt` in `tools/` are
```

Measurement: `grep -rnE 'import (Crypto|Cryptodome|nacl|ssl)|from (Crypto|Cryptodome|nacl|ssl)' tools psm kernel`
→ 0 lines; `grep -rln 'import hashlib' tools/*.py | wc -l` → **10**; `grep -rhoE 'hashlib\.[a-z_0-9]+' tools psm kernel | sort -u`
→ `hashlib.sha256`, only; `grep -rnE '\bhmac\b|pbkdf2|AES|Cipher|sign\(|verify_signature|tls' tools psm kernel | wc -l` → 0.
The published sentence is defensible but its plain-English reading ("no crypto at all") is stronger
than the measurement, and a document about classification should not leave a term to be inferred.

## C7 — F5: label the revision each gate block tested, and cover the head

`evidence/m17-security-boundary-v1/VERIFICATION-20261122.log`, §10 (lines 180–232).

Add one line under the §10 heading, and one block at its end:

```
Revisions read by this section: refs as of 2026-11-22T01:33:56Z, when `docs/m17-security-boundary-analysis`
was at `c118e67a`; the gate commands below were executed at that revision, before `d099492` was committed.

## 10b. Third pass, at the final head `d099492`
    $ git worktree add --detach /tmp/r-head d09949226c39052fa04827c2c9b440129735a312
    $ cd /tmp/r-head && TMPDIR=/tmp make check
      PASSED: 165 checks, 0 failures · DOCS OK: 71 · CITATIONS OK: 258 · PRESENTATION OK (13 status rows)
      Ran 933 tests in 61.734s · OK (skipped=109)                                    exit 0
    (independently reproduced by the review in evidence/pr37-independent-review-v1/; the
     delta from c118e67 to d099492 is 4 files, all Markdown plus the regenerated HASHES.txt,
     117 insertions / 15 deletions — no file the test suite imports)
```

Measurement: `git diff --stat c118e67a d099492` = `docs/playstation/SECURITY_BOUNDARY.md` +45/−…,
`AUDIT-PR36-20261122.md`, `HASHES.txt`, `VERIFICATION-20261122.log` +58; 4 files, +117/−15. The
numbers §10 carries are correct — they match runs made here at *both* revisions, 933 tests and
`skipped=109` at each — so this is provenance hygiene, not a substantive gap. It is worth doing
because "which revision was tested" is the one question this evidence directory exists to answer.

## C8 — optional, and not required for merge

Two sentences that would make the document harder to misuse, both purely additive:

1. In §9, next to the star counts, note that they are volatile metadata retrieved on a date and are
   cited to characterise activity, not to support a technical conclusion. Measured:
   `grep -in 'volatile' docs/playstation/SECURITY_BOUNDARY.md` → no matches, so the caveat is currently
   implicit.
2. In §5's S9 row, name `S-SONY-2020` where the storage figure appears. It is already defined
   (`psm/registry.py:73`) and already used by `C-STO-01` (`PS5_PLATFORM_CONTRACT.md:411`) for
   825 GB / 5.5 GB/s; only §9's nine-source list omits naming it, so a reader checking §9 alone finds
   no source for the hardware numbers. Nothing is wrong; one token would make it traceable.

## What a merge-without-correction would cost

Nothing that changes a decision. F1 and F2 send a reader to a file with no code in it and to a test id
that does not run; F3 leaves one operational fragment unsourced in a document that forbids
distribution-adjacent instruction; F4/F6 leave three sentences stronger than their measurements; F5
leaves the head commit without a recorded full-suite run in its own transcript (closed by §6.1 of the
review). All five are text. None of them touches `tools/`, `boot/`, `kernel/`, `psm/`, `ci/`, the USB
path, the refusal list, or a milestone `state` — which is why the review records #37 as ready for an
explicit merge decision rather than as blocked on these corrections.
