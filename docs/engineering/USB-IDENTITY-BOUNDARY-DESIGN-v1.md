# USB write identity: analysis, alternatives and the correction under review

Scope: `pc5ctl usb --iso … --device /dev/sdX --yes`, which copies an image to a
removable disk with `dd`. All work here is synthetic: no block device was
opened, no destructive write was performed, and nothing in this file is
hardware validation.

**Status now: implemented and merged.** Descriptor binding is in `main` as of
PR #35, merge commit `52f682c8435956c8210b3189cad23ebea973d2de` — see §8, which
is the authority for the current state. The paragraph below is retained as the
status *as authored on 2026-11-21*, before that PR, because §1–§7 analyse the
pre-remediation code and the review that led to it; it does not describe `main`.

> Status at authoring time: the correction exists in the working tree of
> `arena/c8a76776-pc5` **uncommitted**, plus `evidence/identity-boundary-v1/USB-identity-boundary-correction-v2.patch`
> (the apply-verified pair, with `USB-cli-boundaries-fd-update-v2.diff`; the `-v1` files are retained
> unchanged and superseded) (verified to apply cleanly to a fresh `git archive HEAD` export). It is a
> proposal for independent review; USB acceptance remains **BLOCKED**.

## 1. The production path, step by step

`tools/pc5ctl.py` as shipped at `56c5852`:

| # | Step | Mechanism | Identity used |
|---|------|-----------|---------------|
| 1 | `main` → `cmd_usb` | `argparse` | — |
| 2 | argument shape | `device.startswith("/dev/")` | string prefix only |
| 3 | existence | `os.path.exists(device)` | name |
| 4 | **decision 1** | `check_target_safe(device)` → `Topology.devnum_for_path` (`os.stat` → `st_rdev`), root device from mountinfo, `root_closure()` from sysfs | name → `major:minor` |
| 5 | confirmation | `--yes` | — |
| 6 | open | `os.open(device, os.O_WRONLY)` | **descriptor** |
| 7 | identity of what we hold | `os.fstat(fd)`, `S_ISBLK`, compared with a *second* `devnum_for_path(device)` | descriptor **and** name |
| 8 | **decision 2** | `check_target_safe(device)` again | name (a *third* resolution) |
| 9 | child | `subprocess.call([dd, "of=/proc/self/fd/N", …])` | descriptor path, **no `pass_fds`** |

Two defects live in steps 8 and 9.

* **Fail-open authorization (the serious one).** The decision the last
  pass makes is about whatever the *name* resolves to at step 8, while the
  write at step 9 goes to whatever the *descriptor* refers to. Between step 7
  (where name and descriptor agree) and step 8 the name can be retargeted —
  a symlink swapped, the stick pulled and a different one plugged in, a stale
  udev link. `evidence/continuation-descriptor-v1/USB-PATH-RACE.log` shows the
  guard authorizing a `dd` launch while the held descriptor is the root disk.
  This is a potential fail-open safety defect, not an operational nuisance.
* **Broken write.** `subprocess.call` closes descriptors for the child unless
  `pass_fds` names them, so `/proc/self/fd/N` does not exist for `dd`. Measured
  on an ordinary file: `dd: failed to open '/proc/self/fd/3': No such file or
  directory`, exit 1, nothing written (`USB-FD-REPRO.log`). Failing closed by
  accident is not a guarantee: it made every *real* write impossible while the
  authorization logic still trusted a name.

## 2. Alternatives considered

| Option | Binds write to authorized object? | Works unprivileged? | Verdict |
|--------|-----------------------------------|---------------------|---------|
| A. Validate the name, write the name (pre-`fd` behaviour) | no | yes | rejected: substitution window is the defect |
| B. Open, compare `fstat` with the name, write the name | no | yes | rejected: the comparison is only a sample; the write still re-resolves |
| C. Open, write `/proc/self/fd/N` without `pass_fds` (shipped draft) | partially | yes | rejected: child cannot perform the write; decision still name-based |
| **D. Descriptor-bound authorization + explicit inheritance + pre-launch re-validation** | **yes** | **yes** | **chosen, implemented in the working tree** |
| E. `O_EXCL` / `flock` on the block device, revalidate after locking | no | yes | rejected as the primary mechanism: Linux locks are advisory, and no lock stops `pivot_root`, a device-mapper table reload or a replug |
| F. `name_to_handle_at` + `open_by_handle_at` (identity by filesystem handle, independent of names) | yes, strongest | **no** — needs `CAP_DAC_READ_SEARCH` | deferred: the durable direction, out of scope for an unprivileged CLI; would be a privileged helper |
| G. `O_DIRECT` + read-back verification | orthogonal | yes | future integrity work, does not address identity |

## 3. The correction (option D) as implemented

Ordering matters; each step refuses and prints `nothing was written`:

1. `os.open(device, os.O_WRONLY)` — one open, held for the whole sequence.
2. `target_fd >= 3` — `pass_fds` cannot inherit a standard stream, and refusing
   must not close something that is not ours to close.
3. `fd_writable()` — `fcntl(F_GETFL)` on the *open file description* must report
   `O_WRONLY`/`O_RDWR`. Access mode is a property of the description, so this is
   what proves the inheriting child can write; a pathname can lie, this cannot.
4. `fd_block_identity()` — `fstat` must report a block device; `major:minor`
   becomes **the** identity for everything below.
5. `fd_child_target_usable()` — `/proc/self/fd/N` must be `lstat`-able and its
   `readlink` must not end in ` (deleted)`. A descriptor-backed path is not
   automatically safe: with procfs absent (containers, chroots) or the object
   unlinked, the child could not resolve it — and there is deliberately **no
   fallback to the original pathname**.
6. Name agreement check: `devnum_for_path(device)` must still equal the
   descriptor identity. This can only *refuse*; it never authorizes. It exists so
   a swapped device node is reported rather than silently bypassed.
7. **Decision on the held identity**: `check_target_safe(device,
   topology=_BoundTopology(Topology(), opened_as))`. `_BoundTopology` pins
   `devnum_for_path` to the descriptor's `major:minor`, so the root device, its
   parent disk, sibling partitions and the slaves/holders closure are all
   evaluated against the object that will be written — never against a fresh
   name lookup.
8. Final `fd_block_identity()` re-read immediately before the launch.
9. Exactly one output argument, pinned: `of=/proc/self/fd/<target_fd>`, with
   `close_fds=True, pass_fds=(target_fd,)`.
10. `subprocess.call` wrapped: an `OSError` at launch is a refusal (no retry, no
    pathname fallback). `finally: os.close(target_fd)`.

`fd_block_identity`, `fd_writable`, `fd_child_target_usable` are small functions
in `tools/pc5ctl.py` so the tests can drive them through the real CLI without
mocking the checks themselves: `fcntl`, `lstat` and `readlink` run against real
descriptors in the tests, and only *block identity* is synthetic.

## 4. What is still racy — the honest limit

Holding a descriptor binds *identity*; it cannot freeze *topology*. Between the
decision and the write, these can still change, and none of them is preventable
by an unprivileged process:

* the root filesystem moving onto the target — `pivot_root`, `switch_root`,
  `mount --move`, or an initramfs handover completing after we checked;
* the device-mapper or md layer growing to use the target — `dmsetup load`,
  `mdadm --grow`, `lvcreate --type mirror`; the `holders`/`slaves` sets we read
  are a snapshot of a moving graph;
* the partition table being rewritten (`sfdisk`, a USB reset renumbering
  partitions), which changes which sibling partitions belong to which disk;
* physical removal and re-addition with `major:minor` reuse — the kernel happily
  hands a new stick the number the old one had. Our write still goes to the
  object we hold (that is the point of the descriptor), but "this device is
  unrelated to `/`" was reasoned about the previous one;
* sysfs entries vanishing or becoming unreadable mid-read — handled as `UNKNOWN`
  and refused, never as "no relationships".

So the guarantee is precisely: **the object written is the object authorized,
and the authorization is computed from the kernel-reported identity of that
object; anything that cannot be established is a refusal.** The guarantee is
**not**: "nothing in the storage topology changed since the check" — no
userspace mechanism can promise that, which is why option F (a privileged
`open_by_handle_at` helper, plus in-kernel verification) is recorded as the
durable direction and why the write step itself is the only place a real
hardware guarantee can live.

Practical consequence for a physical run: perform the write from an environment
where the target cannot be the live root (rescue boot, or the device not mounted
and not referenced by any active dm/md target), and treat the CLI check as
defence in depth rather than as the sole control.

## 5. Verification inventory

* `evidence/identity-boundary-v1/USB-SUITE-v3.log` — 87 tests, exit 0: 56
  `test_pc5ctl_usb_safety`, 8 `test_pc5ctl_usb_cli_boundaries` (retained; their
  fabricated descriptor numbers were replaced by real writable descriptors so the
  positive controls pass for the right reason), 23 new
  `test_pc5ctl_usb_descriptor_identity`. `USB-SUITE-v2.log` is the same inventory
  one case earlier (86); the 23rd, `test_22`, keeps the `os.open` refusal branch —
  which predates this correction — permanently covered. The unmodified production
  file still fails this inventory in exactly 12 assertions plus 2 errors
  (`USB-SUITE-v3-BASELINE.log`).
* `USB-SUITE-v2-BASELINE.log` — the same 22 new tests against unmodified `HEAD`
  production: 12 assertion failures and 2 errors, including the fail-open case
  `test_08_symlink_substitution_after_opening_cannot_authorize_the_write`, which
  fails because `dd` *is* launched. That is the vulnerability, demonstrated by
  assertion rather than argument.
* `USB-MUTATIONS-v3.log` — the seven required mutations (pathname validation
  restored, pathname substituted after validation, `pass_fds` omitted, wrong
  descriptor passed, final identity comparison skipped, incomplete enumeration
  accepted, unreadable topology read as empty). Each is caught by its intended
  test with an `AssertionError` and exit code 1, plus the added
  `m8-open-failure-writes-by-name` (the target-open refusal replaced by a
  pathname write), caught by `test_22`'s own assertion; setup errors are rejected by the
  harness, and the unmutated baseline is green.
* `USB-PRIOR-MUTATIONS-corrected.log` — the five earlier mutation controls still
  detected against the corrected code, baseline green.
* `USB-REAL-DD-FD-PROOF.log` — real `/bin/dd`, ordinary file as target: with the
  correction `dd` writes through the inherited descriptor and the sha256 of the
  target equals the image; with `pass_fds` removed `dd` fails and the target is
  unchanged.
* `REPO-SUITE-corrected-namespace.log` — full repository suite in a disposable
  export of `HEAD` + correction, capabilities dropped and network isolated:
  919 tests, `OK (skipped=3)`, exit 0. Nothing here was OVMF- or hardware-run.
* `WORKSPACE-MAKE-CHECK.log` — the repository's aggregate gate (`unit`, `psm`,
  `docs-check`, `citations-check`, `presentation-check`, `brand-check`) in the
  working tree with the correction: 919 tests, `OK (skipped=2)`, exit 0, after
  installing the documented `unicorn==2.1.4` prerequisite.
  `WORKSPACE-MAKE-CHECK-missing-unicorn.log` keeps the pre-install failure (103
  `ModuleNotFoundError` errors) so the dependency's effect is auditable.

## 6. Acceptance position

Identity binding: implemented and covered. Failure paths: covered. Topology
atomicity: impossible in userspace, documented rather than claimed. Physical
validation: not performed. Therefore the USB milestone stays BLOCKED, and this
correction needs an independent review before it is applied to any branch.

*Both halves of that sentence were later discharged, in that order and no further:
the independent review is `evidence/usb-descriptor-independent-review-v1/`, and the
review's §10 conditions were met before the branch was opened. Neither the review
nor the merge changed the last two: topology atomicity stays impossible in userspace,
and physical validation has still not been performed. §8 states where that leaves
acceptance now.*

## Composition against the pushed branch tip

In a disposable clone at `ae9f3e25f66ac3d31b2b7b64dccef7695fef1d73` (the current remote tip of
`arena/c8a76776-pc5`, i.e. main plus the four M2a commits), the unmodified tree is 954 tests
`OK (skipped=2)`; adding the correction patch and the companion diff keeps it green at 985 tests
`OK (skipped=2)`, 87 USB cases `OK`, and `make docs-check` green. Both artifacts apply with plain
`git apply`, which means the descriptor binding is orthogonal to the M2a work — it neither rescues
it nor depends on it. `evidence/identity-boundary-v1/COMPOSITION-REMOTE-TIP-v1.log` holds the
commands and the test-count reconciliation; `CORRECTION-ON-REMOTE-TIP-export.log` records why a
`git archive` export is the wrong way to run this comparison.


## 7. Residual named by the independent review, added by the closure pass

Appended 2026-11-21 by the F-1/F-2/F-3 closure pass (`evidence/usb-descriptor-remediation-v2/`);
§1–§6 above are the original design record, unedited.

**F-8, stated in §4's terms.** The topology list in §4 covers what can change *after* a
decision. There is a second, older limit on the *root* side of the decision, which the
review named and which descriptor binding does not touch: the target side is identity-bound
(`fstat` on the held descriptor), but the root side is device-number-bound only when
`/proc/self/mountinfo` is readable. Where it is not, `root_devnum` falls back to resolving
the `/proc/mounts` source **name** through `devnum_for_path` — so if that name has been
retargeted, the protected set follows the name rather than the mount. Measured, not
inferred: the probe is `test_a_retargeted_root_node_would_move_the_boundary`, which passes
precisely because the residual is real. It is not exploitable into a write of the root
storage by accident: an unresolvable source fails closed (`test_unresolved_root_refuses_all_targets`,
every target refused). Fixing it properly means refusing to write at all when mountinfo is
unavailable, or reading the mount's `st_dev` from the mount point instead of its source
name; either change alters behaviour on hosts this pass cannot test, so it is recorded here
as a named residual rather than slipped into a remediation PR. `/proc/self/mountinfo` exists
on every Linux system the tool targets, which is why the residual is rated low.

**§6's condition is discharged, and only that.** §6 required an independent review before
this was applied to any branch: `evidence/usb-descriptor-independent-review-v1/` is that
review, and `evidence/usb-descriptor-remediation-v2/FINDINGS-CLOSURE-20261121.md` records
what was done about its findings, including the two claims of its own that measurement
overturned. What §6 also states — physical validation not performed — is unchanged: the
USB milestone stays **BLOCKED** whatever happens to this branch, and a merged PR is not a
device test.

**F-6 closure, and a correction to how it was first described.** The review's F-6 said the
CLI-level refusals survive the unreadable-topology mutant "through a second, unrelated guard".
Measured, the reason is less flattering and more fixable: `test_20`/`test_21` make a
directory under `devices/sda` unreadable, and the root-side walk interrogates each child of
the root disk in `partitions_of()` too — so both tests refuse for two reasons at once and can
never attribute the decision to `_relations`. `tests/test_pc5ctl_usb_topology_unknown.py`
instead denies reads on `devices/sda/sda1/holders` (and `…/slaves`), which only
`_relations` reads: real code answers UNKNOWN and the CLI refuses; with the mutant applied,
the answer is `[]`, the closure completes, and `dd` is launched — the cases fail, which is the
property the review asked to be pinned. Its control case asserts the same fixture writes when
nothing is unreadable, so the refusal cannot be overdetermined again by accident.

## 8. Current status, recorded after the merge (2026-11-21)

Appended by `docs/usb-post-merge-reconciliation`; §1–§7 above are unedited history.

* **Implemented and merged.** The descriptor-bound remediation is in `main`:
  PR #35 (`https://github.com/SpicyBadran/PC5/pull/35`), merge commit
  `52f682c8435956c8210b3189cad23ebea973d2de`, branch head `80fc8615283173fd820d26c5779ad0cb94047736`,
  four commits on base `56c58521580e88c4339ceb6eb40ce724a2bb533b`. §3's "correction
  (option D) as implemented" is therefore a description of shipped code, not a proposal.
* **Independently reviewed, in the repository's own record.** The adversarial review is
  `evidence/usb-descriptor-independent-review-v1/INDEPENDENT-REVIEW-20261121.md`
  (findings F-1…F-10); the disposition of every one of them, with the command that
  reproduces each and the measured result, is
  `evidence/usb-descriptor-remediation-v2/FINDINGS-DISPOSITION-20261121.md`. Two claims of
  the review were overturned by measurement and are recorded as overturned
  (`FINDINGS-CLOSURE-20261121.md`), including the first description of F-6's mechanism.
* **Tests and mutation verification are documented evidence, not hardware evidence.**
  95 USB cases (`test_pc5ctl_usb_safety.py` 56, `test_pc5ctl_usb_descriptor_identity.py` 27,
  `test_pc5ctl_usb_cli_boundaries.py` 8, `test_pc5ctl_usb_topology_unknown.py` 4) and three
  mutation harnesses (`usb-descriptor-remediation-v1/mutation_harness.py`,
  `usb-descriptor-remediation-v2/mutation_harness_v2.py`,
  `identity-boundary-v1/usb_identity_mutations.py`). `make check` on a fresh clone of `main`
  after the merge: `Ran 929 … OK (skipped=2)`, exit 0. Every one of those cases runs against
  temporary regular files and a synthetic `/sys/dev/block` tree.
* **F-8 remains open, disposition unchanged:** the *root* side of the decision resolves the
  `/proc/mounts` source **name** when `/proc/self/mountinfo` is unreadable, so the protected
  set can follow a retargeted name. §7 keeps the mechanism, the two candidate fixes and the
  reason neither was bundled into a remediation PR. It fails closed when the name cannot be
  resolved, and `test_a_retargeted_root_node_would_move_the_boundary` passes precisely
  because the residual is real.
* **F-9 remains open, disposition unchanged:** an unexpected exception escaping a
  *post-decision* topology read surfaces as a traceback instead of the `nothing was written`
  line. It fails closed — nothing launched, nothing written, non-zero exit — and was left
  alone deliberately because wrapping it would remove the diagnostic that says the guard was
  reached. Reporting quality, not a safety property.
* **Physical-device validation has not occurred.** No block device node exists in this
  environment and `mknod` is denied, so no test, no mutation harness and no green total has
  ever touched media. The evidence that the guard decides correctly is complete; the evidence
  that a real stick, a real firmware and a real `dd` behave as modelled does not exist.
* **USB deployment therefore remains blocked**, pending physical-device validation and
  explicit authorisation. Merging PR #35 authorised the *code in the tree*; it did not
  authorise writing an image to hardware, and nothing in §8 should be read as that. A
  follow-up record of the post-merge reconciliation — including why GitHub's 111 changed
  files and PR #35's first completion note of 103 are both correct, for different trees — is
  `evidence/usb-descriptor-remediation-v2/POST-MERGE-RECONCILIATION-20261122.md`.
