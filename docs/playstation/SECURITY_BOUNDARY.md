# The security and authenticity boundary

**Milestone:** `M17` — "Security and authenticity boundary" (`docs/architecture/roadmap.json`).
**Status of this document: the published analysis half of `M17`.** `M17` remains **`blocked`**, and
so do `M18`, `M19`, `M20` and `M21`. Writing this analysis does not unblock them; the blocker is
about the input and the trust anchor, not about whether the boundary has been understood.

**Scope of the claim:** this is analysis, not legal advice and not a plan of record. It records
what public evidence supports about a trust boundary, and it is written to be falsifiable by §4.

**What this is:** an engineering feasibility and security analysis of the authentication and trust
requirements that stand between PC5's platform work and the project's destination, written to
`M17`'s four acceptance items.

**What this is not:** an implementation guide for defeating authentication; a specification of any
bypass, patch, key or workaround; a claim that any genuine Sony system software has been loaded,
executed or run by PC5 (it has not, in any sense — see §7.4); legal advice; or a change to any
acceptance criterion. The refusal list in §6 is unchanged by anything written here, and nothing in
§2 or §5 may be read as a plan: the steps are *named and classified* precisely so that the parts
nobody may build stay named as the parts nobody may build.

Authority for the vocabulary and the boundary:
[`PS5_PLATFORM_CONTRACT.md`](../architecture/PS5_PLATFORM_CONTRACT.md) §2 and §3.7, ADR-007 and
ADR-022 in [`TECHNICAL_DECISIONS.md`](../TECHNICAL_DECISIONS.md), and the architecture spec
[`PC5_ARCHITECTURE_SPEC_v2.md`](../architecture/PC5_ARCHITECTURE_SPEC_v2.md). Method and scope:
[`SCOPE-AND-DEPENDENCY-ASSESSMENT-20261122.md`](../../evidence/m17-security-boundary-v1/SCOPE-AND-DEPENDENCY-ASSESSMENT-20261122.md).

---

## 0. Method, vocabulary, and how much confidence each row carries

Three vocabularies have to be reconciled, because this document answers an external request that
used one while the repository enforces another. The repository's markers are the ones with a
machine-checkable meaning here — the rule engine in `psm/registry.py` rejects any other value — so
they are what the tables use:

| repository marker | means | may be implemented? | maps to the requested class |
|---|---|---|---|
| `PUBLIC` | a public primary source states it, cited with publisher, title, date, URL and location | yes, with a conformance case on the PC5 side | `public documentation` |
| `INFERRED` | it follows from public facts plus an assumption written into the claim | yes, assumption named | `public documentation` (weakened) |
| `UNKNOWN` | nothing public supports a value or a behaviour | **no** — a double returns `unsupported`, never a plausible value | `unknown` |
| `RESTRICTED` | reaching it would require an act on the §6 refusal list | **no, ever** (ADR-007, ADR-022) | *(no counterpart — the distinction is the point)* |

Sources are labelled `verified` (read in this environment on 2026-11-22), `located` (publisher,
title and URL confirmed, body not read here) or `not-verified`. `observable behaviour` in the
requested vocabulary is used for what PC5 measured directly in this environment, always with the
command that produces it, and it is never promoted to `PUBLIC` about the console: an observation
about a PC, a repository file, or a public source repository's README is an observation about
*that*, not about Sony's system software.

Three epistemic labels are used in prose: **[fact]** — carried by a cited source; **[assessment]**
— a reasoned conclusion whose premise is named; **[unknown]** — no public source supports a value.
A row that says `[assessment]` is not evidence, and no row here is offered as evidence about
console behaviour.

**"A conventional PC could lawfully provide this"** has an operational meaning, not a legal one:
the capability or input is obtainable by running ordinary, documented PC platform firmware or
hardware features, or by using a channel the rights holder itself publishes, **without** any act
from the §6 refusal list. Whether a given act is lawful in a given jurisdiction is not adjudicated
here — that is the deliberate limit of this document, and §10 lists it as an open dependency.

## 1. What is being authenticated, and against what

There are two distinct questions that discussions of this destination routinely merge:

1. *Can this code run here?* — a capability question about CPU, memory, devices.
2. *Will this code accept this platform as authorised?* — a trust question answered by a
   verification performed inside the consumer, against a key the consumer already holds.

The destination is gated on (2), not (1). The console's answer to (2) is computed by code and
silicon that PC5 neither has nor seeks: `C-SEC-01` in the contract's registry records the
boot-chain authentication and root of trust as `RESTRICTED` — "the mechanism is not public, and
reaching it would require circumvention" — and `C-SEC-02` records what the system software does
with authenticated state once running as `UNKNOWN`. That is why this subsystem has a contract and
no interface (§3.7), and why a `denied` result in the status vocabulary is distinct from
`unsupported`: "you will not" is not "you do not know".

## 2. Authentication-step inventory

Rows are derived from the boot-order chain in
[`BOOT_FEASIBILITY.md`](BOOT_FEASIBILITY.md) §1, the package facts in
[`FIRMWARE_ANALYSIS.md`](../FIRMWARE_ANALYSIS.md) §2, the installation sequence in
[`PS5_SYSTEM_SOFTWARE_TARGET.md`](../PS5_SYSTEM_SOFTWARE_TARGET.md) §5, and the two security claims of
the platform contract. **No step is described by mechanism.** Where a source names a requirement,
the requirement is listed; where no source names a mechanism, the mechanism column of this table
does not exist.

Legend for **PC?**: `yes` = ordinary documented PC capability, no refusal-list act needed;
`no-anchor` = the PC has an analogous mechanism but not the trust anchor this step needs;
`no-input` = the required input is not lawfully obtainable; `n/a` = console-side step a PC cannot
perform at all; `unknown` = not classifiable from public sources.

Rows score the step **as a whole**; a step that is partly satisfiable is not a `yes` row.
**No row in the table is `yes`.** That is the finding, not an omission: read down the **PC?** column
and there is not one authentication step on this path that an ordinary, documented PC platform
capability satisfies end-to-end. §7.3 keeps the two lawful partials in view (S1's file-handling
share, S9's contract-side work), and they are exactly that — partials of steps, not steps.

| # | Step | What must be authenticated or trusted | Performed by | Depends on | PC? | Class | Conf. |
|---|---|---|---|---|---|---|---|
| S1 | Package provenance at install time | the updater must accept only an "official update file provided online by Sony Interactive Entertainment"; files from other sources, or an "altered or modified" console, "might not be able to install the official update data" | the console's updater | the published channel | no-input | `PUBLIC` (Sony's own support page, quoted) | high |
| S2 | Outer container signature | the `SLB2` package is signed and/or contains signed entries; the console validates it | console updater, before install | Sony signing key held by the console | no-anchor | `INFERRED` (community reports + Sony's instructions; layout version-specific, explicitly *not verified here*) | medium |
| S3 | Per-version encryption of inner components | inner components are encrypted; reading them needs a key the consumer does not hold | console, at load | a device- or version-specific key | no-input, **and refused** | `INFERRED`; the *key* is `RESTRICTED` | medium |
| S4 | First code the SoC runs | boot ROM / reset vector authenticates the next stage against a hash rooted in the console's fuses | console silicon | immutable mask/efuse values | n/a | `PUBLIC` that such an anchor exists; `RESTRICTED` for its details (`C-SEC-01`) | high on existence, zero on mechanism |
| S5 | Chain of trust to the kernel | each stage authenticates the next (loader → kernel → modules), so the running system is the authorised one | console boot stages | S4 | n/a | `INFERRED` from the existence of an authenticated chain | low-medium |
| S6 | Kernel authority to run privileged console services | the kernel's right to set up the platform (memory map, device ownership, service layer) is granted by authenticated state, not by hardware discovery | console kernel | S5, S10 | n/a | `UNKNOWN` | low |
| S7 | Platform authorisation state | a notion of "this is a legitimate, unaltered console" that later checks consume | security processor / fused state | S4 | n/a | `UNKNOWN` (`C-SEC-02`: "no public source describes it") | low |
| S8 | Component firmware authentication | GPU (uEngine) and other component firmware must be authenticated before use | console / component RoT | S4 | n/a | `PUBLIC` that component firmware is console-specific and "no public driver contract" exists (BF §1 row 6); mechanism `RESTRICTED` | medium |
| S9 | Storage controller and decompression path | the custom NVMe controller's own firmware/decompression path is part of the platform the software expects | console storage stack | S4, S5 | no-anchor | `PUBLIC` that a custom path exists (BF §1 row 7; Sony's 2020 spec post: 825 GB SSD, 5.5 GB/s raw); `UNKNOWN` for its contract | medium on existence |
| S10 | Update/recovery mode entry | the console only accepts the file when entered through its own Safe Mode procedure (power-button sequence, `PS5/UPDATE/PS5UPDATE.PUP`) | console service mode | the console's UI and its own integrity state | n/a | `PUBLIC` (Sony's support instructions) | high |
| S11 | Entitlement and online checks at run time | signed-in, licence and telemetry checks consumed by titles and the shell | system services / PSN | S7, network | unknown | `UNKNOWN`; secondary reports of an emulator "stalling at a PSN/online check" are `not-verified` and are **not** treated as fact | low |
| S12 | Post-boot integrity attestation | whether the running system attests its own authenticated state to consumers (services, titles) | system software | S7 | unknown | `UNKNOWN` — no public source describes the interface | low |
| S13 | A platform model's own acceptability | *the step PC5 cares about*: would the genuine software accept a PC-hosted model as an authorised platform | the software, via S2–S7 | S4 anchors every one of them | no-anchor | `UNKNOWN` by construction; this is the question M18 cannot answer in advance | n/a |

### 2.1 Why each "no" is a "no"

* **S3 and anything keyed to Sony's keys — `no-input`:** the input required is a key or a
  decrypted artifact. There is no lawful channel that provides it, and acquiring it is on the §6
  refusal list, so this analysis records the requirement and stops.
* **S11 and S12 are scored `unknown`, not `no-input`, and the difference is deliberate:** for S3
  we know what the missing input is (a key) and refuse it; for the entitlement and attestation
  steps we do not know the interface well enough to name the input at all. Nothing is gained by
  marking them `RESTRICTED` on a guess, and nothing would be gained by marking them
  `no-input`: an `unknown` row may not be implemented either, but it also stays open to being
  answered by a public source later, which a refusal is not. The repository's own tool says
  the same thing at the code level: `tools/firmware.py` notes "The PFS image is AES-XTS encrypted;
  PC5 does not decrypt it." **[fact]**
* **S2, S4–S10 — `no-anchor` or `n/a`:** a conventional PC *does* have an authenticated boot chain,
  and this is the most useful thing §2 says. UEFI Secure Boot verifies boot applications against
  `db`/`dbx`; AMD Platform Secure Boot authenticates the first UEFI firmware block through the on-die
  secure processor, keyed to hashes fused in the silicon; TPM 2.0 extends measurements into PCRs so a
  verifier can check what ran. All three are ordinary, documented, lawful PC capabilities. None of
  them can make Sony's updater or kernel accept the platform: the anchors are enrolled by the platform
  vendor and its key holders, not by Sony, and the console's chain is anchored the other way. Making
  the console accept a PC anchor instead is **trust-anchor substitution**, which is §6, not §2.
  **[assessment]**, premise: the PC mechanisms are documented for PC firmware, and nothing public
  describes any enrolment path by which a console chain would consume them. Sources: `S-UEFI`
  (Secure Boot, `db`/`dbx`), `S-AMD-PSB` and `S-IOACT-PSB` (the secure processor authenticating the
  first firmware block against fused hashes); `S-AMD-PSB` and `S-IOACT-PSB` also describe the TPM
  measurement role they expect. All are `located` here — see §9 for exactly what was read.
* **S6, S7, S12, S13 — `unknown`:** not "unlikely"; there is no public source. A `UNKNOWN` row may
  not be implemented, and a double for it must return `unsupported` rather than a plausible value —
  the contract rule, kept here so the analysis cannot be read as a licence to guess.
* **S3 and S4 are what the roadmap itself calls external preconditions.** `PS5_SYSTEM_SOFTWARE_TARGET.md` §4 classifies nine requirements and then states that requirements 2 and 3 — a lawful, authenticated way to obtain the inner components, and a trust anchor equivalent to the console's security processor — are *not* PC5 work; the table files both of them against `M17`. An inventory that reached the same two rows independently and then disagreed with the repository would be the interesting result; here they agree.
  **[fact, in-repo]**, with the caveat that the classification is the project's own judgement about its scope, not a measurement of the world.
* **S13 is the one that decides the milestone.** Everything else in the table is either ordinary PC
  engineering or ordinary refusal. S13 asks whether the *software* accepts a modelled platform, and
  the only thing that can answer it is the software itself, run against a model. That is `M19`'s
  evidence class by definition, so no amount of analysis — including this — can close it. **[assessment]**

## 3. The feasibility paths, restated as written

[`BOOT_FEASIBILITY.md`](BOOT_FEASIBILITY.md) §3 lists **three** paths — a point worth
stating because a count of "four" was circulated in a follow-up note and is wrong (§8.1). Restated
without changing their meaning:

**A. Sony authorises it.** A licensed PC platform, or a published virtualisation contract. **[fact
that none is publicly known]**: no such programme is described by the material reviewed. "No amount
of engineering substitutes for it" is the document's judgement and this analysis agrees with it,
because A is the only path that supplies the anchor in S4/S7 rather than working around it.

**B. A complete console emulator exists, including the security processor**, so the signed boot
chain is *emulated rather than bypassed*. **[assessment — partially stale as written]**: the
document's "publicly unattempted in full" no longer holds for emulation *in general*: public
source repositories exist and are active (§4.1). It still holds for the qualifier that matters —
none of what was reviewed presents itself as emulating the security processor or booting the signed
system software; they load game executables with user-supplied dumps. Path B's condition therefore
remains unmet, while becoming less hypothetical than the sentence implies.

**C. The system software is rebuilt from decompiled or leaked sources.** **[fact, about PC5]**: this
is what the project will not do — no Sony binaries, keys or derived code are distributed, and no
circumvention is implemented. This analysis reaffirms C as refused, not as unassessed.

The document's own conclusion follows from the three: "If none of A–C holds, genuine PS5 system
software cannot be booted by this project, and the honest deliverable is the analysis and tooling
plus a clear statement". `FIRMWARE_ANALYSIS.md` §5 splits the same question into four ordered
requirements (a verified loader path; SoC-level device emulation; a storage and file-system
implementation; "a legal basis for using and, if necessary, decrypting material — which PC5 does
not have and does not assume"), and its step 1 is S4/S5 here. Both documents stand; §4 refines
their evidence, §7 states the consequence.

### 3.1 The three decompositions of one question, reconciled

The same dependency question is written down three times in this repository, in three different
grain sizes, and the counts are what confuse people:

| document | how many | items | rows here |
|---|---|---|---|
| `BOOT_FEASIBILITY.md` §3 | **3 paths** | A authorisation, B full emulator incl. security processor, C rebuild from leaked sources | the whole of §3 above |
| `FIRMWARE_ANALYSIS.md` §5 | **4 requirements, in order of dependency** | 1 verified loader path, 2 SoC-level device emulation, 3 a storage and file-system implementation for the package format, 4 a legal basis | 1 → S4/S5 · 2 → S8/S9 and the `M11`–`M16` device layer · 3 → S1/S2 as the package to be read, plus `M13` as the console's storage contract · 4 → §6 |
| `PS5_SYSTEM_SOFTWARE_TARGET.md` §4 | **9 requirements, classified** | container understanding · lawful authenticated input · trust anchor · platform init · CPU · memory · storage · GPU · audio/USB/services | 1 → S2 · 2 → S3 · 3 → S4 · 4 → S6 · 5–9 → the `M11`–`M16` layer, which is capability rather than trust and is therefore *not* inventory rows here |

The mappings in the right-hand column are **[assessment]** — this document's reading of which row
answers which question. None of the three source lists says "this maps to S4"; if a reader prefers
a different pairing, the counts, the classes and the conclusions below are unaffected.

The middle row is the origin of a number that has been misattributed before: four is the count in
`FIRMWARE_ANALYSIS.md` §5, not in `BOOT_FEASIBILITY.md` §3 (§8.1). Keeping the three lists apart
matters because their conclusions differ in kind: §3's paths are about whether a lawful route
exists at all, §5's items are engineering sequence, and §4's nine rows are the only one of the
three that says which parts are **not PC5's to do** —

> requirements 1–9 are all **PC5 work**, and most of them are useful on their own… requirement 2 and
> requirement 3 are **not** PC5 work. They are external preconditions.

That sentence is the strongest in-repo corroboration this analysis can have for the two rows that
carry the whole blocker: S3 (a lawful, authenticated way to obtain the inner components,
class **restricted**) and S4 (a trust anchor equivalent to the console's security processor, class
**Sony-specific silicon — may be impossible**). Both are recorded there against `M17` itself. This
document adds nothing to that conclusion and takes nothing away from it.

## 4. Falsifiers, assessed against what is actually available

§4 of `BOOT_FEASIBILITY.md` names three conditions under which its assessment would be wrong. Each
is answered here with the evidence reviewed on 2026-11-22 and the retrieval limits of this
environment. Extracts are preserved in
[`FALSIFIER-SOURCE-EXTRACTS-20261122.md`](../../evidence/m17-security-boundary-v1/FALSIFIER-SOURCE-EXTRACTS-20261122.md).

**F-1 — "an authorised, public path to obtain the inner system components".** **Not observed.**
What exists is narrower than the sentence and worth separating: Sony's own support page publishes
the *outer* package for update and for reinstallation, so a lawful download channel for
`PS5UPDATE.PUP` is documented **[fact, S-SONY-SW]**. The falsifier asks about the **inner**
components, which are the encrypted entries (S3); no reviewed source describes an authorised path
to them. Public *claims* of decryption tooling exist — the gbatemp thread the repository already
cites, titled as a "PUP decrypt tool", and a community firmware list that declines to host payloads
and offers them only to "PS5 security research" **[fact that the claims exist; `not-verified`
about their truth]** — and none of them is *authorised*, so none can satisfy F-1 as worded: an
unauthorised decryption path is §6, not a falsifier. **What would change this:** a published
authorisation from the rights holder naming PC execution as a permitted use, or an official
distribution of the inner components.

**F-2 — "a working full-SoC emulator that boots Sony-signed software on commodity hardware (with
published evidence)".** **Not observed, and materially closer than the record implies.** Measured
directly from `api.github.com` on 2026-11-22 **[fact, observable]**: `sharpemu/sharpemu` (C#,
GPL-2.0-or-later, created 2026-03-11, 6,692 stars, pushed 2026-11-20) describes itself as "An
experimental PlayStation 5 emulator for Windows and Linux", and its README's Status section says it
"can currently load the `eboot.bin` of real games, execute native CPU instructions, and partially
handle gpu-related functionality", that "All games used during development and testing are dumped
from consoles that we personally own", and that the project "does not contain any copyrighted
system firmware"; `KytyPS5/KytyPS5` (C++, GPL-2.0, created 2026-06-09, 12,461 stars, pushed
2026-11-21) is a "PlayStation 5 translation layer" whose status is "expanding game compatibility and
improving boot reliability", needing user-supplied `eboot.bin`/`.zar` dumps; `RPCSX/rpcsx`
(created 2023-06-22, 2,043 stars) calls itself "An experimental PlayStation 4 and PlayStation 5
emulator" with no boot-status claim in its README and last pushed 2026-06-29. **None reviewed**
presents full-SoC coverage, security-processor emulation, or a boot of the signed *system
software* on a PC. Secondary reporting claims a project boots a "VSH" and safe mode
**[`not-verified`]** — a claim this analysis explicitly declines to treat as established, per §4's
own "with published evidence" bar. So F-2 is unmet, and PC5's §7 position (a model, not an
emulator; contract, not guesswork) is unchanged; but "publicly unattempted" is no longer the right
wording, and §8.2 proposes the correction.

**F-3 — "a Sony-licensed scheme to run PS5 system software on PC".** **Not observed.** The reviewed
material shows the opposite shape: Sony's published PC activity is games on PC and streaming from a
console, neither of which is the system software executing locally on PC. **[assessment]** from the
absence of any licensing statement in the reviewed sources, plus the documented console-only
framing of S1/S10 (the update path assumes a console performing the install). **What would change
this:** a published licence, SDK, or virtualisation contract naming PC execution.

Per the same §4 rule, an observed falsifier must be recorded in
[`RESEARCH_LOG.md`](RESEARCH_LOG.md) with a source and `BOOT_FEASIBILITY.md` revised.
No falsifier is observed, so neither is done here; F-2's *partial* movement is recorded in §8.2 as
a wording correction, which is the honest size of the finding.

## 5. Platform-model assessment

The distinction the milestone asks for — what a model could satisfy, and what it cannot — is stated
in four layers, deliberately kept apart. Each layer's "proves" column is what a reader may
conclude, and no more:

| layer | what it is | what it can demonstrate | what it can never demonstrate |
|---|---|---|---|
| **L1 — ordinary PC firmware and hardware** | UEFI + Secure Boot, AMD PSB / Boot Guard-class roots of trust, TPM 2.0 measurement and attestation (sources as in §2.1) | that authenticated boot, measured boot and remote attestation are standard, lawful, implementable PC capabilities; PC5's own boot path can be built and tested on them | anything about the console's chain: the anchors are different, and none of it is a step toward S4 |
| **L2 — a hypothetical PC5 platform model** | `M11`–`M16`: contracts, test doubles, conformance suites, PC5-authored payloads | that PC5 presents a defined platform: CPU/privilege/memory/interrupt/storage/graphics/audio/USB/service behaviour conform to *PC5's* written contract, with unknowns returned as `unsupported` | acceptance by the genuine software (S13); any security-state property (there is no `PSM-SEC` interface, by rule and by test); "the trust chain is satisfied" |
| **L3 — the genuine target platform** | a retail PS5 | the reference behaviour the model aims at | not available to PC5: no console hardware, and none is claimed |
| **L4 — actual authenticated system-software execution** | the destination (`M19`, level 5) | the software's own output identifying itself, on a recorded configuration a third party can repeat | — |

Per-step verdict, which is `M17`'s fourth acceptance item:

| step | a platform model could satisfy it? | how that verdict was reached |
|---|---|---|
| S1 provenance of the input | **partly** — the model can host and present a file and verify its own recorded hash; it cannot make the *console's* updater accept it | needs no secret, so L2 can do its own share; S1 is defined by Sony's console-side policy |
| S2 container signature | **no** | verifying a signature requires the verifier's key policy; a model can *check* a signature against a key it is given, which is not the same as the console accepting the package |
| S3 encryption of components | **no, ever** | `RESTRICTED`: refusing to decrypt is the boundary, not a gap in effort |
| S4 fused first-code anchor | **no** | the model has no way to be the console's silicon; simulating the *outcome* of a fused check is the definition of trust-anchor substitution |
| S5 chain to the kernel | **no** | inherits S4 |
| S6 kernel authority over services | **unknown** | no public description; a model may expose the *device* contracts (`M16`) and must return `unsupported` for privileged-authorisation semantics it cannot honour |
| S7 platform authorisation state | **no** | `UNKNOWN`/`RESTRICTED` mixture; the contract keeps the whole subsystem out of the interfaces, and `tests/test_psm_registry.py::test_security_is_restricted_and_has_no_interface` enforces that in code |
| S8 component firmware | **no** | console-specific firmware contracts are `UNKNOWN`; the model's job (L2) is to state its own GPU contract honestly, not to answer this |
| S9 storage/decompression path | **partly** | the model can define and pass its own storage contract (`M13`) and be measured against it; the console's expectation of custom hardware stays unsatisfied |
| S10 Safe-Mode entry procedure | **not applicable** | a console UI procedure with no PC analogue; the model neither needs nor can fake it |
| S11 entitlement/online checks | **unknown** | no public interface; if a title checks entitlements, the answer comes from services, not from PC5 |
| S12 runtime attestation | **unknown** | `C-SEC-02`; nothing public describes what is done with authenticated state |
| S13 the software accepts the platform | **not decidable by modelling** | the software itself is the only referee; that is `M18`/`M19`'s evidence rule and `product.destination.must_not_be_satisfied_by` in `roadmap.json` |

**The asymmetry to keep in view, stated once and plainly:** a model that passes its own conformance
suite is a statement about the model. It is not evidence that the genuine platform's trust chain has
been satisfied. An emulator, a stub, a mock, a firmware map, a boot log from PC5's own kernel, or a
successful `make check` run must never be presented as genuine system-software execution; the
roadmap forbids those five as destination evidence, and this document inherits the prohibition.

## 6. The boundary, restated unchanged

From ADR-007, ADR-022 and contract §3.7. PC5 does not specify, implement, test, plan or *design
toward*:

1. extracting or obtaining protected keys, in any form;
2. decrypting protected proprietary payloads (the `PUP` and its inner components);
3. bypassing a signature check, defeating an authentication step, or substituting a trust anchor;
4. patching, modding or otherwise altering protected firmware to make it accept a foreign platform;
5. unauthorised access to, or distribution of, proprietary Sony binaries or anything derived from them;
6. any claim of Sony authorisation, of compatibility, or of genuine system-software boot, without
   evidence of the class §5/L4 requires.

`docs/KNOWN_LIMITATIONS.md` and `evidence/` records keep the same rule for the *USB* path: no
physical validation has occurred, so writing media is not deployment-approved. Nothing in this
document changes that.

What is explicitly permitted, and is what this workstream did: reading public documentation;
measuring the repository; naming requirements; classifying them; recording unknowns as unknowns.
A reader who wants this document's conclusions in another form should ask for a source, not for a
mechanism — there is no mechanism in it, and there will not be one in a revision.

**Measurement backing item 3 as a property of the tree, not a promise:** grepping
`tools/`, `psm/`, `kernel/` for crypto primitives and library imports on 2026-11-22 found no crypto
library imported anywhere in them, and the only occurrences of the words `decrypt` in `tools/` are
refusal statements (`tools/firmware.py` lines 13, 166, 219; `tools/pc5ctl.py` line 8;
`tools/presentation.py` line 686 prints "analysed, decrypted or executed | **no**, in any sense").
`psm/` has no `security` module — the directory contains
`audio, audit, conformance, contract, cpu, graphics, interrupts, memory, psm, registry, render,
services, storage, usb`.

## 7. Conclusions

**7.1 What the public evidence establishes.** That the destination is gated on a trust decision
taken inside software PC5 does not have, against an anchor PC5 cannot lawfully hold; that an
authenticated boot chain on the console side *exists* (its existence is uncontroversial industry
practice, per the contract, and the details are `RESTRICTED`); that conventional PCs have their own
documented, lawful roots of trust, measurement and attestation, which are structurally analogous
and specifically unusable here; that Sony publishes the outer package for update and reinstallation
and frames it as console-only; and that PS5 emulation of *game executables* is now a public, active,
substantial engineering activity, which none of the reviewed projects describes as booting the
signed system software or emulating the security processor.

**7.2 What remains unknown — and stays unknown.** The mechanism and measured values of the
console's chain (S4, S5); the privileged-authorisation semantics (S6); what is done with
authenticated state at run time (S7, S12); the entitlement path (S11); the inner-component entry
table of the specific package the repository points at (recorded `NOT VERIFIED` in
`PS5_SYSTEM_SOFTWARE_TARGET.md` §1.1, and it stays that way, because the payload was never fetched
here and will not be); and above all S13.

**7.3 What a conventional PC, or a model, may lawfully satisfy.** S1's own share (hosting and
verifying a file against a recorded hash), S9's contract-side work, and — entirely — L1 and L2 as
engineering: the platform model, its ten interfaces, its conformance suites. These are worth
building on their own merits and are what `M11`–`M16` ask for. None of them moves S4, S7 or S13.

**7.4 Why `M17` remains `blocked`.** Its blocker is a statement about the world — no lawful trust
path is known — and this analysis was written to test that statement rather than to repeat it. The
test did not find a path: the two conditions that could create one (A and B in §3) are both
unmet, and the third (C) is refused on principle. The analysis half is done; the boundary half is
not, because a boundary cannot be crossed by analysis. `M17`'s state is therefore unchanged, and
`roadmap.json` records only a `notes` field saying the deliverable is published.

**7.5 Why `M18` and `M19` remain `blocked`.** `M18` (genuine system-software load) needs a lawful,
authenticated input — the payload's absence from the tree is asserted by tests, not an oversight —
plus `M17`'s outcome. `M19` needs `M14`, `M15`, `M16` *and* `M18`, and its acceptance is the
software's own output, which no model can produce on its behalf; `M20` and `M21` sit behind `M19`.
Do not weaken any of those criteria to make the chain look shorter: the criteria are the only
thing that makes the eventual answer worth having.

## 8. What this document found wrong elsewhere (proposed, not applied)

**8.1 A count of "four" attributed to `BOOT_FEASIBILITY.md` §3, which lists three.** A follow-up
note in PR #36 (`evidence/usb-descriptor-remediation-v2/POST-MERGE-RECONCILIATION-20261122.md` §8)
refers to "the four 'would have to be true' paths of BOOT_FEASIBILITY.md §3". Measured: §3 contains
`A.`, `B.`, `C.` and no fourth item (`grep -c '\*\*[A-F]\.' docs/playstation/BOOT_FEASIBILITY.md`
→ 3; `grep -n '\bD\.'` over the file → no match). The number itself is not invented — four is the
count in `FIRMWARE_ANALYSIS.md` §5, and nine is the count in `PS5_SYSTEM_SOFTWARE_TARGET.md` §4;
§3.1 maps all three decompositions. **So the minimal correction is a citation fix, not an arithmetic
one:** either "the four ordered requirements of `FIRMWARE_ANALYSIS.md` §5" or "the three paths of
`BOOT_FEASIBILITY.md` §3". Saying "three" alone would fix the sentence while leaving the next reader
with three lists and no reason to trust any of them.

**8.2 `BOOT_FEASIBILITY.md` §3B's "publicly unattempted in full" is stale.** Public, active,
large-effort PS5 emulation exists (§4, F-2). The sentence's load-bearing qualifier — emulation
"including the security processor" — still holds, so the *conclusion* is unaffected. Proposed
correction, for the maintainer to apply as a dated revision in the document's own style:

> *B (status note, 2026-11-22):* full-SoC emulation remains unattempted, but PS5 emulation of game
> executables is now publicly active (`M17` analysis §4, F-2), so "publicly unattempted in full"
> should be read as "no published full-system emulation including the security processor".

**8.3 `docs/BUILDING.md` line 12 states `make check` skips 107 tests without `unicorn`.**
Measured in a fresh clone of `main` at `52f682c` with no `unicorn` installed: `Ran 929 tests …
OK (skipped=109)`. The figure is two stale. Proposed: make the row's number a thing a test checks,
or drop the number and keep the sentence — an exact count in prose is the sort of claim that goes
quiet.

## 9. Sources

**In-repo (read in full or at the cited lines, in this clone, 2026-11-22), `verified`:**
`docs/architecture/roadmap.json` (M17/M18/M19 entries, `product.levels`,
`destination.must_not_be_satisfied_by`, `forbidden_claims`);
`docs/playstation/BOOT_FEASIBILITY.md` §1–§7; `docs/PS5_SYSTEM_SOFTWARE_TARGET.md` §1, §3.1, §4–§8;
`docs/architecture/PS5_PLATFORM_CONTRACT.md` §2, §3.7, §4; `docs/FIRMWARE_ANALYSIS.md` §2, §5;
`docs/TECHNICAL_DECISIONS.md` ADR-007, ADR-022; `docs/KNOWN_LIMITATIONS.md`; `psm/registry.py`,
`tests/test_psm_registry.py`, `tests/test_product_identity.py`, `tests/test_architecture.py`,
`tools/firmware.py`, `tools/docs_check.py`, `ci/README.md`.

**External, with verification state as of 2026-11-22:**

| ID | Title / publisher | Date | URL | State |
|---|---|---|---|---|
| S-SONY-SW | "How to update system software on a PS5 console" — Sony Interactive Entertainment, PlayStation Support | page dated 2026-11-03 in the retrieved listing | <https://www.playstation.com/en-us/support/hardware/ps5/system-software/> | `located` — quoted via a retrieved search excerpt; the full page was not fetched in this environment. The same URL is already cited by `docs/FIRMWARE_ANALYSIS.md` §2 |
| S-SHARP-EMU | `sharpemu/sharpemu` README and repository metadata — GitHub API | repo created 2026-03-11; pushed 2026-11-20 | <https://github.com/sharpemu/sharpemu> | `verified` — README and metadata read here on 2026-11-22 |
| S-KYTYP5 | `KytyPS5/KytyPS5` README and repository metadata — GitHub API | created 2026-06-09; pushed 2026-11-21 | <https://github.com/KytyPS5/KytyPS5> | `verified` — as above |
| S-RPCSX | `RPCSX/rpcsx` README and metadata — GitHub API | created 2023-06-22; pushed 2026-06-29 | <https://github.com/RPCSX/rpcsx> | `verified` — as above |
| S-AMD-PSB | "AMD PRO Technologies — security and the AMD framework…" (white paper), Advanced Micro Devices, Inc. | 2025-03 (retrieved listing) | <https://www.amd.com/content/dam/amd/en/documents/products/processors/technologies/amd-pro-technologies-security-white-paper.pdf> | `located` — excerpt read via search; PDF body not fetched here |
| S-IOACT-PSB | "Exploring AMD Platform Secure Boot", IOActive | 2026-11-17 | <https://www.ioactive.com/exploring-amd-platform-secure-boot/> | `located` — excerpt read via search; page not fetched here |
| S-UEFI, S-NVME, S-AMD-APM | reused from the platform contract's registry (`verified`/`located` there, retrieval date 2026-11-16) | — | see contract §2 | as recorded in the contract |
| S-GBATEMP | gbatemp thread on a "PUP decrypt tool", cited already by `FIRMWARE_ANALYSIS.md` §2 | not retrieved | see `FIRMWARE_ANALYSIS.md` §2 | `not-verified` — cited here only as evidence that *claims* of such tooling circulate, never as support for any capability |
| S-FWLIST | community "PS5 official firmware list" (checksums; explicitly declines to host payloads) | retrieved 2026-11-22 | <https://github.com/MewX/ps5-official-firmware-list/blob/main/README.md> | `located` — README excerpt read via search; used only for §10's metadata observation |

Secondary emulator-status reporting (three sites surfacing in the same search) was read in excerpt
form only and is **not** cited as a source for any claim about what boots; where a secondary claim
matters, §4 says so and marks it `not-verified`.

## 10. The next evidence, and what would change this document

1. **A metadata-only identification of the package the repository points at, which needs no
   payload.** Sony's update-list URLs embed the SHA-256 of the file they point to, and the community
   list publishes per-version hashes and sizes **[fact, from the retrieved excerpts]**. So the
   repository's *declared* object id `42ea0e5aad1361e098837d40157863c4c519f0bbc66eb03c04dbaaf339b063fb`
   and size 1,423,697,408 B could be matched against an official `updatelist.xml` (and the
   published checksum table) to identify version and whether the file is an update or a
   reinstallation image — hashes and metadata only, no download, no decryption, fully inside
   ADR-022. **Not executed here:** this sandbox's egress does not include those hosts, and the
   question is `M9`'s, not `M17`'s. Recorded as the cheapest lawful evidence item in the whole
   destination path, and offered for the maintainer's decision. If run, it must be recorded in
   `docs/playstation/FIRMWARE_VERSIONS.md` per that document's rules.
2. **`M18`'s synthetic-package half is buildable now and should not wait.** Its third acceptance
   item is "the load path is exercised against a synthetic package PC5 builds itself, so the
   mechanism is testable without Sony bytes". That is the only part of `M18` that is not blocked,
   and it would give the loader a real conformance target while S13 stays open.
3. **What would change this document:** any of §4's three falsifiers being observed (then
   `BOOT_FEASIBILITY.md` is revised and `RESEARCH_LOG.md` gains an entry, per its own §4 rule); a
   public primary source describing the console's chain (then the corresponding `UNKNOWN` rows move,
   and only to `PUBLIC`); or a decision to abandon the destination, which would be a different
   roadmap, not a weakening of this one.
4. **What would not change it:** a PC5 kernel boot, a modelled device passing its own suite, an
   emulator screenshot, or a plausible reconstruction of the boot chain from leaked material. The
   first three are excluded by `product.destination.must_not_be_satisfied_by`; the fourth is
   excluded by §6.
