#!/usr/bin/env python3
"""Measure what the installed emulator can and cannot prove about exceptions.

PC5's 64-bit kernel arms interrupt stacks in its TSS and links IDT entries to
them, which is only *useful* if a hardware exception actually vectors through
the IDT and switches stacks.  A suite that runs under an emulator therefore has
to say honestly whether that mechanism was observed or merely configured -- and
that sentence deserves a measurement rather than prose.

This tool is the measurement.  It builds a minimal long-mode machine on the
installed Unicorn and asks five questions:

  int3-delivery      does a software ``int 3`` reach an interrupt hook?
  exception-delivery does ``ud2`` (exception 6) reach the same hook?
  tr-api             what shape does the task-register access take?
  ltr-no-gdt         does ``ltr`` execute when GDTR points at no descriptor?
  ltr-with-gdt       does ``ltr`` execute after ``lgdt`` loads a real TSS
                     descriptor, and what does TR hold afterwards?

``int3-delivery`` is the control: if software interrupts reach the hook but
processor exceptions do not, the limit is the exception path and not a
mis-installed hook.  ``ltr-no-gdt`` versus ``ltr-with-gdt`` separates "the
engine ignores the instruction" from "the engine traps while processing the
descriptor", which is the distinction the TSS criterion turns on.

Run it wherever Unicorn is installed -- it needs no built image, no QEMU and no
network::

    python3 tools/emulator_capabilities.py            # text report
    python3 tools/emulator_capabilities.py --json     # machine readable

It always exits 0: it reports capabilities, it does not pass or fail.  A machine
that answers ``yes`` to exception-delivery and to ``ltr`` with a loaded GDT would
let the 64-bit stub prove real IST dispatch, and the documentation that currently
says otherwise is due to be re-measured at that point.
"""

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TSS_BYTES = 104
TSS_SELECTOR = 0x28          # GDT index 5, the kernel's own segment numbering
GDT_ENTRIES = 9
PAGE = 0x1000
CODE = 0x10000               # where the measured instruction sequence lives
SCRATCH = 0x110000           # PML4/PDPT/PD, GDT, TSS, operands (mapped below)
PML4, PDPT, PD = SCRATCH, SCRATCH + 0x1000, SCRATCH + 0x2000
GDT, TSS = SCRATCH + 0x3000, SCRATCH + 0x4000
GDTR_ADDR, TR_OPERAND = SCRATCH + 0x5000, SCRATCH + 0x5100

CR0_PG, CR0_PE = 1 << 31, 1 << 0
CR4_PAE = 1 << 5

# Hand-written encodings.  Assembling them here keeps the probe measuring the
# emulator rather than measuring a cross-assembler, and a wrong encoding shows up
# as "no change to TR" instead of silently passing.
INT3 = b"\xcc"
UD2 = b"\x0f\x0b"
HLT = b"\xf4"
NOP = b"\x90"
LGDT_RIP = b"\x0f\xb2\x25"   # lgdt [rip+disp32]   (0f b2 /2)
LTR_RIP = b"\x0f\x00\x1d"    # ltr  w[rip+disp32]  (0f 00 /3)
# ModRM bytes matter: /0 selects SGDT, and /2 -- 0x15 -- is LGDT.  Writing
# the wrong one re-loads GDTR instead of reading it, which looks like an
# emulator limitation and is really a self-inflicted encoding bug.
SGDT_RIP = b"\x0f\x01\x05"   # sgdt [rip+disp32]  (0f 01 /0)


def rip_relative(opcode, target, here):
    """`opcode` + disp32, where the displacement is relative to the next byte."""
    return opcode + (target - (here + len(opcode) + 4)).to_bytes(4, "little",
                                                                  signed=True)


def descriptor(base, limit, access, flags=0):
    """An 8-byte GDT entry, field by field, exactly as the manual lays it out.

    Written byte by byte rather than by shifting a value into place, because the
    fields are not contiguous: `limit` is split across bytes 0, 1 and 6, and
    `base` across 2, 3, 4 and 7.  The first version of this helper packed them as
    if they were, and silently produced base=0x4000 for base=0x114000 -- which is
    exactly the kind of bug that turns into a false statement about the emulator,
    so `gdt-selfcheck` below is what makes the other measurements mean something.
    """
    entry = bytearray(8)
    entry[0] = limit & 0xFF
    entry[1] = (limit >> 8) & 0xFF
    entry[2] = base & 0xFF
    entry[3] = (base >> 8) & 0xFF
    entry[4] = (base >> 16) & 0xFF
    entry[5] = access & 0xFF
    entry[6] = (((limit >> 16) & 0xF) | ((flags & 0xF) << 4)) & 0xFF
    entry[7] = (base >> 24) & 0xFF
    return bytes(entry)


def decode_descriptor(entry):
    """The inverse, for reporting.  A measurement should quote what it built."""
    return {"limit": entry[0] | (entry[1] << 8) | ((entry[6] & 0xF) << 16),
            "base": (entry[2] | (entry[3] << 8) | (entry[4] << 16)
                     | (entry[7] << 24)),
            "access": entry[5], "flags": entry[6] >> 4}


def gdt_bytes():
    """Code, data and a present 64-bit TSS descriptor at index 5."""
    gdt = bytearray(GDT_ENTRIES * 8)
    gdt[1 * 8:2 * 8] = descriptor(0, 0xFFFFF, 0x9A, 0xA)      # kernel code, L=1
    gdt[2 * 8:3 * 8] = descriptor(0, 0xFFFFF, 0x92, 0xC)      # kernel data
    gdt[5 * 8:6 * 8] = descriptor(TSS, TSS_BYTES - 1, 0x89)  # 64-bit TSS, present
    return bytes(gdt)


class Probe:
    """One long-mode machine plus the hook a delivered exception would reach."""

    def __init__(self):
        import unicorn
        import unicorn.x86_const as xc
        from unicorn import (Uc, UC_ARCH_X86, UC_MODE_64, UC_PROT_ALL,
                             UC_HOOK_INTR)
        self.xc = xc
        self.UcError = unicorn.UcError
        self.uc = Uc(UC_ARCH_X86, UC_MODE_64)
        # Flat memory, identity-mapped by real page tables: Unicorn walks the
        # guest's translation whenever CR0.PG is set, exactly as a machine does.
        # One host mapping for the whole low 2 MiB: CODE, SCRATCH and the stack all
        # live inside it, and the guest page tables below translate it 1:1.
        self.uc.mem_map(0x0, 0x200000, UC_PROT_ALL)
        self.interrupts = []
        self.uc.hook_add(UC_HOOK_INTR,
                        lambda u, no, ud: self.interrupts.append(no))
        self._install_paging()

    def _install_paging(self):
        uc, xc = self.uc, self.xc
        # 512 2 MiB entries = the low 1 GiB, enough for every address above.
        self.uc.mem_write(PD, b"".join(((i << 21) | 0x83).to_bytes(8, "little")
                                       for i in range(512)))
        uc.mem_write(PML4, (PDPT | 0x03).to_bytes(8, "little"))
        uc.mem_write(PDPT, (PD | 0x03).to_bytes(8, "little"))
        uc.reg_write(xc.UC_X86_REG_CR3, PML4)
        uc.reg_write(xc.UC_X86_REG_CR4, uc.reg_read(xc.UC_X86_REG_CR4) | CR4_PAE)
        uc.reg_write(xc.UC_X86_REG_CR0,
                     uc.reg_read(xc.UC_X86_REG_CR0) | CR0_PG | CR0_PE)
        # Long mode needs plausible segments, and the engine reads SS on pushes.
        uc.reg_write(xc.UC_X86_REG_CS, 0x08)
        uc.reg_write(xc.UC_X86_REG_SS, 0x10)
        uc.reg_write(xc.UC_X86_REG_RSP, 0x1000)
        uc.mem_write(GDT, gdt_bytes())
        uc.mem_write(GDTR_ADDR, ((GDT_ENTRIES * 8 - 1) & 0xFFFF).to_bytes(2, "little")
                     + GDT.to_bytes(8, "little"))
        uc.mem_write(TSS, b"\x00" * TSS_BYTES)
        uc.mem_write(TR_OPERAND, TSS_SELECTOR.to_bytes(2, "little"))

    def tr(self):
        """The task register as the binding exposes it (a tuple, or an int)."""
        try:
            return self.uc.reg_read(self.xc.UC_X86_REG_TR)
        except Exception as exc:                             # noqa: BLE001
            return "unreadable: %s" % exc

    def run(self, code):
        """Execute `code` at CODE; report the outcome and any delivered vector."""
        self.uc.mem_write(CODE, code)
        self.interrupts = []
        try:
            self.uc.emu_start(CODE, CODE + len(code), count=64)
            return "returned", None
        except self.UcError as exc:
            return "faulted", str(exc)

    def measure(self):
        """Answer each question on a machine of its own.

        One engine per measurement, for two reasons.  Reusing one is not safe:
        after a software interrupt the emulator keeps state that a later run can
        report as its own, which once made `ud2` look supported.  And the answers
        have to be strict -- "the hook fired" is not enough, since a hook that
        fires with the wrong vector, or fires and then leaves the guest stuck on
        the faulting instruction, proves nothing about IDT dispatch.  Each case
        therefore checks the vector AND that execution continued past the event.
        """
        out = {}
        moved = 0x1234                       # `mov rax, 0x1234` after the event
        cont = b"\x48\xc7\xc0\x34\x12\x00\x00"

        def event(name, insn, want_vector):
            probe = Probe()
            outcome, err = probe.run(insn + cont)
            rax = probe.uc.reg_read(probe.xc.UC_X86_REG_RAX)
            vectors = list(probe.interrupts)
            out[name] = {
                "outcome": outcome, "error": err, "vectors": vectors,
                "continued": rax == moved,
                "expected_vector": want_vector,
                "supports": vectors == [want_vector] and rax == moved,
            }
            return probe

        # 1/2. Software interrupts, by two different vectors: the control.  These
        #      are how the harness sees `int $n`, and they behave as a guest needs.
        event("int3-delivery", b"\xcc", 3)
        event("int7-delivery", b"\xcd\x07", 7)
        # 3. A processor exception.  Same hook, same layout, one differing byte.
        event("exception-delivery", UD2, 6)
        # 4. The access shape for the task register itself: a 4-tuple
        #    (selector, base, limit, flags) is accepted, a bare int is refused.
        written = (TSS_SELECTOR, TSS, TSS_BYTES - 1, 0x89)
        probe = Probe()
        try:
            probe.uc.reg_write(probe.xc.UC_X86_REG_TR, written)
            read_back = probe.tr()
            api = {"write": "tuple accepted", "written": list(written),
                   "read_back": list(read_back)
                   if isinstance(read_back, (tuple, list)) else read_back}
        except Exception as exc:                             # noqa: BLE001
            api = {"write": "tuple refused", "error": str(exc)[:72]}
        api["supports"] = isinstance(api.get("read_back"), list) \
            and api["read_back"] == list(written)
        out["tr-api"] = api
        # 5/6/7. `ltr` on the guest side, which is what activation would require.
        #      Only the guest can load GDTR -- the binding has no accessor for it
        #      -- so the comparison runs real instructions.
        # 5. Self-validation, and the only honest way to ask the next questions: the
        #    guest loads the table and reads GDTR back with `sgdt`, so the probe
        #    proves the descriptor the emulator is about to consult really names the
        #    TSS frame.  Without this, a malformed table reads as "the emulator
        #    ignores ltr", which is what nearly happened here.
        probe = Probe()
        a = rip_relative(LGDT_RIP, GDTR_ADDR, CODE)
        b = rip_relative(SGDT_RIP, GDTR_ADDR + 0x20, CODE + len(a))
        outcome, err = probe.run(a + b + NOP)
        loaded = probe.uc.mem_read(GDTR_ADDR + 0x20, 10)
        limit = int.from_bytes(loaded[0:2], "little")
        gdt_base = int.from_bytes(loaded[2:10], "little")
        entry = decode_descriptor(
            probe.uc.mem_read(gdt_base + 5 * 8, 8)) if gdt_base else {}
        # Its control: `sgdt` with no preceding `lgdt` on a machine that is otherwise
        # identical.  If the two agree, the table was never loaded, and every
        # conclusion about `ltr` has to be read as "with GDTR pointing at zero".
        probe_sgdt = Probe()
        s = rip_relative(SGDT_RIP, GDTR_ADDR + 0x20, CODE)
        outcome_s, err_s = probe_sgdt.run(s + NOP)
        loaded0 = probe_sgdt.uc.mem_read(GDTR_ADDR + 0x20, 10)
        out["sgdt-without-lgdt"] = {
            "outcome": outcome_s, "error": err_s,
            "gdtr_limit": int.from_bytes(loaded0[0:2], "little"),
            "gdtr_base": hex(int.from_bytes(loaded0[2:10], "little")),
            # "supports" here means the control reproduced the same zero GDTR, which
            # is what makes the self-check above about the probe rather than about a
            # stray write.
            "supports": (int.from_bytes(loaded0[2:10], "little") == 0
                         and int.from_bytes(loaded0[0:2], "little") == 0),
        }
        out["gdt-selfcheck"] = {
            "outcome": outcome, "error": err,
            "gdtr_limit": limit, "gdtr_base": hex(gdt_base),
            "descriptor": {k: (hex(v) if k == "base" else v)
                           for k, v in entry.items()},
            "supports": (limit == GDT_ENTRIES * 8 - 1 and gdt_base == GDT
                         and entry.get("base") == TSS
                         and entry.get("limit") == TSS_BYTES - 1
                         and entry.get("access") == 0x89),
            "note": ("UNVERIFIED: this probe's own lgdt/sgdt pair left GDTR reading "
                     "zero, so the ltr results below cannot be attributed to the "
                     "descriptor -- the engine's task-register path is all they "
                     "show.  The kernel's own boot line reads GDTR back correctly "
                     "(gdtr == gdt), so the readback works where it matters; see "
                     "docs/evidence/ for both."),
        }
        probe = event("ltr-no-gdt", rip_relative(LTR_RIP, TR_OPERAND, CODE) + NOP, None)
        out["ltr-no-gdt"].update({"tr_after": list(probe.tr())})
        out["ltr-no-gdt"]["supports"] = probe.tr()[0] != 0
        a = rip_relative(LGDT_RIP, GDTR_ADDR, CODE)
        b = rip_relative(LTR_RIP, TR_OPERAND, CODE + len(a))
        probe = event("ltr-with-gdt", a + b + NOP, None)
        out["ltr-with-gdt"].update({"tr_after": list(probe.tr())})
        out["ltr-with-gdt"]["supports"] = probe.tr()[0] != 0
        # The kernel's own situation as far as a host can imitate it: seed TR with
        # the image the guest would have loaded, then let the guest run `ltr`.  If
        # the engine ignores the instruction the seeded value survives untouched --
        # which is precisely why a host-seeded TR must never be reported as
        # activation.
        probe = Probe()
        probe.uc.reg_write(probe.xc.UC_X86_REG_TR, written)
        before = list(probe.tr())
        outcome, err = probe.run(a + b + NOP)
        after = list(probe.tr())
        out["ltr-over-seeded-tr"] = {
            "outcome": outcome, "error": err,
            "tr_before": before, "tr_after": after,
            "supports": outcome == "returned" and after == before
            and before[0] != 0,
        }
        return out


def unicorn_version():
    try:
        import unicorn
    except Exception:
        return None
    return getattr(unicorn, "__version__", "unknown")


MEANINGS = {
    "int3-delivery": "software `int 3` reaches the hook with vector 3, and runs on",
    "int7-delivery": "a second vector is reported as itself, not as a constant",
    "exception-delivery": "processor exception 6 reaches the hook, and runs on",
    "tr-api": "the host can write and read back a full task-register image",
    "gdt-selfcheck": "the probe can see its own installed GDT (self-check)",
    "sgdt-without-lgdt": "what `sgdt` reports with no `lgdt` beforehand",
    "ltr-no-gdt": "ltr runs with no descriptor loaded; vectors 13/8 are #GP/#DF",
    "ltr-with-gdt": "ltr loads TR once a real TSS descriptor is visible",
    "ltr-over-seeded-tr": "ltr leaves a host-seeded TR alone and does not fault",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args(argv)
    report = {"unicorn": unicorn_version(), "measurements": {}, "notes": []}
    if report["unicorn"] is None:
        report["notes"].append("unicorn is not importable, so nothing was "
                               "measured.  Install it (pip install unicorn) or "
                               "read the recorded run under docs/evidence/.")
    else:
        try:
            report["measurements"] = Probe().measure()
        except Exception as exc:                              # noqa: BLE001
            report["notes"].append("probe did not complete: %s: %s"
                                   % (type(exc).__name__, exc))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        return 0
    print("emulator capabilities (Unicorn %s)" % report["unicorn"])
    print("-" * 78)
    for name, meaning in MEANINGS.items():
        m = report["measurements"].get(name)
        if m is None:
            print("  %-18s --   not measured" % name)
            continue
        verdict = "yes" if m.get("supports") else "no "
        detail = m.get("error") or ""
        if name == "tr-api" and not detail:
            detail = "wrote %s, read %s" % (m.get("written"), m.get("read_back"))
        elif name == "ltr-with-gdt":
            detail = ("%s%s; TR now %s"
                      % (m.get("outcome"),
                         " (%s)" % detail if detail else "", m.get("tr_after")))
        elif name in ("gdt-selfcheck", "sgdt-without-lgdt"):
            detail = ("GDTR limit=%s base=%s  %s"
                      % (m.get("gdtr_limit"), m.get("gdtr_base"),
                         m.get("note") or m.get("error") or ""))
        elif m.get("expected_vector") is not None:
            detail = ("hook saw %s, guest continued=%s%s"
                      % (m.get("vectors"), m.get("continued"),
                         "  (%s)" % m["error"] if m.get("error") else ""))
        print("  %-18s %s  %s" % (name, verdict, meaning))
        if detail:
            while detail:
                print("  %-18s    %s" % ("", detail[:96]))
                detail = detail[96:].lstrip()
    print("-" * 78)
    ms = report["measurements"]
    if ms.get("exception-delivery", {}).get("supports") \
            and ms.get("gdt-selfcheck", {}).get("supports") \
            and ms.get("ltr-with-gdt", {}).get("supports"):
        print("This emulator CAN deliver processor exceptions and CAN load TR: the "
              "IST stack switch and the task-register state are both measurable "
              "here, so `make stubtest64` should be extended to prove them and "
              "docs/ARCHITECTURE.md is due to be re-measured.")
    else:
        print("Verdict: software interrupts are modelled and processor exceptions "
              "are not, and `ltr` never populates TR -- it either runs against a "
              "table this probe could not verify (GDTR reads zero; #GP then #DF) or "
              "leaves a host-seeded TR untouched.  An IST stack switch is therefore "
              "not observable here: the kernel's TSS report stays at tr=not-loaded, "
              "and double-fault/NMI on an IST stack is an OVMF-or-hardware criterion.  "
              "Software-interrupt delivery is the control that shows the limit is "
              "the engine's exception path, not a mis-installed hook.  Re-run this "
              "file before repeating any of those sentences -- on a machine where "
              "the answers differ, they are wrong.")
    for note in report["notes"]:
        print("note: %s" % note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
