# PC5 architecture — as implemented

> **Scope.** This document describes the code that exists: the boot chain, the
> kernel and the host tools. It is not the product architecture — that is
> [`architecture/PC5_ARCHITECTURE_SPEC_v2.md`](architecture/PC5_ARCHITECTURE_SPEC_v2.md),
> where PC5 is one platform whose destination is genuine PS5 system software on
> PC hardware. Read this page as the map of the current implementation.

## 1. Boot chain as implemented today

```
 firmware (BIOS/SeaBIOS)
   │  two paths, one boot image (ADR-014):
   │    El Torito no-emulation entry written by tools/mkiso.py
   │      -> firmware copies the 4096-byte image to 07C0:0000 and jumps
   │    hybrid MBR in the ISO9660 system area (sector 0 of the image)
   │      -> boot/mbr.S (440 bytes) reads that same image with INT 13h
   │         extended read into 0000:7C00 and jumps there with DL intact
   ▼
 boot/loader.S         real mode, 4096 bytes, loaded at 07C0:0000
   ├─ COM1 serial console (115200 8N1) + failure codes
   ├─ INT 15h E820 memory map            → 0x2000
   ├─ INT 10h 1130h firmware 8x16 font   → 0x2900
   ├─ VBE 4F00/4F01/4F02 linear mode     → 0x2800  (text mode fallback)
   ├─ INT 13h read of ISO9660 sector 16  → 0x3A00  (proves the medium reads,
   │                                                and detects 2048 vs 512
   │                                                byte disk units)
   ├─ INT 13h read of the kernel image   → 0x10000 (signature "PC5K" checked)
   ├─ struct pc5_boot_info               → 0x4000
   └─ GDT + CR0.PE, 32-bit far jump      → 0x10000 with EBX = 0x4000
   ▼
 kernel/start.S        identity flat 32-bit entry, .bss cleared, IDT installed
   ▼
 kernel/main.c         console → timer → CPUID → E820 → PCI → SMBIOS → ACPI
                       → firmware probe → storage (ATAPI + ISO9660 self-test
                       → partition scan, read-only)
                       → keyboard → chain → interface
```

Fixed low-memory contract (both `boot/loader.S` and `kernel/include/pc5.h`):

| Address | Contents |
|---|---|
| `0x2000` | E820 entries (up to 40 × 24 bytes) |
| `0x2500` | VBE controller information |
| `0x2600` | copied VBE mode list |
| `0x2800` | VBE mode information block (framebuffer address/geometry) |
| `0x2900` | 256-glyph 8×16 font copied from the video BIOS |
| `0x3A00` | ISO9660 primary volume descriptor |
| `0x4000` | `struct pc5_boot_info` |
| `0x4400` | disk address packet |
| `0x10000` | kernel image (limit `0x8F000`) |
| `0x9F000` | stack top |

`_Static_assert`s in `kernel/include/pc5.h` pin the struct offsets so the
kernel and the loader cannot drift apart silently.

## 2. Kernel modules

| File | Responsibility |
|---|---|
| `kernel/start.S` | entry stub, `.bss` clear, protected-mode continuation, IDT with 32 real exception gates |
| `kernel/main.c` | boot order, evidence log, chain evaluation, hand-off to the UI |
| `kernel/console.c` | linear-framebuffer console (firmware font), VGA text fallback, shadow character grid, framebuffer read-back self-test, panic |
| `kernel/serial.c` | 16550 polling driver on COM1 |
| `kernel/lib.c` | freestanding string/memory/formatting (`pc5_snprintf` is the only formatter in the tree) |
| `kernel/cpu.c` | CPUID: vendor, brand, family/model, logical CPUs, feature bits, long-mode |
| `kernel/mem.c` | E820 accounting (usable, addressable, top of memory) |
| `kernel/pci.c` | configuration mechanism #1 enumeration and classification |
| `kernel/acpi.c` | RSDP discovery (EBDA + BIOS area), RSDT walk, table signatures |
| `kernel/smbios.c` | `_SM_`/`_SM3_` anchor, structure walk (BIOS, system, board, CPU, DIMMs) |
| `kernel/ata.c` | legacy ATA/ATAPI PIO driver: LBA28 512-byte sector read/write for disks, packet reads on 2048-byte blocks for optical media |
| `kernel/block.c` | block-request rules with no port I/O, so the host tests can prove them |
| `kernel/part.c` | MBR/GPT parsers (pure) and a read-only, explicit-device scan |
| `kernel/fat32.c` | FAT32: BPB validation, FAT chains, directory traversal, 8.3 lookup and case-insensitive path resolution, file read; three write operations (create, overwrite-in-place, mkdir) sharing one discipline — plan and validate the whole allocation in memory, build in unreferenced clusters, write every FAT copy and re-read it, flush, one directory-entry write, flush, read back through the name, then reclaim the replaced chain |
| `kernel/sha256.c` | SHA-256 for write verification (and, later, update manifests) |
| `kernel/storage_test.c` | explicit `wtest` write/read-back self-test on a reserved window |
| `kernel/iso9660.c` | ECMA-119 volume mount, root directory walk, file read on top of `ata.c` |
| `kernel/kbd.c` | 8042 PS/2 keyboard, polled, scan-code set 1 translation, E0 handling |
| `kernel/timer.c` | PIT calibration against the TSC; millisecond timeouts and uptime |
| `kernel/chain.c` | the 13-stage PS5 compatibility chain and its evidence strings |
| `kernel/fw.c` | firmware probe (manifest presence), never a claim of execution |
| `kernel/ui.c` | six pages, controller/keyboard navigation, serial recovery console, audit log |

The kernel is deliberately small (about 65 KB in the 0.3 line, of which the filesystem
is the largest single module) and freestanding: no libc, no
allocator, no paging, no interrupts beyond the IDT gates. Everything is
polled, which keeps the boot deterministic and makes failures reproducible.

## 3. Host tooling

| Tool | Purpose |
|---|---|
| `boot/mbr.S` | 440-byte hybrid MBR bootstrap: relay at 0000:0500, INT 13h extended read of the boot image, hand-off at 0000:7C00 |
| `tools/mkiso.py` | ISO9660 (ECMA-119) + El Torito writer plus the hybrid MBR in the system area, byte-exact control of the boot descriptor, deterministic layout |
| `tools/verify_iso.py` | independent verifier: system-area MBR (signature, one entry, type/flag/extent, CHS, patch words), volume descriptors, catalog checksum, boot entry, descriptor CRC, kernel signature, per-file SHA-256 |
| `tools/firmware.py` | firmware container identification, entropy profile, manifest generation — no decryption |
| `tools/pc5ctl.py` | operator CLI: `info`, `verify`, `boot`, `chain`, `fw`, `usb` |
| `tests/v86_runner.mjs` | boots an image in v86, captures serial and the VGA text screen, injects serial/PS2 input |
| `tests/boot_test.py` | asserts boot markers and the rendered interface, writes `build/test/boot-evidence.json` |
| `tests/kernel_unit.c` | host-side unit tests for the kernel's pure logic, including the block rules and SHA-256 vectors |
| `tests/test_storage.py` | contracts for the write test, its scratch window and harness safety |
| `tests/test_partitions.py` | fixtures and contracts for partition discovery |
| `tests/disk_images.py` | deterministic MBR/GPT disk fixtures used by the boot test |
| `tests/fat32_images.py` | deterministic FAT32 fixture, an independent FAT32 reader, and structural checks (FAT copies, chains, orphans, FSInfo, changed sectors) |
| `tests/fat32_check.c` | host driver that runs `kernel/fat32.c` against a real image |
| `tests/fat32_write_check.c` | host driver for the create, overwrite, mkdir and read paths, with write/flush/copy-targeted fault injection and an LBA log of every write |
| `tests/test_fat32.py` | three-way digest comparison and refusal contracts |
| `tests/test_fat32_write.py` | creation matrix, refusals, FSInfo and flush behaviour, fault-injection classification |
| `tests/test_fat32_expand.py` | overwrite, directory creation, path handling, integrity invariants and a per-write failure sweep that classifies what each failure left behind |
| `tests/test_hybrid.py` | the assembled MBR bootstrap byte by byte, the layout it produces, and one rejection test per way the table can lie about the image |
| `tests/mbr_fixture.py` | synthetic and really-assembled bootstrap fixtures shared by the unit tests |
| `tests/test_tools.py` | unit tests for the ISO writer, verifier and firmware tool |
| `tests/uefi_stub_firmware.py` | executes the real `BOOTX64.EFI` on the Unicorn CPU emulator against a stub firmware (protocols at their specified slots, two file-system volumes); emulates `lgdt`/segment loads/`lretq` |
| `tests/uefi_stubtest.py` | asserts 42 properties of that run, plus two negative runs; `make stubtest` |

## 4. Interfaces that the next stages plug into

* **Display**: `console_init()` accepts any boot info with a VBE mode block;
  a GOP-based mode can be supplied by a future UEFI loader without touching the
  console.
* **Input**: `kbd_read()` is the only input source in the UI; a USB HID or
  DualSense translator is a second source behind the same interface.
* **Storage**: two interfaces with different units, deliberately (ADR-013).
  `ata_read_blocks()` reads 2048-byte ISO9660 blocks from the selected boot
  device and is what `iso_read_file()` uses; `ata_read_sectors()` and
  `ata_write_sectors()` move 512-byte sectors on an explicitly indexed ATA disk
  and are what a filesystem, partition parser or installer will use. AHCI, NVMe
  and USB storage implement the same sector contract behind the same rules
  (`kernel/block.c` validates every request).
* **Filesystem**: `kernel/fat32.c` talks to a disk only through `struct
  fat32_io` — a `read` callback, an optional `write` callback and an optional
  `flush` callback, each `(ctx, lba, count, buf)`. The mount made during boot
  attaches a read callback and nothing else, so the boot path cannot write even
  by mistake; `mounted_write_io()` is the one place a write callback is attached,
  and only the explicit console commands reach it. Every write entry point
  (`fat32_create_file`, `fat32_overwrite_file`, `fat32_create_dir`) is a function
  of that interface alone, which is why the host driver can run the real module
  against an in-memory image with fault injection and no emulator.
* **Firmware**: `fw_probe()` consumes a manifest compiled into the kernel; the
  manifest is produced by `tools/firmware.py` from a user-supplied image.
* **Compatibility chain**: `chain_evaluate()` takes one argument per subsystem,
  so a new subsystem adds a stage without rewriting the reporting.

## 5. The UEFI boot path

The ISO carries two El Torito entries, so one medium boots on either kind of
firmware:

```
catalog +32   default entry  platform 0x00 (80x86)  -> boot/loader.S (BIOS)
catalog +64   section 0x91   platform 0xEF (UEFI)   -> build/efi.img
catalog +96   the UEFI entry                        -> \EFI\BOOT\BOOTX64.EFI
```

`boot/uefi/` is a freestanding PE32+ EFI application, cross-linked by binutils'
`i386pep` emulation with `--enable-reloc-section`. No EDK2, no mingw: the same
gcc and binutils the kernel uses. `bootx64.S` supplies the two things a C
compiler will not: the ms_abi entry frame (firmware calls `efi_main` with
ImageHandle in RCX and SystemTable in RDX, and PE images arrive with `.bss`
uninitialised) and the handover trampoline.

The handover order in that trampoline is the part that has to be exactly right:
in 64-bit mode CR0.PG cannot be cleared, so the CPU leaves long mode with a far
return into a 32-bit compatibility segment, and only then is paging switched
off before the flat 32-bit GDT is loaded and the kernel is entered at `0x10000`
with EBX = `0x4000`, which is what `boot/loader.S` does from real mode.

What the loader reports comes from firmware and is labelled as such:

| Field | UEFI source | Difference from the BIOS path |
|---|---|---|
| `e820_addr/count` | UEFI memory map, converted (conventional memory → type 1, everything else → type 2) | loader data is *not* reported as usable |
| `vbe_mode_addr`, `vbe_ok` | a synthetic VBE block describing the GOP framebuffer (32 bpp, direct colour) | GOP format 1 (BGR) is reported honestly; the kernel writes RGB order, so channels swap |
| `font_addr` | always 0 | firmware hands over no VGA font, so the kernel uses its text-mode fallback |
| `pvd_ok`, `volume_id`, `kernel_lba`, `iso_sectors` | 0 / empty / 0 / 0 | the file protocol does not expose the ISO9660 descriptor or a file's LBA; `flags` bits 1 and 2 say so, and the kernel reads the descriptor itself when it probes storage |
| `boot_drive` | `0xFFFFFFFF` | there is no BIOS drive on this path |

Everything about that handover that can be checked without firmware is checked:
`tools/eficheck.py` validates the PE32+ image (machine, subsystem, entry point,
base relocations, no imports), `tools/mkefiimg.py` writes and re-reads the FAT
ESP, and `tools/verify_iso.py` walks the ESP out of the finished ISO and
confirms a PE32+ EFI application sits at `\EFI\BOOT\BOOTX64.EFI`.

The handover is also *executed*: `tests/uefi_stub_firmware.py` runs the real
`BOOTX64.EFI` on the Unicorn CPU emulator, with firmware replaced by a stub that
answers Simple Text Output, GOP, Boot Services, Loaded Image, Device Path and a
two-volume Simple File System at the slots the specification assigns, and
`tests/uefi_stubtest.py` (58 checks, `make stubtest`) asserts the trace, the
boot-info block, the VBE block, the E820 conversion and merging, the handover
window against the map, `ExitBootServices` and its retry policy, the watchdog,
the read-back of the kernel copy, the GDT and the far jump. Because that stub is not firmware — no ACPI, no PCI, no
interrupts, and `lgdt`/segment loads/`lretq` emulated by the harness — a stub run
proves the loader's logic and the handover contract, not UEFI compatibility.

The firmware side is proved separately by `make ovmf-test`, which boots the ISO
under genuine TianoCore OVMF in QEMU, cold and warm, and prints
`PC5-OVMF-BOOT-OK` from the harness after 40 checks (1 NOT APPLICABLE) — see
`docs/TEST_RESULTS.md` §16. That gate now also cross-checks the kernel's own
memory report against the loader's count, asserts the Secure Boot policy refuses
an unsigned image, runs a low-memory negative case and emits a 22-row required
matrix (`§18`). Physical UEFI hardware is still untested.

Memory ownership at the handover is a checked property, not an assumption: the
loader validates its whole `[0x2000, 0x9F000)` window against the map before it
calls `ExitBootServices` (`E15`), merges descriptors instead of truncating them
(`E16`), and reads the kernel copy back before jumping (`E17`).

## 6. Why a Linux foundation is not in this build

No Linux kernel source or binary could be *built or booted* here (apt is
unreachable, the Kconfig prerequisites and a QEMU/KVM vehicle are absent, and
kernel.org is blocked — though `codeload.github.com` can serve the source), so a
Linux-based PC5 runtime could not be built or tested. ADR-009 in
`docs/TECHNICAL_DECISIONS.md` records Linux as the accepted foundation for PC5
Native and the freestanding kernel as the recovery environment; the constraint is
execution, not direction. The bring-up kernel is therefore the whole
runtime, and it establishes the hardware-inventory and reporting layer that a
future Linux image would reuse. See `docs/KNOWN_LIMITATIONS.md` and
`docs/ROADMAP.md`.

## 7. The 64-bit foundation (experimental)

Everything in sections 1–5 boots a **32-bit** kernel. That is not an accident of
history that a compiler flag can fix: `boot/uefi/bootx64.S` leaves long mode with
a far return into a 32-bit compatibility segment, disables paging and enters a
flat 32-bit protected-mode kernel. Nothing in that sequence is a 64-bit kernel,
and turning `-m32` into `-m64` on it would produce an image that cannot run.

`boot/uefi64/` and `kernel64/` are a second, separate path built to answer that
honestly. It is **experimental**: it is not part of `make iso`, the release ESP
does not carry it, and `make -n all` shows no 64-bit work.

### 7.1 Boot sequence

1. Firmware loads `\EFI\BOOT\BOOTX64.EFI` (PE32+, `boot/uefi64/bootx64.S`) and
   calls it in long mode, ms_abi, with `RCX` = ImageHandle and `RDX` =
   SystemTable. The entry stub zeroes `.bss` (NOLOAD, so firmware does not) and
   calls `efi_main64`.
2. The loader opens COM1 directly and prints `PC5-64-LOADER-BANNER`. No console
   protocol is involved: the evidence has to survive ExitBootServices.
3. It reads `\KERNEL64.BIN` from the ESP through SimpleFileSystem, taking the
   size from `EFI_FILE_INFO`, and allocates **exactly** the kernel's link
   address (`0x100000`) with `EFI_ALLOCATE_ADDRESS`. A loader and kernel built
   from different trees fail here instead of jumping into nonsense.
4. GOP and the ACPI RSDP are recorded; the memory map is copied into
   `struct pc5_memdesc64[]`, dropping the spare zeroed descriptor firmware adds.
5. PC5 builds its own page tables and calls `ExitBootServices` with the map key,
   retrying up to eight times when firmware invalidates the key. Only after a
   successful exit does it install `CR3`.
6. Before touching `CR3` it asks firmware where this application was loaded
   (`EFI_LOADED_IMAGE_PROTOCOL`) and refuses to continue if the image is outside
   the region it is about to map: `PC5-64-LOADER-REJECT loader-image=…` then
   `PC5-64-LOADER-FAIL=above-identity-map`. Every PC5-owned buffer (boot info,
   memory map copy, page tables, stack) is asserted to be inside that region too.
7. `pc5_enter_kernel64` (assembly, `boot/uefi64/bootx64.S`) saves the caller's
   `RFLAGS` and `CR3`, masks interrupts, writes `CR3`, **reads it back and
   compares**, and only then loads `RSP` and jumps — **in long mode, with no mode
   switch anywhere**. A write that does not take effect restores firmware's root
   and returns −1, which the loader reports as `PC5-64-LOADER-FAIL=cr3-not-installed`.
   It is assembly on purpose: "no loader code runs on the new map" is then a
   property of the instruction sequence, not a comment on a C function.

### 7.2 Page tables

`boot/uefi64/pagetables.c` builds an identity map below 4 GiB from 2 MiB pages:
one PML4, one PDPT and four PDs, six pages in all. A PDPT entry is consumed by a
page-directory *pointer*, and one page directory holds 512 entries of 2 MiB — one
gigabyte — so the span needs **four** PDPT entries, one per PD page, not one. An
earlier version installed only `PDPT[0]`, which mapped the first gigabyte and left
the other three PD pages unreachable while the builder still reported 2048 mapped
entries (corrected in `ed9c6a3`; see `TEST_RESULTS.md` §27). All six pages are
zeroed before use, so no firmware value survives inside an active structure.

2 MiB pages are used because every x86-64 CPU that can enter long mode supports
them; 1 GiB pages are only reported by CPUID, not required. The framebuffer's
pages are marked PWT|PCD so they are uncached. Firmware's tables are abandoned
with firmware's stack.

`PC5-64-PAGING enabled=1 root=0x…` is printed by the *kernel*, from its own
`CR3`, and the kernel fails the boot when that value differs from the page-table
address in the boot info (`pagetable-root-mismatch`). The loader's own plan is
printed before the switch (`PC5-64-LOADER cr3-plan=…`), so the stub harness can
check the two agree — a read-back performed by the kernel *on* the new map is
stronger evidence than the loader checking its own write.

The map has a hard edge, and the code says so rather than clipping quietly:

- `pc5_pt_range_supported(start, size)` is overflow-free and answers whether a
  range is inside the 4 GiB the map can describe at all;
- `pc5_pt_mark_uncached()` clips to the span, refuses entries beyond
  `PC5_PT_MAX_INDEX` (2047), skips entries already uncached, and returns the number
  of entries it actually changed — so a framebuffer at or above 4 GiB can no longer
  write past the six-page block into whatever follows it in memory;
- a resource that cannot be mapped is *recorded* as unmapped (the loader zeroes the
  address and sets `PC5_BOOT64_F_UNMAPPED_FRAMEBUFFER` / `..._RSDP`) instead of
  handing over an address the kernel would dereference and fault on.

`tests/test_pagetables64.py` builds the real `pagetables.c` as a host library with
canary pages on both sides of the six-page block and covers: entirely below 4 GiB,
ending exactly at 4 GiB, crossing it, entirely above, unaligned starts and ends,
empty and inverted ranges, ranges that overflow 64-bit arithmetic, and an invalid
page-table base.

It also walks the installed hierarchy rather than reading the leaf array, because
those are not the same question: `IdentityHierarchyTests` asserts that the
returned count equals what the PML4 → PDPT → PD walk actually reaches, that every
PDPT entry points at its own PD page, that translation succeeds immediately below,
at and above each 1 GiB boundary and fails at the 4 GiB exclusive edge, and that
removing one PDPT link makes `pc5_pt_lookup()` stop translating even though the
leaf is still populated.

### 7.3 Boot protocol, version 2

`struct pc5_boot64` (`kernel64/include/pc5_boot64.h`) is **160 bytes**, with
`magic` "PC5B", `version` = 2, `size` = 160, `flags`, a descriptor array
(`memmap_addr`, `memmap_bytes`, `memmap_desc_size`, `memmap_desc_version`), the
framebuffer (address, width, height, pitch, format), the RSDP, the kernel base and
size, the stack (`stack_top`, `stack_size`), the page tables (`pagetable_addr`,
`pagetable_pages`, `identity_span`), the loader's own image
(`loader_image_addr`, `loader_image_size`), an `exit_boot_services` flag and a
timestamp. Offsets are pinned by `_Static_assert` in `kernel64/main.c` **and** in
`boot/uefi64/uefi64_main.c` (the assembly handoff loads `stack_top` from offset 88,
so a layout change must break the build rather than the jump), and checked from
Python by `tests/test_kernel64.py`, which compiles the same header on the host.

Version 1 was 112 bytes and described none of the last three groups. A loader that
still emits it is refused with `PC5-64BIT-FAIL=bootinfo-version`; the kernel accepts
exactly the version it was compiled for and has no "unknown fields, hope for the
best" path.

What the kernel establishes before using anything (in this order):

| Stage | Established |
|---|---|
| structure | the structure's own address does not wrap, is 8-byte aligned, lies inside the identity span and passes the header's magic/version/size/stride checks |
| memory map | the map is non-empty, its byte count is a multiple of the stride, fits in `MEMMAP_MAX_BYTES`, every descriptor is self-consistent (nonzero page count, no wrap at `physical_start + page_count·4096`, a known type), **and the set is validated as a set**: no two descriptors may claim the same physical bytes. Overlap — partial, nested, duplicate, or across conflicting types — is refused (`bootinfo-memmap-overlap`) rather than resolved by picking whichever descriptor is convenient, and this happens before any range is checked against the map |
| mandatory ranges | kernel image (exactly the linked size, at the link address), stack (page-aligned top, sane size, no underflow), page tables (aligned, 3…514 pages, no overflow, and `identity_span == (pages − 2)·512·2 MiB`), the loader's own image, and the memory-map buffer are each inside the span **and** covered by memory of an acceptable type |
| environment | `CR0.PG`, `CR4.PAE`, `CR3` equals `pagetable_addr`, 64-bit operand size and arithmetic really work, `RSP` is inside the declared stack and 16-byte aligned, and CPUID reports long mode; the CPU's physical address width is checked when CPUID reports one |
| frame pool | the map is turned into a bitmap the kernel can allocate from: only `EfiConventionalMemory` inside the identity span, with the kernel image, the stack, the page tables, the boot info, the map buffer, the loader's image and the zero page removed from it; a map the bitmap cannot describe is refused rather than managed partially |
| optional resources | framebuffer and RSDP are validated (geometry, no overflow, inside the span, memory type, `"RSD PTR "` signature for the RSDP). The framebuffer's pixel format must be one of the two direct-colour layouts the protocol can describe; a bit-mask layout or `PixelBltOnly` is classified unusable rather than interpreted. A resource that fails is reported as `usability=unsupported reason=…`; it is **never** dereferenced and never called usable |

Memory types are a contract, not a guess: the loader's own ranges accept
LoaderCode/LoaderData/BootServicesCode/BootServicesData/RuntimeServicesData **and
Conventional** (firmware is not obliged to retype pages it just handed out, so
demanding Conventional, or demanding *not* Conventional, would be wrong in one
direction or the other); the framebuffer accepts only MMIO/MMIO-port/LoaderData/
BootServicesData; the RSDP accepts ACPI-reclaim/NVS/MMIO/Reserved/loader and
boot-services types plus a verified signature.

### 7.3a Where the kernel's own stack comes from

`kernel64/start.S` starts on the image's `.bss` stack, not on the loader's:
taking `RSP` from an unvalidated `stack_top` means the very first `push` can fault,
and the check that would have reported it never runs. Once the boot info has been
validated, `pc5_adopt_stack()` switches to the loader's stack and continues in a
fresh frame there; `PC5-64-STACK rsp=…` is printed *from that stack*, so the line is
evidence that the switch happened. A broken `stack_top` is therefore refused
(`bootinfo-stack*`) rather than executed.

### 7.4 What the kernel proves before it says anything good

`kernel64/main.c` prints `PC5-64BIT-LONG-MODE-OK` only after all of:

| Check | Evidence line |
|---|---|
| entered in 64-bit code | `PC5-64BIT-KERNEL-ENTRY` (from the kernel's own entry stub) |
| memory map parsed and descriptors consistent | `PC5-64-MAP entries=… conventional_pages=…` |
| kernel image range validated | `PC5-64-IMAGE base=… size=… range=ok` |
| loader's own image validated | `PC5-64-LOADER image=… size=… range=ok` |
| boot info valid and consistent | `PC5-64-BOOTINFO magic=ok version=2 size=160 memdesc=32 …` |
| paging enabled, PAE on, CR3 page-aligned and equal to `pagetable_addr` | `PC5-64-PAGING enabled=1 root=0x…` |
| 64-bit operand size really active | `PC5-64-REGS wide-operands=ok arithmetic=ok` |
| stack adopted from the loader, 16-byte aligned, inside the map | `PC5-64-STACK rsp=0x… top=0x… size=… aligned=16 range=ok` |
| optional resources classified | `PC5-64-FB … usability=ok|unsupported reason=…|absent`, `PC5-64-RSDP …` |
| CPU feature report collected | `PC5-64-CPU vendor=…`, `phys_bits`, `nx`, `svm_advertised`, … |

`EFER.LMA` is printed when the environment reports it; when an emulator returns
zero for the MSR the kernel says so (`efer.lma unavailable`) and relies on the
architectural checks instead. A string printed by a 32-bit component never
counts, and the marker is never printed by the loader.

### 7.5 Memory foundation: what exists and what does not

Exists: a page-table builder with unit tests, the L4/L3/L2 split, uncached
framebuffer marking, an ownership protocol, a validated boot-info structure, a
physical memory map the kernel validates as a set, and a frame pool over that map
(`mem64.c`, §7.5a) that hands out only conventional memory below the identity span —
with no consumer inside the kernel yet, which is what makes it safe rather than useful.

Does not exist: a *consumer* of the frame pool (no subsystem allocates a page yet),
a virtual-memory allocator, per-process address spaces, page-level
protection, guard pages, NX use (reported by CPUID, not yet set in EFER), any
mapping above 4 GiB, or any DMA protocol. No process-level protection is
claimed, because none has been implemented.

Nothing above 4 GiB is mapped, and nothing pretends to be: a framebuffer or RSDP
above the span arrives as an explicit "unmapped" flag with a zero address, and an
application that firmware placed above the span is refused before `CR3` changes.
Widening the map is future work, not a silent behaviour.

### 7.5a The frame pool: what it manages, and every way it refuses

`kernel64/mem64.c` turns the handover map into a first-fit page-frame pool: one bit per
4 KiB frame, set means *not available*. Everything about it is a refusal, because a
kernel this early cannot recover from a wrong grant:

  * the pool begins **all-claimed** and only what the map proves is conventional is
    opened up; filling it the other way round would hand out any region a map failed to
    mention;
  * a conventional region that reaches past `identity_span` contributes only the pages
    below it — a frame above the map the kernel is running on faults instead of working;
  * if the map reaches past what the bitmap can describe, init **fails** with
    `map-above-bitmap-cap` rather than forgetting the frames above the cap: a pool that
    silently ignored the top of RAM would report it as unavailable, and the kernel would
    believe the machine had less memory than firmware said it had. The kernel's own
    bitmap is `PC5_IDENTITY_LIMIT / 4096 / 8` = 128 KiB — derived from the protocol's
    limit, not chosen — so no map the protocol is allowed to state can outgrow it, and
    the refusal remains reachable only for a caller that passes a smaller buffer (which
    `tests/test_mem64.py` pins);
  * every grant is re-derived at allocation time (the map must still cover the run, and
    the run must touch nothing claimed), so a bitmap edited behind the pool's back cannot
    produce an allocation. Two layers assert that: `tests/test_mem64.py`, and — since the
    in-kernel battery clears frame 0's bit and demands the grant still be refused
    (`bitmap-lie-refused=1`) — `make stubtest64` as well. The second one exists because
    the first was not enough: deleting the re-check left the emulator boot reporting
    31/31 OK, which is how you find out a guard is only tested somewhere else;
  * `free` refuses a range it never granted, including the zero page and the kernel's own
    image, so a stray `free(0)` cannot put the pages the kernel stands on back into
    circulation;
  * `0` is never a success value *and* an address at once: `pc5_mem64_alloc` reports
    granted/refused separately, clears its out-parameter on a refusal, and frame 0 is
    reserved by policy. The sentinelled version of this API had exactly that bug, and the
    executed stub gate caught it on the first run — the host battery asserts it now too.

The pool reports itself once per boot as `PC5-64-MEM` (`status`, `frames`,
`conventional`, `conventional_total`, `claimed`, `free`, `largest`, `span`), followed by
`PC5-64-MEM-SELFTEST`, which allocates, frees, re-allocates, and tries every way of
cheating the pool. The self-test **dereferences nothing**: an earlier version wrote a
pattern into the page it had just been granted, which passed the stub firmware (whose map
backs the whole window) and faulted the synthetic machine in `tests/test_kernel64.py`,
whose does not — 41 contract tests failing on a line that was not testing them. What
"the page is usable" means here is a property of the map and the span, so that is what is
asserted. A pool too small for the battery reports `result=skipped`, and a pool whose
battery disagrees marks itself `ready = 0` and reports
`status=unavailable reason=mem64-selftest-failed` rather than halting a boot that has
nothing to allocate yet. `conventional` and `claimed` obey
`conventional = claimed + free`, and `conventional_total` must equal the
`conventional_pages` the map validation counted — two independent counts over the same
descriptors, compared by `make stubtest64`. A map the pool cannot support is reported as
`status=unavailable reason=…` and the boot continues: nothing in the kernel allocates
from it yet, so refusing to *manage* memory must not stop a machine that would otherwise
boot — but the executed gate requires `status=ok`, so it can never quietly regress.

Three layers check this, and they are deliberately not interchangeable: the host battery
(`python3 -m unittest tests.test_mem64`, which also compiles three mutants of `mem64.c`
and fails if any of them passes), the executed 64-bit stub gate (`make stubtest64`, real
long-mode execution of the linked kernel under Unicorn), and genuine firmware
(`make ovmf-test`), which this machine cannot run at all and which therefore has **not**
verified the allocator on OVMF or on a physical PC.

### 7.5b How far the boot path is actually verified

"Done" has six levels here, and the roadmap records them instead of collapsing them:

| level | M2a (long mode, APIC, timers, CPU enumeration) | the frame pool (§7.5a) |
| --- | --- | --- |
| implemented | yes - `7737d896ebcfd126fb2aebc161c9bb249115c4d1`, `094a03e5a895cf9212cc8134397ccb9361ae2261`, `43ab4af9f10c272be7752d65dd9551e285b69836`, `547ebd5cff04b87330d95807a90795d9ac4d66d0` | yes - `7fac313668a13511f4278fc27a8bed463b442fcd` |
| host-tested | yes - `python3 -m unittest tests.test_apic64 tests.test_idt64 tests.test_timer64 tests.test_madt64` | yes - `python3 -m unittest tests.test_mem64` |
| stub-firmware-tested | yes - executed in long mode under Unicorn by `make stubtest64` | yes - the same gate, and its battery lines |
| genuine-UEFI-tested | **no** - `make ovmf-test` reports NOT TESTED here (no OVMF image, no QEMU) | **no** |
| physical-hardware-tested | **no** - no machine has run this kernel | **no** |
| outstanding acceptance criteria | interrupt delivery from a device, a second CPU brought up, per-machine SVM records in the qualification list | a kernel subsystem that allocates through it, and the same measurements on firmware |

M2a and M2b are therefore `in_progress`, not `not_started` and not `complete`: the code
and its two lower verification levels are real and re-runnable, the two upper levels have
never happened, and `make ovmf-test` exits 2 with `NOT TESTED` on this machine rather
than passing. The ceiling is enforced, not promised - `tests/test_roadmap_dependencies.py`
refuses a `complete` state for either milestone while
`docs/evidence/validation/ovmf-test.json` still records `not-tested`, refuses a promotion
to `complete` that cites no evidence, and refuses any milestone whose cited evidence path
does not exist.

### 7.5c The first consumer: a TSS, two interrupt stacks, and the one step not taken

The pool exists to be consumed, so the kernel now consumes it.  `kernel64/tss64.c` asks
for three frames - one for a 104-byte task-state segment, one for the stack a double fault
runs on (IST1), one for the NMI stack (IST2) - and keeps them for the life of the boot.
It writes the TSS into the frame it was given, encodes a descriptor for it into a GDT the
kernel owns, installs that table, and reads GDTR back to prove the install happened:
`PC5-64-TSS status=ok ... gdt=0x129280 gdtr=0x129280 cpl=0 frames=3 free-after=617`.
The executed gate requires the frames reported taken to be the frames the pool lost
(`free 620 -> 617`), the three frames to be distinct, each IST to be a page top, and
GDTR to equal what was written - so the accounting cannot drift from the report.

**What it does not do is load TR, and that is a measurement, not an omission.** IST is
only consulted once TR names the TSS, so the natural last step is `ltr`; under the
emulator this repository can actually run, executing `ltr` raises an exception.  It was
ruled out that the table is wrong: CPL was read as 0 first, LGDT on the preceding
instruction succeeded, SGDT read the same base and limit back, the descriptor decodes to
the granted frame with limit 103 and the available-64-bit-TSS access byte, and pointing
the descriptor at the kernel's own image instead of a pool frame faults identically.  The
kernel therefore *refuses to arm the routing* while TR does not name this TSS -
`tr=not-loaded`, `ist-df=0`, `ist-nmi=0` - and the gate asserts all three.  Arming a gate
onto an interrupt stack the CPU cannot resolve converts a fault the kernel reports into a
fault nobody sees, which is the opposite of the point.

The rules that would arm it are exercised on the live table anyway (absent gate refuses,
index 0 refuses, index 8 refuses, index 1 arms and reads back, clearing clears), which is
what `arm-rules=1` means, and `tests/test_tss64.py` compiles five mutants of the builder
(a misaligned IST, an ignored ready flag, a release that forgets the stacks, a refusal
that keeps the frames, a descriptor whose high base bytes land in the wrong field) and
fails if any of them survives.  Loading TR on real firmware stays open, and is recorded
as open: nothing here demonstrates a double fault running on its own stack.

**That limit is now a command rather than a paragraph.** `make emulator-probe`
(`tools/emulator_capabilities.py`) measures, on whatever emulator is installed, the four
things the sentence depends on, and it is worth reading before repeating it.  On Unicorn
2.1.4 the answers are: software interrupts *are* modelled (`int 3` and `int 7` reach an
interrupt hook with their own vectors and the guest continues) while processor exceptions
*are not* (`ud2` reaches nothing and the run stops with `UC_ERR_INSN_INVALID`); TR is
writable and readable by the host as a 4-tuple of selector, base, limit and flags, which is
why a host-seeded value must never be reported as activation; and a guest `ltr` never
populates TR -- it takes `#GP` then `#DF` against a table the probe could not verify, or
leaves a seeded TR unchanged.  The same `ud2` injected into `report_tss()` on the real boot
path stops the harness at the faulting RIP with `PC5-64-EXCEPTION` never printed, in a boot
that otherwise passes, so this is the engine's exception path and not PC5's IDT, TSS or
harness.  Consequence, unchanged in substance and now measurable: the IST entries are
configured and gated, dispatch is not observed, and the criterion belongs to OVMF or
hardware.  The run, the reasoning and the encoding bug the self-check caught are in
[evidence/2026-11-22-emulator-capabilities/](evidence/2026-11-22-emulator-capabilities/README.md).

### 7.6 CPU features and the SVM ladder

`kernel64/cpu64.c` reports vendor, family/model/stepping, physical and virtual
address widths, long mode, NX, 1 GiB pages, APIC, x2APIC, maximum APIC IDs and
the SVM bits (advertised, nested paging, ASIDs) plus whether the CPU is already
a guest. Every extended leaf is gated on the **saved** maximum extended leaf, not
on whatever a previous `CPUID` left in `EAX`: the address-width leaf is read only
when the CPU advertised it, and the invariant-TSC leaf only when that leaf is
within range. A width the CPU does not report is reported as `not-reported`, never
as "every address fits". Reporting SVM is not a hypervisor claim. The six evidence
levels are: advertised (CPUID), firmware-enabled, permitted, PC5-initialised, guest
executed, VM-exit tested. This work reaches **level 1 only**, and only in emulation.

### 7.7 Release isolation

`iso`, `uefi`, `boot-test`, `verify` and every release asset are unchanged and
still 32-bit. The 64-bit path has its own targets — `make kernel64`,
`make uefi64`, `make stubtest64` — and its own ESP image
(`build/efi64.img`). `tests/test_kernel64.py::ReleaseIsolationTests` fails if
`make -n all` starts to depend on any of it.
