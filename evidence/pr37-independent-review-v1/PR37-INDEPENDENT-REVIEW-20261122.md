# PR #37 — independent review, dated 2026-11-22

Reviewer: this workstream. Not the author of PR #37, and not a re-run of the author's own checks:
every number below was produced by commands executed here, against objects fetched from GitHub, in
throwaway worktrees — and where a figure also appears in the PR's own transcript, it is marked
`reproduced` rather than `inherited`.

What PR #37 is: `docs/m17-security-boundary-analysis`, four commits
(`b1b4580` → `6b6a7a5` → `c118e67` → `d099492`) on top of `main` at
`52f682c8435956c8210b3189cad23ebea973d2de`, nine files, +1,538 lines, nothing removed. Its
deliverable is `docs/playstation/SECURITY_BOUNDARY.md` (452 lines) plus a five-file evidence
directory and one new test module (`tests/test_milestone_deliverables.py`, 165 lines).

**Standing constraints honoured here.** PR #37 was not merged, approved, commented on, or modified.
Its branch was not pushed to. `main` was not pushed to. No history was rewritten. The review record
is additive and lives on its own branch (`docs/pr37-independent-review`) off verified `main`, so it
can be read whether or not #37 merges. Corrections are *proposed* in
`CORRECTION-PROPOSAL-20261122.md`, in the same directory, with the exact replacement text; applying
them is the branch owner's act or a follow-up, not this review's.

## 1. Remote state, read from the remote

`main` and the PR head were re-read from GitHub, not from any local clone.

```
$ git ls-remote https://github.com/SpicyBadran/PC5.git | grep -E 'refs/heads/(main|docs/m17)'
  refs/heads/docs/m17-security-boundary-analysis -> d09949226c39052fa04827c2c9b440129735a312
  refs/heads/main                                -> 52f682c8435956c8210b3189cad23ebea973d2de

$ gh pr view 37 --json isDraft,state,baseRefOid,headRefOid,mergeable,reviewDecision,commits
  isDraft=true  state=OPEN  baseRefOid=52f682c8…  headRefOid=d0994922…
  mergeable=true / mergeableState=clean  reviewDecision=(empty)  4 commits
```

Status checks: `gh pr checks 37` reports "no checks reported on the 'docs/m17-security-boundary-analysis'
branch"; `check-runs` and `check-suites` are both empty arrays. Branch protection returned **HTTP
403**, i.e. not readable with this token. So the absence of checks is recorded as *absent from the
API*, and the absence of a protection rule as **unknown** — not as "no rule". `mergeable=clean`
means "no textual conflict"; it is not review, approval, or evidence of correctness, and nothing in
this record treats it as any of those.

`/home/user/pc5` (the original workspace, `arena/c8a76776-pc5` at `56c5852`) was not read into any
conclusion and not modified.

## 2. Method

Six things made this a review instead of a re-run:

1. **The whole diff was read**, not the summary: `git diff --stat 52f682c..d099492` = 9 files,
   +1,538/−0, and all 1,538 lines were read (`SECURITY_BOUNDARY.md` in full, §0–§10).
2. **The documents #37 depends on were read at the same revision**, because a claim about a source
   is only as good as the source: `docs/playstation/BOOT_FEASIBILITY.md` (§1–§7),
   `docs/FIRMWARE_ANALYSIS.md` (§2, §5), `docs/PS5_SYSTEM_SOFTWARE_TARGET.md` (§1, §3.1, §4–§8),
   `docs/playstation/RESEARCH_LOG.md`, `docs/architecture/PS5_PLATFORM_CONTRACT.md` (§3.7, §7, the
   interface census, the revision log), `docs/KNOWN_LIMITATIONS.md`, `docs/TECHNICAL_DECISIONS.md`,
   `docs/architecture/roadmap.json`, `BUILDING.md`.
3. **The code the document describes was read**, and the described facts were re-derived from it
   rather than from the document's own prose (§3, findings F1, F2, F6).
4. **Every gate figure was produced by a run performed here.** The PR head was checked out into a
   detached worktree and the full suite executed; `main` was checked out separately and executed the
   same way, so the "before" numbers are also local (§6). No figure in §6 is quoted from the PR.
5. **External claims were re-retrieved from primary sources** through the GitHub API at the time of
   review (§4.3, §4.6) — repository READMEs and licence fields, not the PR's summary of them.
   Star counts were retrieved but are treated as volatile metadata and are *not* counted as
   technical evidence; #37 itself does not use them that way.
6. **The negative control was reproduced in isolation**, in a worktree of `main` with only the new
   test file copied in, to see whether the test actually fails on the defect it claims to catch
   (§6.3). It does, with a diagnostic that names the milestone and the missing path.

Classification vocabulary for the findings, as required: `confirmed`, `confirmed with qualification`,
`unsupported`, `incorrect`, `not independently verifiable`. Each finding carries the file, section,
line range and the command output that decides it.

## 3. Findings

Six findings. One is an outright error, two are references that do not resolve, two are precision
defects, one is a provenance gap in the transcript. **None of them weakens the security boundary,
touches a production path, or changes a milestone state.** Three of them are one-line fixes.

| # | Class | Where | One line |
|---|---|---|---|
| F1 | `incorrect` | `docs/playstation/SECURITY_BOUNDARY.md` §0, :34 | attributes the classification rule engine to `psm/registry.py`, which contains no code |
| F2 | `unsupported` | same file, §4 (table), :287 | the test id it cites does not resolve; the class name is missing |
| F3 | `unsupported` | same file, §2, :110 | a Safe-Mode power-button entry sequence and an on-device path are asserted with no source in the PR's own extract file |
| F4 | `confirmed with qualification` | same file, §5 :299 and §6 :323–327 | a cross-reference whose number matches a different list; a quote presented as a printed sentence is a table row |
| F5 | `confirmed with qualification` | `evidence/m17-security-boundary-v1/VERIFICATION-20261122.log` §10, :180–232 | the recorded full-suite gate corresponds to `c118e67`, not to the final head; the final head's run was not in the transcript (it is here) |
| F6 | `confirmed with qualification` | `docs/playstation/SECURITY_BOUNDARY.md` §6 :323–325; §9 | "no crypto library imported anywhere in them" is true under a stated meaning of *crypto*; ten modules do import `hashlib` |

### F1 — `psm/registry.py` is not the rule engine (class: `incorrect`)

The document's opening method section says the repository's classification markers carry
machine-checkable meaning because a rule engine rejects any other value — and names the wrong file.
Verbatim, at `docs/playstation/SECURITY_BOUNDARY.md` §0, lines 33–35:

```
machine-checkable meaning here — the rule engine in `psm/registry.py` rejects any other value — so
they are what the tables use:
```

Measured at `d099492`:

```
$ grep -cE '^(def |class |    def )' psm/registry.py
0
$ grep -n '^[A-Z_]+ *[:=]' psm/registry.py
29:SOURCES: Tuple[Source, ...] = (
79:CLAIMS: Tuple[Claim, ...] = (
472:DECISIONS: Tuple[dict, ...] = (
543:CONTRACT = Contract(sources=SOURCES, claims=CLAIMS, revision="r1 (2026-11-16)")
```

`psm/registry.py` is a data table: `SOURCES`, `CLAIMS`, `DECISIONS`, and the one line that
instantiates `Contract`. It has no `def` and no `class`. The vocabulary and its enforcement both
live next door:

```
$ grep -n 'CLASSIFICATIONS = \|    def problems' psm/contract.py
36:CLASSIFICATIONS = ("PUBLIC", "INFERRED", "UNKNOWN", "RESTRICTED")
114:    def problems(self) -> List[str]:
$ sed -n '142,143p' psm/contract.py
            if claim.classification not in CLASSIFICATIONS:
                found.append(f"claim {claim.id}: unknown classification {claim.classification!r}")
```

`Contract.problems()` is what rejects an unknown value; it runs through
`python3 -m psm.contract`, which is the first command of the `psm` target and therefore of
`make check` (`Makefile:292–296`). `psm/contract.py`'s own docstring says so: "the platform-contract
registry: claims, sources, and the rules that keep them honest".

Why the slip is understandable, and why it still matters. `docs/architecture/roadmap.json` describes
M10's deliverable as "`psm/` — evidence registry, rule engine, linkage audit and ten interfaces",
and `docs/architecture/PS5_PLATFORM_CONTRACT.md:7` as "`psm/` — the registry, the rule engine and
the ten PC5-authored doubles": two module-level nouns fused into one filename. `tests/test_psm_registry.py`
makes it worse in a specific way — it *tests* the rule engine but is named after the registry, and
the class that does the mutating is `RuleEngineTest` (`tests/test_psm_registry.py:89`). A reader
who followed #37's sentence to `psm/registry.py` and then to its tests would find the rule they were
told to distrust is enforced somewhere else. The claim being made (that an unknown classification is
rejected by machine, not by prose) is **true**; only the module is wrong. The fix is one word:
`psm/contract.py`.

### F2 — the registry test id at :287 does not resolve (class: `unsupported`)

The inventory's S7 row cites the test that enforces the "security is `RESTRICTED`, and has no
interface" rule. Verbatim, `docs/playstation/SECURITY_BOUNDARY.md:287`:

```
| S7 platform authorisation state | **no** | `UNKNOWN`/`RESTRICTED` mixture; the contract keeps the
whole subsystem out of the interfaces, and
`tests/test_psm_registry.py::test_security_is_restricted_and_has_no_interface` enforces that in code |
```

(line-wrapped here for reading; it is one line in the file.) That is the only reference to that test
anywhere in the deliverable. The named function is not module-level:

```
$ grep -n '^class \|^def \|^    def test_security' tests/test_psm_registry.py
30:class RegistryRulesTest(unittest.TestCase):
82:    def test_security_is_restricted_and_has_no_interface(self):
89:class RuleEngineTest(unittest.TestCase):
156:class LinkageAuditTest(unittest.TestCase):

$ python3 -m unittest tests.test_psm_registry.test_security_is_restricted_and_has_no_interface   # as cited
  FAILED (errors=1)                                                  exit 1
$ python3 -m unittest tests.test_psm_registry.RegistryRulesTest.test_security_is_restricted_and_has_no_interface
  Ran 1 test in 0.000s
  OK                                                                  exit 0
```

`pytest` is not installed in this environment, so the `file::test` form cannot be run as a pytest
node id here; under `unittest` — the runner this repository uses — it resolves to nothing. The PR's
own transcript already contains the correct qualified form at
`evidence/m17-security-boundary-v1/VERIFICATION-20261122.log:146`:

```
        tests.test_psm_registry.RegistryRulesTest.test_security_is_restricted_and_has_no_interface
```

so the document and the transcript disagree about the same test. This is a citation defect in the
artefact whose whole subject is citation discipline, which is why it is filed at all: the enforced
rule (`docs/playstation/SECURITY_BOUNDARY.md:287`, `C-SEC-01` at
`docs/architecture/PS5_PLATFORM_CONTRACT.md:627`) is real and the test does cover it.

### F3 — the Safe-Mode entry sequence at :110 has no source in this PR (class: `unsupported`)

Verbatim, `docs/playstation/SECURITY_BOUNDARY.md:110` (§2, inventory row S10):

```
| S10 | Update/recovery mode entry | the console only accepts the file when entered through its own
Safe Mode procedure (power-button sequence, `PS5/UPDATE/PS5UPDATE.PUP`) | console service mode |
the console's UI and its own integrity state | n/a | `PUBLIC` (Sony's support instructions) | high |
```

The PR's source-extract file for exactly this kind of assertion is
`evidence/m17-security-boundary-v1/FALSIFIER-SOURCE-EXTRACTS-20261122.md`. Searching it:

```
$ grep -in 'power\|safe mode\|rest mode\|update file provided' evidence/m17-security-boundary-v1/FALSIFIER-SOURCE-EXTRACTS-20261122.md
14:   … (a sentence about which official update file the console will accept)
100:  … "safe mode" appears inside a sentence about the MewX repository and a PS5 shell
127:  "…only an official update file provided by Sony…"
```

Those are the only relevant lines, and none of them contains a power-button sequence or the path
`PS5/UPDATE/PS5UPDATE.PUP`. A repository-wide search at the same revision finds the same two strings
only inside `SECURITY_BOUNDARY.md` itself:

```
$ grep -rn 'PS5/UPDATE/PS5UPDATE.PUP\|power button\|power-button' docs/ evidence/m17-security-boundary-v1/ \
    | grep -v '^docs/playstation/SECURITY_BOUNDARY'
  (no output)
$ grep -n 'power-button' docs/playstation/SECURITY_BOUNDARY.md
110
```

So the row's two parenthesised details are asserted *here* without a source *here*. Two
qualifications, both in the PR's favour and both stated in the file: the classification given is
`PUBLIC`, the material is Sony's published support documentation rather than anything proprietary,
and the document's §0 already warns that a `PUBLIC` class means "publicly documented", not
"independently re-fetched by this workstream". The row's *conclusion* — that acceptance of an update
file is gated by console-side service-mode state rather than by anything PC5 can supply — follows
from `docs/FIRMWARE_ANALYSIS.md` §2 and from `docs/PS5_SYSTEM_SOFTWARE_TARGET.md` §5 and is not in
doubt. What is not supported is the specific, operationally-shaped detail. Either drop the
parenthetical, or cite the Sony support page by URL in §9. That matters more than it looks in a
document whose §6 item 5 forbids distributing anything derived from proprietary material: a
step-by-step entry sequence reads as an instruction, whereas "the console gates acceptance on its
own service-mode state" reads as a requirement. The latter is what the rest of the table does, and
`:84` says so — "**No step is described by mechanism.**"

### F4 — two places where the sentence is looser than the list (class: `confirmed with qualification`)

**(a) `:298–299`, "those five".**

```
successful `make check` run must never be presented as genuine system-software execution; the
roadmap forbids those five as destination evidence, and this document inherits the prohibition.
```

The immediately preceding sentence enumerates **six** artefacts (an emulator, a stub, a mock, a
firmware map, a boot log from PC5's own kernel, a successful `make check` run), so "those five"
does not point at its own list. It *does* match the roadmap's list, which has exactly five:

```
$ python3 -c "…print len(must_not_be_satisfied_by)…"
5
  - a PC5 kernel booting
  - a simulated or modelled environment running PC5 payloads
  - an imitation of the PS5 interface
  - an emulator menu PC5 drew
  - a screenshot without the software's own output
```

(`docs/architecture/roadmap.json`, `product.destination.must_not_be_satisfied_by`.) The count is
therefore correct against the thing cited and surprising against the sentence beside it, and the two
lists are not the same five items. Naming the source — "the roadmap's five `must_not_be_satisfied_by`
items" — removes the ambiguity without changing the meaning.

**(b) `:326–327`, a table row presented as a printed sentence.**

```
refusal statements (`tools/firmware.py` lines 13, 166, 219; `tools/pc5ctl.py` line 8;
`tools/presentation.py` line 686 prints "analysed, decrypted or executed | **no**, in any sense").
```

```
$ sed -n '686p' tools/presentation.py
    lines.append("| analysed, decrypted or executed | **no**, in any sense |")
```

The quoted text is a faithful substring of that line — nothing is invented — but the line is a
Markdown table row appended to a generated document, not a sentence the tool prints about itself. The
other four citations in the same clause are genuine refusal statements
(`tools/firmware.py:13,166,219`, `tools/pc5ctl.py:8`). "line 686 renders a table row saying" is the
honest shape. Word counts: the five occurrences of `decrypt` in `tools/`, `psm/`, `kernel/` are
these five, and there are no others —

```
$ grep -rn 'decrypt' tools psm kernel | wc -l
5
```

so the clause's substance ("the only occurrences of the word `decrypt` are refusals") is `confirmed`.

### F5 — the transcript's gate block predates the head it certifies (class: `confirmed with qualification`)

`evidence/m17-security-boundary-v1/VERIFICATION-20261122.log` §10, added by the final commit
`d099492` itself, records a second pass timestamped `2026-11-22T01:33:56Z`. Its own remote re-read
names the *penultimate* commit as the branch head:

```
$ sed -n '180p;213,215p' evidence/m17-security-boundary-v1/VERIFICATION-20261122.log
180: ## 10. Second pass, 2026-11-22T01:33:56Z — the same task re-issued, so the state was re-read rather than remembered
215:     refs/heads/docs/m17-security-boundary-analysis   -> c118e67a3806cc1518e036f387991c05796f1a74   (#37, this PR)

$ git diff --stat c118e67a d099492
 docs/playstation/SECURITY_BOUNDARY.md              | 45 +++++++++++++--
 evidence/m17-security-boundary-v1/AUDIT-PR36-20261122.md    | 17 +++++--
 evidence/m17-security-boundary-v1/HASHES.txt       | 12 ++---
 evidence/m17-security-boundary-v1/VERIFICATION-20261122.log | 58 ++++++++++++++++
 4 files changed, 117 insertions(+), 15 deletions(-)
```

Two consequences. (i) The `make check` figures in §10 were produced at `c118e67`; §10 does not state
that, and reads as though it certifies the head. (ii) The commit that §10 was appended by is the one
commit for which the transcript records **no** full-suite run — although it touches only Markdown and
the regenerated manifest, i.e. exactly the files `docs-check` reads and nothing the test suite
imports. The gap is a labelling one, not a substantive one, because it is closed by an actual run at
the final head: `Ran 933 tests`, `OK (skipped=109)`, `PASSED: 165 checks`, `DOCS OK: 71`, exit 0
(§6.1). Nothing in the PR is copied from an earlier run in a way that misrepresents it: the
transcript is dated, timestamped, and each block says which revision it read. The fix is one
sentence in §10 naming the tested revision (`c118e67`) and one further block for `d099492`.
Recommended regardless of whether the numbers happen to be stable.

### F6 — two claims that hold, with their definition needing to be in the text (class: `confirmed with qualification`)

**(a) `:324–325`, "grepping `tools/`, `psm/`, `kernel/` for crypto primitives and library imports on
2026-11-22 found no crypto library imported anywhere in them".** Reproduced:

```
$ grep -rnE 'import (Crypto|Cryptodome|nacl|ssl)|from (Crypto|Cryptodome|nacl|ssl)' tools psm kernel | wc -l
0
$ grep -rln 'import hashlib' tools/*.py | wc -l
10
$ grep -rhoE 'hashlib\.[a-z_0-9]+' tools psm kernel | sort -u
hashlib.sha256
$ grep -rnE '\bhmac\b|pbkdf2|AES|Cipher|sign\(|verify_signature|tls' tools psm kernel | wc -l
0
```

True, under the meaning the sentence needs: no cipher, MAC, KDF, signature or TLS primitive is
imported or called in those three directories; the only cryptographic-adjacent import is
`hashlib.sha256`, used for integrity records and content addressing. The clause would be stronger
and harder to misread if it said "no cipher, MAC, KDF, signature or TLS import; the only hash
primitive is SHA-256 (`tools/*.py`, 10 modules, for integrity records)". One adjacent claim in the
same paragraph is worth confirming because it is the one a reader might expect to be padded:
"`psm/` has no `security` module".

```
$ ls psm/*.py | wc -l && grep -rn 'PSM-SEC' psm/*.py | wc -l && test -f psm/security.py && echo present
15
0
```

Fifteen files, the fourteen named at `:328–330` plus `__init__.py`; no `PSM-SEC` string anywhere; no
`psm/security.py`. The enumeration is accurate as printed.

**(b) §9's characterisation of the public emulator landscape** (sharpemu, KytyPS5, RPCSX, MewX) was
re-retrieved from GitHub rather than accepted. All four statements check out; see §4.3 and §4.6. The
RPCSX line, which was the last item of the review still open at the time the PR's transcript was
written, is now `confirmed`: its README, fetched via `gh api repos/RPCSX/rpcsx/readme`, reads at line
4 `*An experimental PlayStation 4 and PlayStation 5 emulator for Linux written in C++*`, which is what
#37 says it says. (`gh api repos/RPCSX/rpcsx/contents/README.md` returns an empty body for this
repository because the README lives at `.github/readme.md` — a fetch-shape artefact, not absence of
content. The MewX line — that the repository offers binaries to people working on PS5 security
research — is likewise accurate: its README carries, verbatim, "**However, if you work on PS5
security research, then I'm happy to offer binaries that I have.**" Qualification kept, because
"offers binaries to researchers" is precisely the kind of sentence that must not be paraphrased into
"publishes firmware".)

## 4. The review questions, answered

### 4.1 The thirteen-step inventory (§2, :92–:104 and the §4 table)

Necessary, separated, and supported. `grep -c '^| S[0-9]'` over §2 gives **13** rows, S1–S13; §4's
per-step model table gives 13 verdict rows as well. The derivation sentence (`:80–86`) names four
sources and no count, so nothing is claimed about arithmetic between the sources and the table:
`BOOT_FEASIBILITY.md` §1 (11 numbered dependency rows), `FIRMWARE_ANALYSIS.md` §2 (package facts),
`PS5_SYSTEM_SOFTWARE_TARGET.md` §5 (installation sequence), plus `C-SEC-01`/`C-SEC-02`. The step set
is a superset of §1's chain in order, and each added row is traceable to one of the three other
sources. No inferred proprietary behaviour is presented as fact: every row whose subject is a
mechanism PC5 cannot see is classed `UNKNOWN` or `RESTRICTED`, and §2's `:84` states the rule that
made this testable ("**No step is described by mechanism.**" followed by "where no source names a
mechanism, the mechanism column of this table does not exist") — checked row by row; the mechanism
column does not exist anywhere in §2. `no-input`, `no-anchor`, `n/a` and `unknown` are used
consistently against the legend at `:88–:90`; the distinction the review asked for — an unavailable
**input** versus an unavailable **anchor** — is drawn and drawn correctly (S2/S3 are `no-input`,
S4/S5 are `no-anchor`). F3 is the only row carrying an unsupported detail, and it does not affect
its verdict.

### 4.2 The four-layer platform model (§4, `:262–:300`)

Layers distinguished, and the substitution failure mode is refused explicitly rather than by
omission. `:295–299` states the asymmetry once — a model that passes its own conformance suite is a
statement about the model — and §5's table rows keep "the model can define and pass **its own**
contract" separate from "the console accepts it". No row implies that Secure Boot, AMD PSB or a TPM
substitutes for another platform's anchor: S4 and S5 both say `no-anchor`, and `docs/KNOWN_LIMITATIONS.md`
keeps its wording. The emulator-conformance point is handled the same way: §5's S13 row answers
"a platform model's own acceptability" with **not decidable by modelling** and points at
`product.destination`'s evidence rule rather than at any test result. The rule that would be broken
by a weaker document — `C-SEC-01`'s RESTRICTED status, "not modelled — no PSM interface exists for
security state" (`docs/architecture/PS5_PLATFORM_CONTRACT.md:627`) — is quoted correctly and, at
`:287`, tied to a test that exists (F2 is about the id, not the rule).

### 4.3 Paths, falsifiers and counts (§3, `:150–:199`)

The counts the review was asked to confirm are exactly as stated in the document, and each was
re-measured from the source at the same revision:

| Claim in #37 | Source measured | Result |
|---|---|---|
| `BOOT_FEASIBILITY.md` §3 has **three** paths | `:54`–`:75` | `A.`, `B.`, `C.` — 3, confirmed |
| `BOOT_FEASIBILITY.md` §4 has **three** falsifiers | `:76`–`:87` | 3 conditions, ending "None has been observed." |
| `FIRMWARE_ANALYSIS.md` §5 has **four** | `docs/FIRMWARE_ANALYSIS.md` §5 | 4, confirmed |
| `PS5_SYSTEM_SOFTWARE_TARGET.md` §4 has **nine** rows | that file's §4 | 9, confirmed |

The mapping table at `:189–:198` preserves the separate meanings of the three lists and does not
merge them into a canonical list; §8.1 (`:372–:382`) does the specific useful thing — it locates an
earlier "four paths attributed to `BOOT_FEASIBILITY.md` §3" error, gives the measured command that
shows three, and fixes the sentence in place rather than silently restating it. "not observed as of
2026-11-22" is scoped correctly: it appears as a dated statement about the searches performed, never
as "does not exist" or "proven impossible", and §3/§5 keep the falsifier framing that would let a
later reader break the claim. §8.3 (`:383`) marks `BOOT_FEASIBILITY.md` §3B's "publicly
unattempted in full" as stale against the emulator landscape, which is the honest direction for the
correction to run. Emulator descriptions and dates were re-retrieved (see F6(b)): stars and dates are
citation-only metadata, and #37 uses them only to characterise activity, never to support a technical
conclusion. That is the standard the review asked for, so it is met — with one qualification worth
recording: `grep -in 'volatile' docs/playstation/SECURITY_BOUNDARY.md` finds nothing, so the document
never states in its own words that the star counts it cites will drift.

### 4.4 The security boundary (§6, `:301–:320`)

No bypass instruction, no obtaining-material instruction, no weakening anywhere in the diff. §6
restates the six prohibitions as a list and then says plainly that a boundary is not crossed by
describing it (`:318–:320` permits reading public documentation, measuring the repository, naming
requirements, classifying them, recording unknowns as unknowns — and nothing else). The prohibition
list itself:

```
306: 1. extracting or obtaining protected keys, in any form;
307: 2. decrypting protected proprietary payloads (the `PUP` and its inner components);
308: 3. bypassing a signature check, defeating an authentication step, or substituting a trust anchor;
309: 4. patching, modding or otherwise altering protected firmware to make it accept a foreign platform;
310: 5. unauthorised access to, or distribution of, proprietary Sony binaries or anything derived from them;
311: 6. any claim of Sony authorisation, of compatibility, or of genuine system-software boot, …
```

The only row in the whole PR that comes close to operational instruction is the F3 parenthetical, and
it is a fragment ("power-button sequence"), not a procedure. On the source side, `git diff --name-only
52f682c8..d099492` lists nine paths, all under `docs/playstation/`, `tests/`,
`evidence/m17-security-boundary-v1/`, plus `docs/architecture/roadmap.json`; `git diff 52f682c8..d099492
-- tools boot kernel psm src firmware ci ci/` is empty, and `docs/KNOWN_LIMITATIONS.md` is untouched
(lines :14 and :37 still say the tree has never been booted from a physical USB stick).

### 4.5 The regression test (`tests/test_milestone_deliverables.py`, 165 lines)

Derived from the real schema, not from a copied list, and it is the right narrow rule. It reads
`docs/architecture/roadmap.json` and takes the milestone structure from it; the one generalisation it
needs is a prose marker, and the file says so instead of hiding it (`:27–:34`, "The limitation,
stated rather than hidden … `M17` is recognised from the sentence in its `blocker`").

* **Does the rule derive from the schema?** Yes. `DOCUMENT` (`:55`) is
  `^(?:docs|tools|tests|psm|kernel|boot|ci|evidence)/[^\s]+\.(?:md|json|py|c|h)$` — "is this named
  deliverable a repository-relative document path" — applied to the real `deliverables` arrays. No
  roadmap field was invented, and `ANALYSIS_LICENCE = "only as analysis"` (`:58`) is read from
  existing `blocker` prose.
* **Precise enough?** `requires_its_documents()` matches **three** milestones at this revision:
  `M9`, `M10`, `M17`. That is wider than the module docstring's emphasis on `M17`, so the test is not
  a single-milestone special case — and, checked for false positives, both extra milestones do have
  their named documents present (`docs/PS5_SYSTEM_SOFTWARE_TARGET.md`, and M10's contract plus its
  `psm/` deliverables), so nothing fails that shouldn't. No false negatives: every `blocked`
  milestone naming a document that is absent is exactly the case that would have caught #37's own
  bug, and `git grep -l 'SECURITY_BOUNDARY' 52f682c8` returns **one** file,
  `docs/architecture/roadmap.json`, so the docstring's "the path appears once in the whole tree: in
  `roadmap.json` itself" is true at `main`.
* **Brittleness against blocker prose.** Real, and bounded. The predicate depends on the exact phrase
  `only as analysis` surviving in a future blocker edit; if it were reworded, M17's document
  requirement would silently lapse. Mitigation present: case 3 (`test_a_missing_named_deliverable_is_caught`)
  is non-vacuous because it runs the predicate against a `tempfile` fixture roadmap rather than
  against the live one, so the *rule* is tested and not merely the current data. A residual hardening
  option, not a defect: also assert the phrase still matches at least one milestone, so a reworded
  blocker fails loudly instead of quietly.
* **Unintended out-of-scope effects.** Case 4 pins `M19` (`blocked`, deliverable named as an artifact
  to be built later, correctly not demanded) and the DOCUMENT regex cannot match directory-shaped or
  prose deliverables such as `psm/ — registry, …`, so it cannot widen itself into demanding that a
  destination be finished. The new `notes` key in `roadmap.json` is tolerated by the gates — no
  schema field was added and no `state` was touched:
  `git diff 52f682c8..d099492 -- docs/architecture/roadmap.json` is one added line,
  `+      "notes": "The analysis half is published: …"`, and its content was checked against the
  repository and found consistent (13 steps, three paths, three falsifiers, ten interfaces, the
  `make check`-era figures).
* **Negative control, reproduced in isolation here.** §6.3.

### 4.6 Evidence, hashes and the transcript

`evidence/m17-security-boundary-v1/HASHES.txt` is 60 lines: **13 records** covering **8 distinct
paths**, every digest a full 64 hex characters, deliberately double-listing the four documents that
are both added and present in the evidence directory, the base identity of the one modified file
(`docs/architecture/roadmap.json` at `52f682c8`: 50,124 bytes, `433148fe…` — which matches this
clone's `main` byte-for-byte), and prose sections explaining the inherited tracked `__pycache__`
bytecode and why the two historical manifests in that directory fail two entries each on #36's branch.
Run with the file's own recipe:

```
$ awk 'NF==3 && length($3)==64 {print $3"  "$1}' evidence/m17-security-boundary-v1/HASHES.txt | sha256sum -c -
  … 13 lines, all ": OK", 0 FAILED                                        exit 0
$ awk 'NF==3 && length($3)==64' evidence/m17-security-boundary-v1/HASHES.txt | wc -l
13
```

The `length($3)==64` guard in the recipe is not decorative and is not dropping records: measured
directly, `psm`-style short digests are absent — every one of the 13 is already 64 characters — so
the filter is safe here (checked because the same filter *would* silently drop a short digest, and
display truncation from `cut -c1-140` initially suggested two were truncated; they are not).

The transcripts correspond to the final head where it matters, and F5 records the one place where the
labelling is imprecise. Reproduced vs inherited, in one line each:

| Figure in #37 | This review |
|---|---|
| `make check` at head: 933 tests, skipped=109, 165 checks, DOCS 71, CITATIONS 258, PRESENTATION 13 rows | **reproduced** (§6.1), independently, exit 0 |
| `make docs-check` exit 0, `DOCS OK: 71 Markdown files, 34 make targets` | **reproduced** (§6.2) |
| `tests.test_milestone_deliverables`: `Ran 4 tests` / `OK` | **reproduced** (§6.2) |
| `HASHES.txt`: 13 records, 13 OK | **reproduced** (§6.2) |
| `main` baseline: 929 tests, skipped=109, `PASSED: 165 checks`, `DOCS OK: 67`, `CITATIONS OK: 258` | **reproduced** (§6.2) — so the PR's whole test-suite delta is exactly **4** tests and its Markdown delta exactly **4** files |
| negative control at `52f682c8` failing with `M17` named | **reproduced in isolation** (§6.3) |
| GitHub API state of #31/#34/#35/#36/#37, checks, protection | **re-read** (§1) |
| sharpemu / KytyPS5 / RPCSX / MewX READMEs, licences, stars | **re-retrieved from primary sources** (§4.3, F6) |
| nothing | *no figure in this record is inherited from #37's transcript* |

## 5. Checked and not filed

Filed here because a review that lists only its findings hides its near-misses. Twelve candidate
findings were investigated and dropped; the deciding measure is given for each.

| Candidate | Why it is not a finding |
|---|---|
| "`psm/` enumeration at `:328–330` omits `storage.py`" | it lists 14 names and `ls psm/*.py` gives 14 modules plus `__init__.py` |
| "`BUILDING.md:12` says 107 skips, the log says 109" | both numbers are in their own right places; `make check` at the head prints `skipped=109`, `BUILDING.md` describes 107 hardware-gated skips of a different set |
| "`ten interfaces` should be eleven, or nine" | `grep -c 'psm:begin interfaces-PSM' docs/architecture/PS5_PLATFORM_CONTRACT.md` = **10**, names `PSM-AUD CPU GFX IPC IRQ MEM STOR SVC TMR USB`; M10's own deliverable string says ten too |
| "`POST-MERGE-RECONCILIATION-20261122.md` is referenced and missing" | the reference belongs to #36's branch; it is absent from `main` by design |
| "`SECURITY_BOUNDARY.md:449–452` cites a section that does not exist" | §10's cross-references resolve against `PS5_SYSTEM_SOFTWARE_TARGET.md` §6 and `docs/KNOWN_LIMITATIONS.md` |
| "10 `aes\|xts\|rsa` hits in `psm/` contradict F6" | `grep -iE 'aes\|xts\|rsa'` matched the substring inside `con-te-xts`; with `grep -w` there are no cipher names |
| "`§1.1`, `§3.1`, `§3.7` are cited but `grep '^## +N\.'` finds none" | those headings are `### 1.1` / `### 3.1 Analysis runbook` / `### 3.7 Security (M17)`; the first grep pattern was wrong, not the citations |
| "`§5` says RESTRICTED is the only classification…" | no such sentence exists in the file; vocabulary counts in the contract are `PUBLIC` 6 / `INFERRED` 9 / `UNKNOWN` 21 / `RESTRICTED` 2 |
| "`S-SONY-2020` is cited from thin air" | it is defined at `psm/registry.py:73` and used by `C-STO-01` (`PS5_PLATFORM_CONTRACT.md:411`) for 825 GB / 5.5 GB/s; only §9's nine-source list omits naming it, which is a completeness note, not an error |
| "`§7.5`'s claim that payload absence is asserted by tests is soft" | `tests/test_product_identity.py::Ps5PackageTests` asserts the 135-byte pointer's `oid sha256:42ea0e5a…` and `size 1423697408`, its `<1024 B` bound, and walks `docs,boot,kernel,tools,tests,ci` for Sony binaries — `grep -rn 'PS5UPDATE.PUP' tools` finds only the refusal in `tools/firmware.py:219` |
| "entropy figure 4.924 invented" | recomputed here over the tracked pointer file with the repository's own `tools/firmware.py::entropy`: 4.924 — the pointer's, not an image's |
| "the roadmap diff also edits a `state`" | one added line, `"notes"`; `M17` stays `blocked` in both files, and `M19`–`M21`, `M9`, `M10` are untouched |

## 6. Reproduction

All runs performed here, with the exit code each actually returned. `TMPDIR=/tmp` throughout: the
sandbox disallows `mknod`, and several tests create device-shaped temp files.

### 6.1 At the final head

```
$ git worktree add --detach /tmp/r-head d09949226c39052fa04827c2c9b440129735a312   exit 0
$ cd /tmp/r-head && TMPDIR=/tmp make check                                            exit 0
  PASSED: 165 checks, 0 failures
  DOCS OK: 71 Markdown files, 34 make targets, links, anchors and commands resolve
  CITATIONS OK: 258 commit reference(s) resolve across 11 documents
  PRESENTATION OK: 6 figures and 5 blocks current, 13 status rows match roadmap.json, 11 validation record(s) read
  Ran 933 tests in 61.734s
  OK (skipped=109)
```

`CLEAN`/`OK` here means the repository's own gates pass in this sandbox. It is not CI (there is none:
§1), not an approval, and not evidence about PS5 hardware or Sony's system software — a distinction
this PR makes itself and this review does not blur.

### 6.2 Focused runs, and the `main` baseline

```
$ cd /tmp/r-head && TMPDIR=/tmp make docs-check                                  exit 0
$ cd /tmp/r-head && TMPDIR=/tmp python3 -m unittest tests.test_milestone_deliverables -v
      Ran 4 tests in 0.006s / OK                                                 exit 0
$ cd /tmp/r-head && awk 'NF==3 && length($3)==64 {print $3"  "$1}' evidence/m17-security-boundary-v1/HASHES.txt | sha256sum -c -
      13 × ": OK", 0 FAILED                                                      exit 0

$ git worktree add --detach /tmp/r-main 52f682c8435956c8210b3189cad23ebea973d2de  exit 0
$ cd /tmp/r-main && TMPDIR=/tmp make check
      Ran 929 tests in 61.230s / OK (skipped=109) · PASSED: 165 checks · DOCS OK: 67 · CITATIONS OK: 258
                                                                                  exit 0
```

### 6.3 Negative control, in isolation

The test claims it catches the defect that motivated it. Tested by putting **only** the new test file
into a `main` worktree — no other change from the PR — and running it there:

```
$ git worktree add --detach /tmp/r-neg 52f682c8435956c8210b3189cad23ebea973d2de
$ cp /tmp/r-head/tests/test_milestone_deliverables.py /tmp/r-neg/tests/
$ cd /tmp/r-neg && TMPDIR=/tmp python3 -m unittest tests.test_milestone_deliverables
  FAIL: test_every_required_document_is_present (tests.test_milestone_deliverables.MilestoneDocumentTests)
  AssertionError: Lists differ: [('M17', 'docs/playstation/SECURITY_BOUNDARY.md')] != []
  …
  Ran 4 tests in 0.014s
  FAILED (failures=1, errors=1)
                                                                                  exit 1
$ ls /tmp/r-neg/docs/playstation/
  BOOT_FEASIBILITY.md  FIRMWARE_VERSIONS.md  RESEARCH_LOG.md  SYSTEM_FEATURE_PARITY.md
```

Expected failure: the missing-document case must fail at `main`, where `docs/playstation/` holds four
files and the deliverable is absent. Actual: exit **1**, with a diagnostic naming both the milestone
and the path, so the failure is legible without reading the test. The `errors=1` companion is the
module's other case reaching for the same absent file — a second signal of the same cause, not a
second defect. Reverting the copy makes the module pass, which is the other half of the control.

## 7. Limits of this review, and what was not tested

* No hardware, no emulator, no PS5, no firmware payload. Nothing in this record is evidence about
  Sony's system software, and nothing in PR #37 claims to be — `docs/PS5_SYSTEM_SOFTWARE_TARGET.md`
  and `docs/KNOWN_LIMITATIONS.md` keep their states for the same reason.
* Nothing was executed that writes to a device: no USB writing, no `dd`, no `losetup` (the sandbox
  disallows `mknod`), no OVMF, no kernel boot. `make check`'s skipped=109 are those environment-gated
  tests, and they remain skipped here — this review therefore confirms nothing about them.
* Not tested: whether `#37`'s document is *useful* to a future M18 implementer beyond what its §5
  table already says; whether the F3 parenthetical is accurate against Sony's live support pages
  (out of scope: this review will not fetch operational instructions for entering service mode, and
  does not need to, because the finding is about sourcing, not about the verdict).
* `gh api repos/SpicyBadran/PC5/contents/README.md` returning an empty body for another repository
  (RPCSX) briefly made a real quote look unverifiable; the `/readme` endpoint resolved it. Recorded
  because a reviewer without that second shape would have filed a false finding.
* The review read only committed objects plus the remote refs. Files in `/home/user/pc5` were not
  consulted as evidence — deliberately, since that tree carries unrelated work in progress.

## 8. Readiness

**PR #37 is ready for an explicit merge decision.** It is technically sound, self-consistent, its
gate figures reproduce independently at its final head, its evidence manifest verifies with its own
recipe, its test derives from the schema rather than from a copy, and its negative control fails the
way it says it will. Nothing in it weakens the security boundary, touches a production path, or
changes a milestone state; `M17` stays `blocked`, `M18`–`M21` and `M9`/`M10` are untouched.

The six findings are corrections to the document and its transcript, not to its conclusions. F1, F2
and F4 are one-line edits; F5 is two sentences of provenance; F3 needs a source added or a detail
removed; F6 needs a definition stated. In a document whose subject is the discipline of citing what
you measured, a wrong module name and an unresolvable test id are worth fixing before the text
becomes part of `main`, and cheap to fix. This review does not merge, does not approve, and does not
open anything on #37's branch; the proposed text is in `CORRECTION-PROPOSAL-20261122.md`, which is
additive and applies cleanly to `d099492`.

Milestone states, as they stand after this review: `M17` **blocked** (analysis half published),
`M18` **blocked**, `M19`–`M21` untouched, `M9` in progress, `M10` held at in progress. Nothing here
changes that, and no acceptance criterion was weakened.
