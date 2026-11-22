# M18 synthetic-package acceptance item — design assessment, 2026-11-22

Task: establish the exact M18 acceptance wording, decide whether the synthetic-package item is
genuinely separable from the rest of M18 and from M17's boundary, and implement the smallest useful
isolated synthetic workflow *if that is justified*. This file is the assessment. **No code is
proposed here and none was written**, because the measurement says the implementation is not yet
safely separable — see §5. The instruction that governed this decision is quoted in §0 so it is
visible to whoever picks the item up next.

## 0. Verdict

| Question | Answer |
|---|---|
| Is item 3 of M18's acceptance separable in principle? | **Yes.** Two repository sources say so, in writing: `docs/PS5_SYSTEM_SOFTWARE_TARGET.md` §6 item 4 (`:179–180`) and `docs/playstation/SECURITY_BOUNDARY.md:440–441` (on `docs/m17-security-boundary-analysis`, not yet on `main`). |
| Is it separable *as an implementation, now, on `main`*? | **No.** There is no loader to exercise: M18's deliverable **is** the loader, and the two seams a load path needs (`PSM-CPU execute_payload`, `PSM-STOR`) are `UNSUPPORTED` by design until `M11`/`M13`, which are `not_started`. |
| Would a test written today satisfy anything? | Nothing that the roadmap can use. It would parse a format PC5 invented for the occasion, against a loader that does not exist, and `tests/test_product_identity.py:276–283` forbids any milestone above level 2 from being `complete` on current evidence, so M18 could not move regardless. |
| Action taken | Design assessment only: §1–§4 record wording, sources, responsibilities and dependency facts; §6 records the design that becomes correct when the preconditions land. No code, no format invented, no roadmap change, no test manufactured. |

> Standing instruction this obeys: *"If not safely separable: stop at a design assessment — no
> superficial test for the sake of progress."* And: *"do not invent a format if a suitable synthetic
> one exists"* — §3 measures that there is no suitable synthetic **package** format in the tree, and
> §4 explains why the synthetic fixtures that do exist are not a substitute.

## 1. The acceptance wording, from the authoritative source

`docs/architecture/roadmap.json` is the authoritative object (it is what
`tests/test_product_identity.py` and `tools/presentation.py` read; the prose documents are rendered
from it). Read at `52f682c8`:

The object in full, exactly as `json.dumps` prints it (so nothing below is paraphrased):

```
$ python3 -c "import json; d=json.load(open('docs/architecture/roadmap.json'));
              print(json.dumps([m for m in d['milestones'] if m['id']=='M18'][0], indent=2))"
{
  "id": "M18",
  "workstream": "WS10",
  "kind": "ps5-compatibility",
  "level": 5,
  "title": "Genuine system-software load",
  "state": "blocked",
  "owner_role": "compatibility-engineer",
  "depends_on": ["M9", "M13", "M17"],
  "advances": "level 5 begins here: the protected input is loaded by PC5's own mechanisms, not by a console",
  "deliverables": ["platform model loader"],
  "acceptance": [
    "a lawfully obtained payload is accepted by the loader and its integrity record matches the recorded hash",
    "the loader refuses a tampered payload and says why",
    "the load path is exercised against a synthetic package PC5 builds itself, so the mechanism is testable without Sony bytes"
  ],
  "evidence": [],
  "blocker": "requires a lawful, authenticated input (the M9 payload is absent from the tree) and the trust analysis of M17; PC5 will not decrypt or circumvent",
  "experimental": true
}

$ python3 -c "… states of the three dependencies …"
  M9 = in_progress     M13 = not_started     M17 = blocked
```

Two structural details of that object matter later. `M18` carries **no `notes` key** — unlike `M17`,
which #37 adds one to — so a note here is a new field to write carefully rather than an edit to
existing prose (and §8 explains why none was written). And its `advances` line already fixes the level
at which any synthetic result sits: "level 5 begins here: the protected input is loaded by **PC5's own
mechanisms**, not by a console". The mechanism under test is PC5's, which is what makes item 3
buildable; the *input's* protected status is what keeps items 1 and 2 blocked.

Three properties of this wording decide everything that follows.

1. **Only item 3 names a PC5-built input.** Items 1 and 2 are about "a lawfully obtained payload"
   and about a *tampered* payload — a tamper is defined relative to an original, and the original is
   the M9 package. Item 3 is the only acceptance line whose subject PC5 can create itself, and it
   says why: "so the mechanism is testable without Sony bytes".
2. **All three items share one verb: *the loader*.** Items 1 and 2 use it ("accepted by the loader",
   "the loader refuses"), and item 3 says "the load path". Item 3 is therefore not an independent
   artefact; it is an *exercise of the same mechanism* on input PC5 owns. An item can be separable in
   its input and inseparable in its subject. That is exactly the case here (§5).
3. **`M18` has no `notes` field and no `evidence` entries.** Nothing in this branch needed to change
   either: the state stays `blocked`, and a note is warranted only when synthetic work *lands* (it
   did not), while editing the criterion would be a weakening (§7).

The dependency wording, kept precise: the payload object belongs to **M9**, whose deliverable string
is `"the repository-root package as a Git LFS pointer only"` — the phrase *"the repository-root
package as a Git LFS pointer only"* appears under M9, not M18. The words "external precondition" do
**not** appear in `roadmap.json`; they are at `docs/TECHNICAL_DECISIONS.md:662` and
`docs/original firmware ps5.md:103`. Attribution of the lawful-input requirement to M18's own
`blocker` string is therefore the only version of the claim that is correct as written.

## 2. Responsibilities: which file owns which half

| Concern | Owner | Evidence |
|---|---|---|
| What the destination may be satisfied by | `docs/architecture/roadmap.json`, `product.levels[5]` + `product.destination.must_not_be_satisfied_by` | level 5 `evidence_class`: "execution evidence produced by the software itself. **Never**: a PC5 kernel booting, a simulated environment, a PlayStation-style interface, or a screenshot of a menu PC5 drew"; level 4's ends "a model running PC5's own payload is not level 5" |
| Whether a level-5 milestone may be marked complete on model evidence | `tests/test_product_identity.py:276–283` | any milestone with `state == "complete"` must have `level <= 2`, else `"{id} is complete at level {level}: only levels 1-2 have evidence"` |
| The refusal boundary, and that M18's synthetic half is buildable now | `docs/playstation/SECURITY_BOUNDARY.md` §10 lead 2 (`:440–441`), on `docs/m17-security-boundary-analysis` @ `d099492` | "*`M18`'s synthetic-package half is buildable now and should not wait* … That is the only part of `M18` that is not blocked, and it **would give the loader a real conformance target** while S13 stays open" — note the conditional: the loader is the absent thing |
| What may be built before the lawful input arrives | `docs/PS5_SYSTEM_SOFTWARE_TARGET.md` §6 item 4 (`:179–180`) | "A loader that validates an input it is given and refuses a tampered one, using a synthetic package PC5 builds itself (`M18`)" — listed under "What PC5 can build before any of that is resolved" |
| Package identity, handling, and what must never be inferred | `docs/FIRMWARE_ANALYSIS.md` §7 (esp. §7.1 `:129–144`, §7.2 `:145–167`) | §7.2 rule 4: "**Structure is reported at the level actually verified.** `tools/firmware.py` identifies `SLB2` and prints the header bytes and printable entry names; it does **not** decode an entry table whose layout has not been confirmed." |
| The two security claims the load path must not pretend to answer | `docs/architecture/PS5_PLATFORM_CONTRACT.md:627–628` (`C-SEC-01` RESTRICTED "not modelled — no PSM interface exists for security state"; `C-SEC-02` UNKNOWN) and `:839–843` | "`M18`–`M21` do not appear above because they consume this contract only through the chain … Nothing in `M18`–`M21` reads a definition that is not already in the table." |
| The interfaces that exist, and that a loader would need | `psm/registry.py` `CLAIMS`, `psm/{cpu,storage}.py`, `psm/audit.py:48` (`EXTRA_INTERFACES`) | ten interfaces (`PSM-AUD CPU GFX IPC IRQ MEM STOR SVC TMR USB`); `psm/registry.py:151` records `conformance="PSM-CPU execute_payload (UNSUPPORTED until M11)"` |
| Existing synthetic fixtures, which are *not* a package format | `tests/test_tools.py`, `tools/firmware.py`, `tests/mbr_fixture.py`, `tools/mkiso.py` | see §4 |
| The USB/media lawfulness rule that stays in force | `docs/KNOWN_LIMITATIONS.md:14`, `:37` | unchanged: never booted from a physical USB stick, so writing media is not deployment-approved |

## 3. Existing format specifications, measured

The task required recording the existing format spec, if any, rather than creating a parallel one.
Measured at `52f682c`:

* **A genuine PS5 package format is *not* specified in this repository, by policy.**
  `docs/FIRMWARE_ANALYSIS.md` §2 describes what a PS5 image is *expected* to be and §7.2 rule 4
  forbids decoding an unconfirmed entry table. `tools/firmware.py` accordingly implements
  identification only: `sha256_file` (`:45`), `entropy` (`:56`), `printable_strings` (`:71`),
  `identify` (`:88`, matching `b"SLB2"` at `:90`), a "SLB2 container" probe whose own note reads
  "header followed by signed/encrypted entries; entry layout is [not confirmed]" (`:143–146`), and
  refusals at `:13`, `:166`, `:219`.
* **PC5's own distributable image format exists but is a *disc image*, not a loadable package.**
  `tools/mkiso.py` writes a boot descriptor tagged `b"PC5BOOT1"` (`:68`, `:219`) and
  `tools/verify_iso.py` checks that magic (`:512`) plus a kernel header prefix `b"PC5K"` (`:545`);
  `docs/INSTALLATION.md` defines the four image targets. This is the medium PC5 boots *its own*
  kernel from — a different chain from the one M18's "load path" names. Reusing `PC5BOOT1` as the
  synthetic "package" would quietly assert that the ISO boot descriptor *is* the platform-model
  loader's input contract, which nothing in the architecture says.
* **There is no `platform model loader` anywhere in the tree.** `ls psm/` gives 15 files
  (`audio, audit, conformance, contract, cpu, graphics, interrupts, memory, psm, registry, render,
  services, storage, usb` and `__init__.py`); nothing is named loader, package, or pup. `grep -rn
  'execute_payload' psm/` finds the op spec at `psm/cpu.py:108` and the `UNSUPPORTED` conformance
  result at `psm/conformance.py:114`. `boot/loader.S`, `boot/mbr.S`, `boot/uefi/bootx64.S` are PC5's
  x86 boot loaders for its own kernel — the same word, a different subsystem, and citing them as
  "the M18 loader" would be a category error of precisely the kind `SECURITY_BOUNDARY.md` §4 warns
  about.
* **A synthetic *package* format would therefore be new**, and `psm/audit.py:48 EXTRA_INTERFACES` is
  the only sanctioned place for a new interface to be reported — with the consequence that a
  synthetic "load" interface becomes a census item that the contract currently says must not exist
  (`PS5_PLATFORM_CONTRACT.md:839–843`) and that #37's new `tests/test_milestone_deliverables.py` and
  the existing contract tests keep count of (ten).

## 4. What a synthetic test could and could not establish

**Could**, if the loader existed:

1. that a loader's validation is *mechanical and deterministic* — identical inputs produce an
   identical accept/refuse decision and an identical integrity record, which is the property the
   roadmap's evidence rule needs for a third party to repeat an attempt;
2. that refusals carry a reason (`tools/pc5ctl.py` already refuses in words; the loader's "says why"
   in item 2 is the same discipline), and that the refusal vocabulary distinguishes *denied* from
   *unsupported* (`PS5_PLATFORM_CONTRACT.md:664`, ADR-007) rather than collapsing both into "no";
3. that malformed input is rejected **without writing anywhere** outside the test workspace —
   the strongest single item on this list, because it is a safety property of the code path, not a
   claim about the console;
4. that the negative controls detect each defect — the pattern the repository already trusts
   (`tests/test_psm_registry.py:89 RuleEngineTest`, "A rule that cannot fail is not a rule").

**Could not**, and this is why a test now would be theatre:

1. **it could not exercise the load path**, because the load path is the thing M18 exists to build;
   a parser written alongside its own fixture tests the parser, not the path, and would have to be
   rewritten the moment `M11` provides `execute_payload`;
2. **it could not say anything about authentication** — `C-SEC-01` is `RESTRICTED` and "not modelled:
   no PSM interface exists for security state"; a synthetic container with a fake signature field
   would *imitate* a Sony authentication structure, which is prohibited outright (the task's own
   Phase-3 constraint; `docs/FIRMWARE_ANALYSIS.md` §7.2 rule 4; `SECURITY_BOUNDARY.md` §6 item 3);
3. **it could not be called a package the console would accept, nor be given a `.PUP` name**, and
   every label on it would have to carry `PC5 synthetic / test-only` — the confusion risk is the
   reason the design in §6 keeps the artefact inside `tests/` and out of the four
   `docs/INSTALLATION.md` image targets;
4. **it could not complete M18**, which fails on items 1 and 2 (no lawful payload) and is barred by
   `tests/test_product_identity.py:276–283` from claiming `complete` at level 5 in any case;
5. **it could not substitute for M1–M3 hardware validation** — a synthetic parse is evidence about
   code PC5 wrote, i.e. level 1–2 material, and level 4's evidence class explicitly excludes "a model
   running PC5's own payload".

## 5. Why the safe answer is to stop here — four measured blockers

| # | Blocker | Measurement |
|---|---|---|
| B1 | The subject of item 3 does not exist. "The load path is exercised" has no referent until `platform model loader` is built, and building it *is* M18's deliverable, not a test of it. | `ls psm/ tools/` — no loader/package module; `roadmap.json` M18 `deliverables == ["platform model loader"]`; `docs/PS5_SYSTEM_SOFTWARE_TARGET.md:179` phrases it as future work ("A loader that validates…"), as does `SECURITY_BOUNDARY.md:441` ("it would give the loader a real conformance target") |
| B2 | The execution seam is withheld until M11. `PSM-CPU execute_payload` is `UNSUPPORTED` by design, and `M11` is `not_started`. | `psm/cpu.py:108` (`OpSpec execute_payload`), `psm/conformance.py:114` (`Status.UNSUPPORTED`), `psm/registry.py:151` ("`execute_payload` (UNSUPPORTED until M11)"), `PS5_PLATFORM_CONTRACT.md:833` ("the execution model itself; `execute_payload` is `UNSUPPORTED` until then"), roadmap `M11.state = not_started` |
| B3 | There is no place to load *from* inside the model. `PSM-STOR` is an M13 test double whose `decompress` and `guest_layout` ops return `UNSUPPORTED` because the on-disk layout is `UNKNOWN` and is M21's work. | `psm/storage.py:71–87` (both op specs, `unsupported=True`, invariants "returns UNSUPPORTED: the block's programming interface is UNKNOWN" / "the layout is UNKNOWN and is M21 work"); roadmap `M13.state = not_started` |
| B4 | A synthetic package format cannot be shaped like the genuine one, and if it is not, it needs a loader contract that the contract deliberately does not define. `psm/` has no security interface, `M18`–`M21` "consume this contract only through the chain", and `SECURITY_BOUNDARY.md` §2's rule is that where no source names a mechanism, the mechanism column does not exist. | `PS5_PLATFORM_CONTRACT.md:627–628`, `:839–843`; `grep -rn 'PSM-SEC' psm/*.py` → 0 hits; `test -f psm/security.py` → absent; `docs/FIRMWARE_ANALYSIS.md` §7.2 rule 4 |

B1–B3 are ordering facts, not opinions: they say *when* this becomes buildable. B4 is the
boundary fact: it says *what must not be improvised* when it is built. Together they mean the item
is separable from the lawful-input half (the input can be PC5's own) but **not** separable from M11
and M13, which are what give "load" a meaning inside the model. Proceeding now would mean
manufacturing that meaning — the "superficial test for the sake of progress" the task forbids.

## 6. The design to implement when B1–B3 clear (recorded so it is not re-derived)

Smallest useful shape, entirely test-only, no new production module:

1. **Where it lives.** A `tests/synthetic_package.py` fixture builder plus
   `tests/test_synthetic_package_loader.py`, using `unittest` only. Nothing under `tools/`, `boot/`,
   `kernel/`, `psm/` — and nothing wired into the genuine intake, which stays
   `tools/firmware.py`'s identification-only path with its refusals at `:13`, `:166`, `:219`.
   Precedent for a fixture module that builds binary structures in-test: `tests/mbr_fixture.py`.
2. **What the format is.** The loader's own container contract, as defined by `platform model
   loader` once it exists — i.e. the fixture *consumes the shipped format*, it does not create one.
   If and only if the shipped loader has no test-only input mode, add one documented entry point on
   the loader (the "safe isolated test interface" the architecture allows), and record in the same
   commit why the genuine path is unaffected.
3. **How it cannot be mistaken for a genuine target package.** Magic and header chosen by the loader
   for PC5 and asserted *different* from `SLB2`; no field named or shaped like a signature,
   certificate, Merkle root or key id; every generated artefact labelled in its first bytes with a
   `PC5-SYNTHETIC` style marker defined only under `tests/`; no `.PUP` extension; the module
   docstring states the milestone, that the payload is PC5-authored, and the sentence "this is not a
   PlayStation 5 package and proves nothing about one".
4. **Positive cases.** Deterministic generation (build twice from the same inputs, assert byte
   identity and one recorded SHA-256, checked against the tool's own `sha256_file`/`entropy`); valid
   parse; validate-accept; the refusal of an unsupported version *naming the version it saw*.
5. **Negative controls, each proving the test detects the defect** — exact command, expected failure,
   actual exit code, and the diagnostic, in the style already used by
   `tests/test_psm_registry.py::RuleEngineTest`: truncation at each structural boundary; bad magic;
   bad version; declared length inconsistent with the buffer; internal offsets pointing outside;
   length/offset arithmetic that would overflow (including huge declared sizes, to catch unreasonable
   pre-allocation — assert the refusal happens *before* allocation, by bounding memory or by a
   refused-on-parse path); missing, duplicated and contradictory metadata entries; tampered payload
   with intact metadata and vice versa; unexpected trailing bytes; an unsupported feature bit set;
   malformed input rejected with no file created outside the temp dir (assert on the directory
   listing, not on the exit code alone).
6. **Integrity mechanism, if any, must be test-only integrity, not authentication.** A plain SHA-256
   over the whole artefact is the maximum: `hashlib.sha256` is already the only cryptographic-adjacent
   import in `tools/`, `psm/`, `kernel/` (10 files under `tools/`, and `grep` finds no cipher, MAC,
   KDF, signature or TLS import anywhere in the three directories). No HMAC with a key constant, no
   keyring, no "verify signature" verb, no asymmetric anything.
7. **Evidence rule.** Report results as level 1–2 material about PC5 code. The milestone line in
   `roadmap.json` keeps `state: blocked`; at most an accurate `notes` sentence is added when code
   lands (states already in the file for M17, e.g. `roadmap.json:1209`, are the model to copy), and
   `evidence` stays empty until a real payload exists. Never reword items 1 or 2, and never widen
   "the mechanism is testable without Sony bytes" into "the mechanism is satisfied".

## 7. Commands run for this assessment, with real exit codes

All executed at `52f682c8435956c8210b3189cad23ebea973d2de` (verified `main`) in a clean clone of it;
`TMPDIR=/tmp` throughout.

```
$ git rev-parse HEAD                                                        52f682c8…  exit 0
$ python3 -c "…M18 from roadmap.json…"   state=blocked level=5 depends_on=[M9,M13,M17]
  deliverables=['platform model loader'] evidence=[]  notes absent; M9=in_progress M13=not_started M17=blocked
$ grep -rn 'execute_payload' psm/            3 hits: cpu.py:108, conformance.py:114, registry.py:151   exit 0
$ sed -n '71,87p' psm/storage.py             decompress + guest_layout, unsupported=True               exit 0
$ ls psm/*.py | wc -l                        15 (14 modules + __init__)                                 exit 0
$ grep -c 'psm:begin interfaces-PSM' docs/architecture/PS5_PLATFORM_CONTRACT.md   10                     exit 0
$ grep -rn 'PSM-SEC' psm/*.py | wc -l        0                                                            exit 0
$ grep -n 'def sha256_file|entropy|identify' tools/firmware.py   45 / 56 / 88                            exit 0
$ grep -n 'PC5BOOT1\|PC5K' tools/mkiso.py tools/verify_iso.py     68, 219, 512, 545                      exit 0
$ sed -n '276,283p' tests/test_product_identity.py   level<=2 rule for complete milestones               exit 0
$ grep -n 'synthetic package PC5 builds itself' docs/PS5_SYSTEM_SOFTWARE_TARGET.md docs/playstation/*   1 file on main
$ git diff --name-only 52f682c84359 HEAD   ->  evidence/m18-synthetic-package-v1/ … (this directory only)
$ git diff --name-only 52f682c84359 HEAD -- tools boot kernel psm src firmware ci   ->  empty            exit 0
$ TMPDIR=/tmp make docs-check          DOCS OK: 68 Markdown files, 34 make targets   exit 0
$ TMPDIR=/tmp make check
    PASSED: 165 checks, 0 failures · DOCS OK: 68 · CITATIONS OK: 258 · PRESENTATION OK (13 status rows)
    Ran 929 tests in 61.838s · OK (skipped=109)                                      exit 0
```

The suite count is **929**, identical to `main` at `52f682c8` — measured here, and equal to the
baseline the review record reports for the same revision. That is the point: this branch adds a
document and no test, so it must not, and does not, change what the repository checks. `DOCS OK`
moves 67 → 68 for the one file added here.

## 8. What was *not* done, and the limits of this record

* No code, no test, no fixture, no format file, no `psm/` or `tools/` change, no roadmap edit.
  Deliberate: §5. The tree this branch touches contains exactly this directory.
* The gates in §7 were run to show that adding this document disturbs nothing — the suite count is
  unchanged at 929 and `make check` exits 0 — **not** to certify an implementation, because there is
  none to certify. They say nothing about M18. Figures for PR #37's head (933 tests, `DOCS OK: 71`)
  live on `docs/pr37-independent-review` in
  `evidence/pr37-independent-review-v1/PR37-INDEPENDENT-REVIEW-20261122.md` §6, another branch; they
  must not be read as runs of this one.
* The blockers B1–B3 are statements about `main` at `52f682c8`. If a loader lands from another
  workstream, §6's item 2 changes from "consume the shipped format" to a concrete fixture list and
  this assessment should be re-run against it; the §5 boundary facts (B4) are not time-dependent.
* Nothing here is evidence about Sony's system software, and no claim in this file should be reused
  as a statement that any part of M18, M17 or M19 has been satisfied. M17 remains `blocked`; M18
  remains `blocked`; M19–M21, M9 and M10 were not touched.
