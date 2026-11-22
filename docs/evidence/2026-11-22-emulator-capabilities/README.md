# Why no emulator here can show an interrupt stack being switched (2026-11-22)

**Baseline.** `aeca706ee3514ba6bf9c16ead08df7a159262352` (live `main`, the merge of #44),
work on `arena/b81a0441-pc5`. Python 3.11.2, `unicorn` 2.1.4 from PyPI into a venv,
`Linux 6.1.158+ x86_64`, glibc 2.36. No `qemu-system-x86_64`, no OVMF image, no
`/dev/kvm`, and `apt-get` cannot install any of them (the sandbox is not root and
`/var/lib/apt/lists` is unwritable), so the 64-bit path is executed only under Unicorn.

**The open sentence.** `docs/ARCHITECTURE.md` §7.5c ends with "Loading TR on real
firmware stays open, and is recorded as open: nothing here demonstrates a double fault
running on its own stack." That is correct, and its *reason* was recorded as "executing
`ltr` raises an exception" — a sentence produced by six failed experiments, each of
which assumed something about the emulator that nothing in the tree could re-check.

This directory converts that sentence into a command:

```sh
python3 tools/emulator_capabilities.py            # text report
python3 tools/emulator_capabilities.py --json     # machine readable
```

`emulator-capabilities.txt` and `emulator-capabilities.json` are its output verbatim, at
this baseline, in this sandbox:

| measurement | Unicorn 2.1.4 | what it decides |
| --- | --- | --- |
| `int3-delivery` | yes — hook saw `[3]`, guest continued | the hook is installed correctly |
| `int7-delivery` | yes — hook saw `[7]`, guest continued | the vector reported is the vector asked for, not a constant |
| `exception-delivery` | **no** — hook saw `[]`, `UC_ERR_INSN_INVALID`, guest did not continue | a processor exception never reaches the IDT path |
| `tr-api` | yes — `TR` accepts and returns the 4-tuple `(40, 0x114000, 103, 0x89)` | a *host-seeded* TR exists, which is exactly what must not be reported as activation |
| `gdt-selfcheck` | no — GDTR reads back `limit=0 base=0x0` after a guest `lgdt` | the probe could not verify its own table; see the caveat below |
| `sgdt-without-lgdt` | yes — the same zeros with no `lgdt` executed | the zeros above are the engine's default, not a stray overwrite |
| `ltr-no-gdt` | no — `#GP`(13) then `#DF`(8) reported, `TR` still zero | the instruction is decoded and trapped, not ignored |
| `ltr-with-gdt` | no — `TR` still `[0, 0, 0, 0]` | with the descriptor the probe built, TR is still not loaded |
| `ltr-over-seeded-tr` | yes — a seeded TR survives `ltr` unchanged and untrapped | the guest's `ltr` does not write the state the host can read |

Read together: **software interrupts are modelled, processor exceptions are not, and the
guest cannot get TR loaded.** IDT dispatch of a hardware exception, the stack switch that
goes with it, and the `mov rsp, tss.ist[n]` that follows are therefore not observable on
this engine — not because PC5's TSS or IDT is wrong, and not because the harness forgot a
hook. `tr=not-loaded`, `ist-df=0`, `ist-nmi=0` remain the honest boot line, and
"double fault runs on IST1 / NMI runs on IST2" stays an OVMF-or-hardware criterion.

## The second confirmation, on the real boot path

A synthetic machine invites the objection that the *setup* is what failed. So the same
`ud2` was injected into the real kernel, at the real place in the real boot:

```sh
git archive HEAD | tar -x -C /tmp/pc5-probe           # a pristine copy; the repo is untouched
python3 - <<'PY'                                       # insert `ud2` at the top of report_tss()
import pathlib; p = pathlib.Path("/tmp/pc5-probe/kernel64/main.c"); t = p.read_text()
a = 'static void report_tss(void)\n{\n    serial64_write("PC5-64-TSS status=");'
p.write_text(t.replace(a, 'static void report_tss(void)\n{\n'
    '    serial64_write("PC5-64-PROBE-A pre-ud2\\n");\n'
    '    __asm__ volatile("ud2");\n'
    '    serial64_write("PC5-64-PROBE-A post-ud2\\n");\n'
    '    serial64_write("PC5-64-TSS status=");'))
PY
cd /tmp/pc5-probe && make kernel64 uefi64 && python3 tests/boot64_stubtest.py \
    --image build/uefi64/BOOTX64.EFI --kernel build/kernel64/KERNEL64.BIN
```

`kernel-ud2-control.log` holds the result. The probe line before the fault prints
(`PC5-64-PROBE-A pre`), the line after it does not, `PC5-64-EXCEPTION` never appears, and
the stub harness dies with `emulation faulted: Invalid instruction
(UC_ERR_INSN_INVALID) (rip=0x100d9b)`. Build exit 0, run exit 1,
`UEFI64 OK: 1474560 bytes sha256=c9cb0e6c…`. The same mutation on unmutated sources is a
clean 41/41, which is why the difference is the exception and not the image.

The handler that should have run is `kernel64/idt64.c`'s, reached through an IDT the kernel
installed and verified earlier in the same boot. It is not reached. Under a real OVMF the
`#UD` would print `PC5-64-EXCEPTION vector=6` and halt in the handler; under Unicorn the
emulator itself is the thing that stops.

## What these rows do *not* say

* **They are not a statement about PC5's TSS.** `make stubtest64` checks the TSS bytes,
  the descriptor fields, the IST arithmetic against the compiler's own
  `tss_ist_offset`, the frame accounting and the arming rules, and those gates pass. What
  is missing is the CPU consulting any of it.
* **`gdt-selfcheck=no` is a limit of this probe, not a finding about GDTR.** The probe
  could not observe its own `lgdt` taking effect, so `ltr-with-gdt` must be read as "`ltr`
  ran and TR did not change", not as "a valid descriptor would have been loaded". The
  kernel's own boot line reads GDTR back as equal to the table it installed
  (`gdt=0x129280 gdtr=0x129280`), so the readback works where it is actually load-bearing;
  a probe that asserts less than the thing under test is the correct way round anyway.
* **`tr-api=yes` makes the negative sharper, not softer.** Since a host *can* write TR, a
  test could fake activation trivially. That is why the gate requires the value to come
  from the guest's own execution and why `report_tss` refuses to arm IDT entries while TR
  does not name the TSS.
* **Nothing here is evidence about firmware or hardware.** QEMU/OVMF is not installed and
  cannot be installed in this sandbox, so every OVMF leg of `make ovmf-test` still exits 2
  with `qemu: not found`, and `make ovmf-test` keeps reporting `NOT TESTED` (exit 3).

## The bug this measurement caught in itself

The first version of this probe reported `ltr-no-gdt: no` on the strength of a GDT whose
TSS descriptor it had packed as `limit | base << 16 | …`, which is wrong: `base` is split
across bytes 2, 3, 4 and 7, so `0x114000` came out as `0x4000`. With that table, "the
engine ignores `ltr`" was a plausible reading of a measurement of nothing. `gdt_bytes()`
is now byte-exact, `decode_descriptor()` inverts it, and the self-check plus the
`sgdt-without-lgdt` control exist so that a future encoding slip shows up as a failed
self-check rather than as a new fact about emulators. The trap is generic: a probe of a
CPU feature measures the *fixture* first, and the fixture needs a control.

## What would change the conclusion

Any of these, on a machine where the tool reports them differently:

1. `exception-delivery: yes` → the stub harness can model IDT dispatch, and the IST stack
   switch becomes directly observable (`tests/boot64_stub.py` would then need a guest
   `sidt`/`sgdt`-based readback and a `PC5-64-EXCEPTION` expectation, not a new emulator).
2. `ltr-with-gdt: yes` after `gdt-selfcheck: yes` → `kernel64/tss64.c` can load TR here,
   `tr=loaded` replaces `tr=not-loaded`, and the arming rule that currently refuses can be
   exercised end to end.
3. QEMU plus OVMF, by whatever route, → `make ovmf-test` stops being `NOT TESTED` and
   `tests/ovmf_boot.py`'s existing 20-odd assertions (including the `kernel_entry eip` and
   memory-map ones) run against genuine firmware. That is the route CI would take, and CI
   still cannot be activated from here: `ci/README.md` records the `workflows` permission
   rejection, most recently at this same baseline.

Until then, the claim chain is: allocator consumers and TSS construction are executed and
gated; the routing rules are executed and gated; **activation of the routing is not, and
the reason is measured above rather than assumed.**
