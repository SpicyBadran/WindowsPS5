# M17 workstream — scope and dependency assessment, written before implementation

Date: 2026-11-22 (sandbox clock, UTC). Measured in `/home/user/pc5-m17work`, a
`--no-hardlinks` clone of `https://github.com/SpicyBadran/PC5`, `main` checked out at
`52f682c8435956c8210b3189cad23ebea973d2de`, branch `docs/m17-security-boundary-analysis`
created from that commit. **PR #36 was not used as a base**: `git merge-base --is-ancestor
aed099d4 HEAD` fails, and no file from PR #36 is present in this tree (`git log --oneline -1`
above shows the base is the merge of PR #35).

## 1. What M17 is, from the authoritative data

`docs/architecture/roadmap.json` (schema `pc5.roadmap/2`, `updated` `2026-11-16`, 35 milestones)
is treated as authoritative; every field below is read from it, not from prose elsewhere.

| field | value |
|---|---|
| `id` | `M17` — "Security and authenticity boundary" |
| `workstream` | `WS10` ("PS5 platform compatibility (system software)", `serves_level` 4-5) |
| `kind`, `level` | `research`, 5 |
| `state` | `blocked` |
| `depends_on` | `[M10]` |
| `deliverables` | `["docs/playstation/SECURITY_BOUNDARY.md"]` |
| `acceptance` | four items, quoted in §3 below |
| `evidence` | `["docs/playstation/BOOT_FEASIBILITY.md"]` |
| `blocker` | "no lawful trust path is known: the console's boot chain is anchored in Sony-specific silicon and fuses, and PC5 implements no circumvention (ADR-007, ADR-022). Until a lawful path exists this milestone can proceed **only as analysis**" |

The last clause is the licence for this workstream: the blocker forbids the *implementation*
half, and explicitly permits the *analysis* half. It does not permit a state change.

## 2. Dependency and state verification (measured, not assumed)

| claim from the previous session's report | verified how | result |
|---|---|---|
| `M17`–`M19` blocked | field read of `state` | **confirmed**; `M20`, `M21`, `M1b` also `blocked` |
| `M14`, `M15`, `M16` not started | field read | **confirmed** (`not_started`) |
| `M17`'s named deliverable is missing | `ls docs/playstation/` | **confirmed** at `main`: `BOOT_FEASIBILITY.md`, `FIRMWARE_VERSIONS.md`, `RESEARCH_LOG.md`, `SYSTEM_FEATURE_PARITY.md` — no `SECURITY_BOUNDARY.md` |
| `M10`, on which `M17` depends, is `in_progress` not `complete` | field read + `notes` | **confirmed**; `M10`'s acceptance is met but `tests/test_product_identity.py::test_no_milestone_claims_a_level_above_its_evidence` forbids `complete` above level 2 |
| no gate would catch the missing deliverable | `grep -n DELIVERABLES tests/test_architecture.py`; `grep -rn SECURITY_BOUNDARY` repo-wide | **confirmed**: the existence test covers `docs/architecture/` names only; the path appears in exactly one place in the tree — `roadmap.json` itself |

`M17`'s dependencies are therefore satisfied for the analysis half: `M10` is merged and its
contract, registry and conformance suites are in the tree. Nothing in this scope needs `M11`+
(the model milestones), and nothing here needs a payload, a device, or hardware.

## 3. The acceptance items this document must answer, verbatim

From `roadmap.json`, `M17.acceptance`:

1. "every authentication step in the console boot chain is listed with what it depends on and
   whether a PC can lawfully provide it"
2. "what would have to be true for a lawful path is recorded, with falsifiers"
3. "no key handling, decryption, patching or bypass is implemented at any point"
4. "the analysis names which steps a platform model could satisfy and which it cannot"

Item 3 is a property of the whole repository, not of this document, and is re-asserted here with
the measurement that supports it (`tools/` and `kernel/` contain no crypto for Sony formats;
`psm/` has no `security` interface, asserted by `tests/test_psm_registry.py`).

## 4. Vocabulary, reconciled rather than duplicated

The task words source classification as `public documentation | observable behaviour | unknown`;
the repository's contract (`docs/architecture/PS5_PLATFORM_CONTRACT.md` §2) already enforces a
four-marker vocabulary — `PUBLIC | INFERRED | UNKNOWN | RESTRICTED` — with source verification
states `verified | located | not-verified`, and the rule engine rejects anything else. The
deliverable uses the **repository's** markers (they are the ones with a machine-checkable meaning
in this tree) and states the mapping in its §0: `public documentation → PUBLIC` (plus `INFERRED`
where an assumption is needed), `observable behaviour →` what PC5 can measure or read directly in
this environment, recorded with the command, and `unknown → UNKNOWN`, with `RESTRICTED` reserved
for anything whose acquisition would require an act on the refusal list. `RESTRICTED` has no
counterpart in the task's three-way vocabulary; collapsing it into `unknown` would lose the
distinction that matters most here, so it is kept.

## 5. In scope / out of scope

**In scope:** the analysis document `docs/playstation/SECURITY_BOUNDARY.md`; one focused
architecture test that derives named deliverables from `roadmap.json` and fails when a required
one is absent; a `notes` field on `M17` recording that the analysis half is published, with
`state` left at `blocked`; this evidence directory.

**Out of scope, deliberately:** any change to `tools/`, `boot/`, `kernel/`, `psm/` or the USB
code; any `roadmap.json` `state` change, for `M17` or for `M9`/`M10` (their structural acceptance
question is separate and must not be resolved as a side effect here); any edit to
`BOOT_FEASIBILITY.md` or `PS5_SYSTEM_SOFTWARE_TARGET.md` — two inaccuracies found in those
documents are reported as proposed corrections in this directory and in the PR, not silently
applied, because they are dated assessments other records cite; any action against a real device;
any fetch of the LFS payload; any key handling, decryption, signature bypass or trust-anchor
substitution; merging anything.

## 6. Method for the inventory

The step list is derived from `BOOT_FEASIBILITY.md` §1 (the 11-row dependency chain in boot
order), cross-checked against `docs/PS5_SYSTEM_SOFTWARE_TARGET.md` §1/§4/§5 (what the package is
and the clean-installation sequence), `PS5_PLATFORM_CONTRACT.md` §3.7 (the two security claims,
`C-SEC-01` RESTRICTED and `C-SEC-02` UNKNOWN) and ADR-007/ADR-022. Steps that only those sources
name *as requirements* are listed; no step is described by mechanism, because the mechanism is
exactly what is not public. Each row therefore records what must be true and who would perform
it, not how it is implemented — the latter being unknowable from public sources and, for the
security device, refused by `C-SEC-01`.

External evidence is limited to material read or located in this environment on 2026-11-22, with
its verification state recorded per row. Nothing is cited that was not actually retrieved; where
the only thing available is a secondary report, that is said in the row rather than promoted to
`PUBLIC`.
