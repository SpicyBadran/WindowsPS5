# Post-merge reconciliation — 2026-11-22, follow-up to PR #35

Prepared on branch `docs/usb-post-merge-reconciliation`, forked from `main` at
`52f682c8435956c8210b3189cad23ebea973d2de`. Scope: documentation status, install
guidance, one hygiene defect in the evidence package, and a file-count reconciliation.
**No production line of `tools/pc5ctl.py` is touched** — there is no reproduced
production defect to justify one, and the merged remediation is not re-derived here.

## 1. The merged state, recorded before anything was edited

    main HEAD (and this branch's base)   52f682c8435956c8210b3189cad23ebea973d2de
    commit subject                       Merge pull request #35 from SpicyBadran/fix/usb-descriptor-bound-remediation
    commit date                          2026-11-21 22:08:47 +0200  (20:08:47Z author-side clock: mergedAt 2026-11-21T20:08:48Z)
    PR #35                               state MERGED, isDraft false, base main, head fix/usb-descriptor-bound-remediation
    PR #35 head                          80fc8615283173fd820d26c5779ad0cb94047736
    PR #35 commits                       4
    PR #35 diff                          111 changed files, +57,469 / -39
    merged by                            SpicyBadran (repo owner), method `gh pr merge 35 --merge`
    PR #31                               OPEN at ac17c5d3afa6fa3ca779c012c6aef36b64751b55, base main, not draft — untouched
    PR #34                               OPEN at 547ebd5cff04b87330d95807a90795d9ac4d66d0, base main, not draft — untouched

Session workspace at capture (`/home/user/pc5`, the state the user's work lives in):
branch `arena/c8a76776-pc5` at `56c58521580e88c4339ceb6eb40ce724a2bb533b`; 11 tracked
modifications; 290 untracked files; 0 staged; 0 stash entries; recovery bundles,
`dropbox/` records and every `evidence/` subdirectory left in place. Two facts about it
are recorded because they matter to reproducibility, not as findings:

* the workspace's contents equal the merged tree for the 103 files of PR #35's first
  commit plus the uncommitted dated notes; nothing needed to be re-applied, which is why
  this follow-up was authored in a fresh clone of `main` rather than by patching the
  workspace;
* the fetch that made `52f682c` reachable in that workspace was
  `git fetch --unshallow origin` — the repository is **no longer shallow**
  (`git rev-parse --is-shallow-repository` → `false`, was `true`). That adds objects; it
  rewrites no ref and no history, and it is disclosed because `30-fresh-clone-verification.txt`
  depends on the shallow state for its explanation.

## 2. Identities of the merged implementation, tests, docs and evidence

Hashed from `git show 52f682c…:<path>` — main's committed blobs, not a working copy — so
these numbers are true of `main` whatever any tree on disk happens to contain:

```
tools/pc5ctl.py 37127 78cb062df6df02f5a335207808bbe60708b65276ac43ae4703421f8ad5a94447
README.md 29379 cab91bdfe8af57436682679a53d0c5fac8d20b9f12e1918b5f00aea92d77d687
docs/INSTALLATION.md 9493 d9dcd22502bcfffb577e7267ab0fce4069cc49c770f83a0418b59d1043eaf814
docs/BUILDING.md 11049 7b6bd55056fdc41f8a41bfdcf7d793f6db02a46e469166fb5115fa5a70b5a63e
Makefile 20927 b9be9c2d4532ac7f3fc39c9a01c79e4d842987e2135477c05bf54bfa60b86c2e
requirements-harness.txt 15 56bce36af734e3b9aeff2be4301bbc2a2c2b58ea1ea1e6ee6e792db84f96fbd4
tools/citation_refs.sh 2934 89afcff0982cb3a6c7cfa597a1a5e0167fe9337595d162ccbb45a71f87adca3a
tests/test_pc5ctl_usb_safety.py 49004 11879172c53b192e198382d76841f51ea0694c1c2e1074d62759764b54ea3c80
tests/test_pc5ctl_usb_descriptor_identity.py 32006 1a0955e17f6ef9977e511525206a00d9bb1c01d8621565e0b731baba505754d9
tests/test_pc5ctl_usb_cli_boundaries.py 6977 8efb0525a7cf1c76d4a113b0a1585180f622a4c1e83c90c1e78615c590d2ad00
tests/test_pc5ctl_usb_topology_unknown.py 7300 7337623e097ab04e5147ab5974748037002631a48b222ec3c9fa5d02f699821a
evidence/usb-descriptor-remediation-v1/mutation_harness.py 11250 2b597f4e59bf4ac591be822f49583e4d19e66ca44ef40f20db1a8b47c3558742
evidence/usb-descriptor-remediation-v1/REMEDIATION.patch 55331 19793a838870913b3afa59e84994bdf1032ad5248d09b0a5192eac6c8a499dac
evidence/usb-descriptor-remediation-v1/HASHES.txt 30878 37cf9de4482319e901c60cf78a3e2f88ad5647bda149f3ed0a7c22c86607a24d
evidence/usb-descriptor-remediation-v2/mutation_harness_v2.py 10803 bf4a61b850329abbc80ad5b9626c26d6fa63a058495f539d0bed846fd1029237
evidence/usb-descriptor-remediation-v2/HASHES-PR-TIP.txt 16427 80f3c26190cb66c4a2815fb611411db86f93fbcf31fff775bcbf87c661f27313
evidence/usb-descriptor-remediation-v2/CORRECTED-MANIFEST.txt 22410 58c2ca6f940e351e037ac6514c56753e069433d5cb69c0ada3126ef3b7675c71
evidence/usb-descriptor-remediation-v2/FINDINGS-DISPOSITION-20261121.md 8504 d81a7e792474a3441ca39f4ae56f12c031fdcde69b7db256d4312d57e10268e7
evidence/usb-descriptor-remediation-v2/USB-REMEDIATION-v2.patch 100588 e1dae862d0d01af8674243f4e77a000f04f051f598405f506c6bcd539f234002
evidence/usb-descriptor-remediation-v2/USB-PR-35.patch 2560207 2b3cefb81583168647c2206a68ed10078c7118907bff123b1c055f20b7ab3b10
evidence/usb-descriptor-independent-review-v1/INDEPENDENT-REVIEW-20261121.md 23206 981d71b95bc330a9ed90196a503262dcd7a1a2985bb1ce681d41297102fdb502
docs/engineering/USB-IDENTITY-BOUNDARY-DESIGN-v1.md 15437 fafa850662e69604c6b8c84abb07f03ccc248f216f89c08345d390c8678ae4c2```

Directories as carried by `main`: `evidence/usb-descriptor-remediation-v1/` 21 files
424,673 B; `evidence/usb-descriptor-remediation-v2/` 51 files 3,915,310 B;
`evidence/usb-descriptor-independent-review-v1/` 21 files 641,943 B. The v2 count includes
one file that should never have been committed, §4.

## 3. The 111-vs-103 file count, reconciled

GitHub is right, the completion note was measuring something else, and both numbers are
derivable from the same four commits:

| commit | touched by the commit | cumulative delta vs `56c5852` |
|---|---|---|
| `3715247` implementation + evidence | 103 | **103** |
| `589dc32` PR-open record + manifests | 7 | 107 |
| `20593d5` manifest regeneration | 2 | 107 (both files already counted) |
| `80fc861` F-6 test + logs | 12 | **111** |

`103` is the delta of PR #35's **first** commit, measured at 19:57Z when the report was
written; `111` is the union of all four commits, which is what a PR's Files tab shows. The
check that distinguishes the two is not `git diff base..head` on whatever is checked out
but the per-commit arithmetic above, which is exact:

    $ B=56c58521580e88c4339ceb6eb40ce724a2bb533b
    $ for c in 3715247 589dc32 20593d5 80fc861; do echo "$c $(git diff --name-only $B $c | wc -l)"; done
    3715247 103
    589dc32 107
    20593d5 107
    80fc861 111
    $ git log --format= --name-only $B..80fc861 | grep . | sort -u | wc -l
    111                                        # union == final delta: no file was added and then removed

The number appeared in two committed places — `logs/30-fresh-clone-verification.txt:4` and
its copy inside `USB-PR-35.patch` — and in the completion report. **Both historical records
are left exactly as they were**, per the standing rule that a superseded measurement is
annotated rather than corrected in place; this section is the annotation. The wording was
also, in its own defence, narrow: it said "in the branch delta" at the moment it was
written, which is true — it just was not the whole PR.

Of the 111, one file is not evidence and not source. §4.

## 4. The committed `.pyc`, and how an ignored path got in

    evidence/usb-descriptor-remediation-v2/__pycache__/mutation_harness_v2.cpython-311.pyc   13,725 B   sha256 2d2362362c87d7fb1b19fcdb517e061ca9a2cfca07fdbe590fdeb6f6f4570235
    blob     ef603eaf7e75d2d601a7dadcba2b5d3a4ee23fcc      (still in history; `git cat-file` reads it)

Necessary? No. It is CPython's compiled cache of the tracked
`evidence/usb-descriptor-remediation-v2/mutation_harness_v2.py`: `marshal` of a fresh
`compile()` of that source is **byte-identical to the tracked file's code section**
(measured in the pre-remediation tree, `True`), while a second `py_compile` run produces a
different file overall (13,725 B, `eb8f49b6…`) because the header carries the source
timestamp. So it encodes no information the source lacks and cannot be re-derived byte for
byte by anyone else — the worst possible combination for a directory whose whole purpose is
re-hashable evidence.

How, given that `.gitignore` has carried `__pycache__/` and `*.pyc` (lines 17-18) the entire
time: the staging command for the F-6 commit was

    git add -A tests README.md … evidence/usb-descriptor-remediation-v2      # ignored, skipped
    git add -f tests/… tests/test_pc5ctl_usb_topology_unknown.py evidence/usb-descriptor-remediation-v2/

and `-f` **on a directory** means "add everything inside, ignore rules notwithstanding" —
which was needed for the dated notes in that directory and was therefore aimed at the
directory rather than the files. The fix is not to regret `-f` (the evidence files it
retrieves are the point) but to stop letting it operate on a directory whose contents are
what a test run also writes.

Resolution in this branch:

* `git rm --cached` on the path — the blob stays in history, so no evidence is destroyed
  and no manifest's claim about a past tree can be falsified by its absence;
* a real guard, `tests/test_repository_hygiene.py` (3 cases): no tracked path is bytecode,
  `.gitignore` still carries both patterns, and the predicate is pinned against names it
  must catch and names it must not, so the check cannot pass by never matching. It is
  `skipUnless`-guarded on being inside a Git repository: an export has no index to read,
  and a skip says so where a vacuous pass would not.
  Negative control, run in a scratch clone: force-adding a dummy `.pyc` gives
  `Ran 3 … FAILED (failures=1)` with the path named; removing it gives `OK`.

Manifest effect: **none**, measured rather than assumed —

    $ grep -c 'pycache' evidence/usb-descriptor-remediation-v2/HASHES-PR-TIP.txt \
                        evidence/usb-descriptor-remediation-v2/CORRECTED-MANIFEST.txt \
                        evidence/usb-descriptor-remediation-v1/HASHES.txt
    0
    0
    0

so no historical manifest is regenerated for this, and none needed to be. `HASHES-PR-TIP.txt`
did claim to cover the whole branch delta, and for one file it did not — that claim is
restored by the removal rather than retro-actively edited.

## 5. Documentation changes in this branch

* `docs/engineering/USB-IDENTITY-BOUNDARY-DESIGN-v1.md` — new §8 "Current status, recorded
  after the merge", plus the two status statements (§header, §6) marked as *as authored* and
  pointed at §8. §1–§7 are unedited. §8 says plainly: implemented and merged in PR #35 at
  `52f682c…`; independently reviewed, with the review and the disposition records in-tree;
  95 tests and three mutation harnesses are **documented evidence, not physical-device
  validation**; F-8 and F-9 remain open with their existing reasons; physical validation has
  not occurred; USB deployment stays blocked pending validation and explicit authorisation.
* `docs/INSTALLATION.md` §2 — the instruction `# check the device path twice, then:` is
  replaced. It was not merely useless, it was the wrong mental model: re-inspecting a
  *pathname* is exactly the operation that cannot be made safe, which is what the
  remediation removed. In its place: the authoritative decision is taken on the open
  descriptor (`fstat` → `major:minor` → `/sys/dev/block`) and that same descriptor is what
  `dd` receives, so no rename between looks can redirect the write; `--yes` records intent
  and cannot override a refusal; what a human is still uniquely able to decide is *which*
  stick. Test count reconciled with the README (91 → 95), the harnesses named as evidence
  about code rather than hardware, and the not-validated / not-deployment-approved warning
  kept and linked to §7–§8.

## 6. Verification, in this clone (`/home/user/pc5-reconcile`, a clone of GitHub `main`)

    $ TMPDIR=/tmp make docs-check                                       exit 0
    DOCS OK: 68 Markdown files, 34 make targets, links, anchors and commands resolve
    $ TMPDIR=/tmp make check                                            exit 0
    PASSED: 165 checks, 0 failures · PSM conformance: 261/261
    DOCS OK: 68 · CITATIONS OK: 258 commit reference(s) across 11 documents
    PRESENTATION OK · BRAND OK
    Ran 932 tests in 61.614s
    OK (skipped=109)
    $ TMPDIR=/tmp python3 -m unittest discover -s tests -p 'test_pc5ctl_usb*.py'
    Ran 95 tests in 0.217s
    OK                                                                  exit 0
    $ TMPDIR=/tmp python3 evidence/usb-descriptor-remediation-v2/mutation_harness_v2.py
    collected inventory: 95 test methods
    RESULT: PASS: baseline green, every mutant caught, and every intended test both present and discriminating
    $ TMPDIR=/tmp python3 evidence/usb-descriptor-remediation-v1/mutation_harness.py
    RESULT: PASS: baseline green and every mutation detected by its intended assertion

`Ran 932` = `929` (as merged) + the 3 hygiene cases. `DOCS OK: 68` is 67 (`main`) plus this
record; `make docs-check` was run once at 67 before it existed and once at 68 after, and the
figures above are the later run, captured 2026-11-21T23:31:30Z. `skipped=109` because this clone has
no `unicorn` installed — the documented unprovisioned shape; the provisioned workspace run is
`929 … OK (skipped=2)`. **No CI success is claimed here:** what GitHub Actions did or did not
run for the follow-up PR is recorded in that PR's own comments (out-of-band, so this file
cannot describe a result that postdates it), and `gh pr checks` reporting nothing is recorded
as nothing rather than as green.

Manifest verification, from the repository root as each manifest's own header directs:

    HASHES.txt (v1, historical)              unchanged, still describes what it described
    HASHES-v2.txt (review package)           20 records, 20 OK
    HASHES-PR-TIP.txt                        109 records, 107 OK, 2 FAILED
    CORRECTED-MANIFEST.txt                   108 records, 106 OK, 2 FAILED

The 2 failures are the same two files in both, and they are *this branch's* edits:
`docs/INSTALLATION.md` (`9,493 B d9dcd225…` → new) and
`docs/engineering/USB-IDENTITY-BOUNDARY-DESIGN-v1.md` (`15,437 B fafa8506…` → new). A
manifest of a past tip that silently kept claiming success after its subject changed would
be the F-2 error again, so both are reported here, with the old and new identities in
`HASHES-FOLLOWUP.txt`, and neither historical manifest is rewritten.

## 7. What this branch does not do

It does not touch PR #31, PR #34 or any M2a kernel work; it does not amend the merged
production code; it does not close F-8 or F-9, and it does not move the USB milestone:
physical-device validation still has not occurred, and **writing an image to media remains
not deployment-approved**.

*Recorded 2026-11-21T23:27:42Z. No device node exists in this environment, `mknod` is denied, and no
destructive call was made or possible.*

## 8. Destination roadmap: verified state, and what is actually startable

Checked against `docs/architecture/roadmap.json` in this clone — its `updated` field is
`2026-11-16`, schema `pc5.roadmap/2`, 35 milestones — and against the two documents that
govern the destination: `docs/playstation/BOOT_FEASIBILITY.md` (124 lines) and
`docs/PS5_SYSTEM_SOFTWARE_TARGET.md` (212 lines). Nothing below is inferred from the roadmap's
prose; each claim is a field of the JSON or a line of a test.

| claim | verdict | measurement |
|---|---|---|
| `M14` not started | **confirmed** | `"state": "not_started"`, `depends_on: [M13, M7]` |
| `M15` not started | **confirmed** | `not_started`, `depends_on: [M13]` |
| `M16` not started | **confirmed** | `not_started`, `depends_on: [M12, M3]` |
| `M17`–`M19` blocked | **confirmed** | `blocked` each; blockers quoted below; `M20`, `M21` blocked too |

Full census: `complete` 9 (`M0`, `M1a`, `M1c`–`M1i`), `in_progress` 2 (`M9`, `M10`),
`not_started` 18, `blocked` 6 (`M1b`, `M17`, `M18`, `M19`, `M20`, `M21`).

**Why `M9` and `M10` stay `in_progress` although their acceptance reads as met.** The gate is
`tests/test_product_identity.py::test_no_milestone_claims_a_level_above_its_evidence`:

> `f"{m['id']} is complete at level {m['level']}: only levels 1-2 have evidence"`

A milestone above level 2 cannot be marked `complete` at all while that rule stands — it is what
keeps `M1` honest, and `M10`'s own `notes` field says so. So "finish `M9`/`M10`" is not
achievable work: they are substantively accepted and structurally held. The repository already
enforces the substance: `test_the_file_in_the_tree_is_a_pointer_not_a_payload`,
`test_the_declared_size_is_recorded_in_the_documents` and `test_nothing_in_the_tree_is_a_sony_binary`
assert the `M9` acceptance items about the LFS pointer
(`42ea0e5a…063fb`, 1,423,697,408 B) and the payload's absence.

**Dependency reachability, measured on the graph.** `M11` depends on `M2`, `M3`, `M10`; `M2` and
`M3` depend on `M1` and `M2a`/`M2b`, and `M1`'s acceptance is a physical boot on qualified hardware
with a `tools/hw_record.py` record. So `M11`→`M16` are not startable here: their unmet
dependencies are hardware-validated layers, not documents. `M18` additionally needs a lawful,
authenticated input; `M19` needs `M14`–`M16` + `M18`.

**The one startable gap, and it is `M17`'s analysis half.** `M17`'s blocker is explicit that it
"can proceed only as analysis", and its deliverable is
`docs/playstation/SECURITY_BOUNDARY.md` — a path that **does not exist** (`ls`:
`docs/playstation/` holds `BOOT_FEASIBILITY.md`, `FIRMWARE_VERSIONS.md`, `RESEARCH_LOG.md`,
`SYSTEM_FEATURE_PARITY.md`). Its four acceptance items are answerable from work already in the
tree: `BOOT_FEASIBILITY.md` §2 classifies dependencies into six classes, §3 lists the four
"would have to be true" paths, §4 lists three falsifiers ("None has been observed"), and ADR-007
/ ADR-022 fix the lawfulness boundary. No gate catches the missing file:
`tests/test_architecture.py` checks deliverable existence for `docs/architecture/` names only
(`test_deliverables_exist_and_are_substantive`), and no test references that path — which is why
an in-progress analysis milestone can carry an unwritten deliverable unnoticed.

**Where this remediation sits in the graph.** The descriptor-bound write tool appears in **no**
milestone's deliverables or acceptance: `usb` in the JSON reaches `M2d` (kernel xHCI/HID/DualSense
input path, `not_started`) and `M15` (PS5 USB *device model*, `not_started`) — different layers
from a host-side imaging tool. What the tool serves is `M1`, whose acceptance includes "an
installation writes a bootable target" and whose four deliverables (`docs/evidence/`,
`docs/HARDWARE_COMPATIBILITY.md`, `docs/hardware/M1_PHYSICAL_BOOT_PROCEDURE.md`,
`tools/hw_record.py`) all already exist — what `M1` lacks is a machine. So:

* the remediation advances **no milestone**, and §8 of the design document says the same about
  deployment approval;
* what it *did* produce is a validated-safe write path, which is a **prerequisite** for `M1`'s
  write step and for any physical validation of it;
* the evidence class of every item in §6 is **synthetic / documented**, not emulator-backed and
  not hardware-backed: `make check` here runs `unicorn`-free (109 skips), and no device node was
  ever created in this sandbox (`mknod` denied, `/dev/` clean).

**Smallest concrete next PR I would accept, with measurable criteria** — write
`docs/playstation/SECURITY_BOUNDARY.md` as the `M17` analysis deliverable, changing no code:

1. every authentication step in the console boot chain listed, each row carrying what it depends
   on and whether a PC can lawfully provide it, and a source class of
   `public documentation | observable behaviour | unknown` — the `M10` rule, "none is invented";
2. the four "would have to be true" paths of `BOOT_FEASIBILITY.md` §3 restated with their
   falsifiers, and the three falsifiers of §4 recorded as *not observed as of 2026-11-22*;
3. an explicit statement, one row per step, of which steps a platform model could satisfy and
   which it cannot — that is `M17`'s fourth acceptance item, and it is what `M18`'s loader design
   would consume;
4. `M17` stays `blocked` in `roadmap.json`; only its `notes` gains "analysis published, blocker
   unchanged" — the `M10` discipline, not a state bump;
5. a test in `tests/test_architecture.py`-style coverage asserting that every milestone
   `deliverables` entry in `WS10` names a file that exists when the milestone is
   `in_progress`/`blocked`-with-analysis — so a named deliverable cannot silently stay unwritten;
6. gates green from a fresh clone: `make docs-check`, `make check`, and the new test's own
   negative control (delete the file, watch it fail).

Two things this does **not** need and must not smuggle in: any key handling, decryption or
authentication bypass (ADR-022 boundary, and item 5 of `M9`'s acceptance forbids even *planning*
it here); and any claim that writing the analysis moves `M17` toward `complete`.

**Separately, three items are waiting on the author, not on engineering:** `M1b` CI needs a
token with the `workflows` scope so `ci/build.yml` can exist (measured:
`gh api repos/SpicyBadran/PC5/actions/workflows` → `{"total_count":0}`); `M1` needs a qualified
machine booted from USB; and physical validation of this write path needs explicit authorisation
to write a real stick.
