# Building PC5

## Requirements

| Component | Version used | Notes |
|---|---|---|
| `gcc` | 12.2.0 | must support `-m32` code generation (no 32-bit libc needed) |
| `binutils` | 2.40 | `as` with `.code16/.code32`, `ld` with `elf_i386` and `--oformat binary` |
| `make` | GNU make | top-level `Makefile` |
| `python3` | 3.11 | ISO writer, verifier, firmware tool, tests |
| `node` + `v86-system` | node 22 | only for `make boot-test` (`npm install v86-system`) |
| `unicorn` (pinned `2.1.4`) | `requirements-harness.txt`, installed into `.venv` | the emulator-backed loader suites; without it `make check` skips 107 tests and says why, with it they run |

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-harness.txt
export PATH="$PWD/.venv/bin:$PATH"
```

That is the same provisioning `ci/build.yml` performs. `pip install` straight into a
distribution Python is refused under PEP 668, so the venv is not a preference here.

The UEFI application in `boot/uefi/` uses the *same* toolchain: it is a PE32+
image produced by `ld -m i386pep` (binutils' 64-bit PE emulation), so neither a
cross compiler nor EDK2 is needed.

No other dependency is required: the build does not use a cross compiler, a
distribution tool, or network access.

## Targets

```sh
make info        # version, build id, timestamp, source list
make             # build/pc5.iso, build/pc5.iso.sha256, build/build-info.json
make unit        # host-side kernel unit tests (165 checks)
make check       # python test suite FIRST, then the unit/contract/documentation gates --
                 # a broken gate cannot hide the suite, and the failing leg is named
make citations-check  # every commit cited by the evidence documents resolves here
make citation-refs    # fetch refs/pull/*/head: needed only for citations that point at an
                      # open pull-request head, or in a filtered/partial clone
make verify      # independent ISO verification (+ build/verify-report.json)
make roadmap     # validate the milestone graph, release isolation and the destination path
make uefi        # just the UEFI application and the FAT ESP (build/efi.img)
make boot-test   # boot the ISO in the emulator; 119 assertions (incl. FAT32 write)
make stubtest    # execute the UEFI loader against a stub firmware (58 checks)
make ovmf-test   # boot the ISO under genuine OVMF; exit 3 = NOT TESTED
make ovmf-setup  # provision QEMU + TianoCore OVMF from the distribution
make ovmf-check  # verify that provisioning, without installing anything
make emulator-probe  # what the installed emulator can and cannot prove (always exit 0)
make metadata    # add provenance to build/build-info.json
make release-assets  # stage pc5.iso, pc5.iso.sha256, build-info.json
make clean
```

## Reproducibility

Two inputs are embedded in the kernel and therefore in the image hash:

| Input | Default | Override |
|---|---|---|
| build id, printed as `PC5_BUILD_ID` and shown on screen | `git rev-parse --short HEAD` | `make BUILD_ID=…` |
| build timestamp, printed as `PC5_BUILD_DATE` | current UTC time | `SOURCE_DATE_EPOCH=…` or `make BUILD_DATE=…` |

Byte-identical output therefore needs **the same commit and the same timestamp**:

```sh
export SOURCE_DATE_EPOCH=1700000000
make clean iso && sha256sum build/pc5.iso
make clean iso && sha256sum build/pc5.iso   # same digest both times
```

Everything else is deterministic: `tools/mkiso.py` allocates every extent by a
fixed rule, stamps the volume and directory records from `SOURCE_DATE_EPOCH`
(not from the wall clock) and writes a constant disk signature into the hybrid
MBR, so nothing depends on file-system order or on when you build. This is covered by
`tests/test_tools.py::test_source_date_epoch_makes_builds_byte_identical`. `build/build-info.json` records the volume
layout, the per-file SHA-256 values and the image SHA-256 that `make verify`
re-checks.

Take the digest from your own build rather than from a document: this
repository quotes hashes with the commit they came from, and a hash built from a
different commit is a different, equally valid image.

## Booting the ISO under real UEFI firmware

The BIOS path is tested with an emulator alone. The UEFI path needs firmware, and
firmware is an external dependency this repository does not ship:

```sh
# Debian/Ubuntu:  sudo apt install ovmf qemu-system-x86
# Fedora:         sudo dnf install edk2-ovmf qemu-system-x86
# Arch:           sudo pacman -S edk2-ovmf qemu-system-x86

make iso
make ovmf-test                       # discovers firmware in /usr/share/OVMF/...
```

Anything unusual can be pointed at explicitly — a wrapper script around
`qemu-system-x86_64` is fine, which is how a QEMU that needs its own loader or
library path gets used:

```sh
PC5_QEMU=/path/to/qemu-system-x86_64 \
PC5_QEMU_DATA_DIR=/path/to/share/qemu \
PC5_OVMF_CODE=/usr/share/OVMF/OVMF_CODE_4M.fd \
PC5_OVMF_VARS=/usr/share/OVMF/OVMF_VARS_4M.fd \
make ovmf-test

# or, equivalently:
python3 tests/ovmf_boot.py --iso build/pc5.iso \
  --ovmf-code …/OVMF_CODE.fd --ovmf-vars …/OVMF_VARS.fd \
  --qemu qemu-system-x86_64 --json-out build/ovmf-report.json
```

`tests/ovmf_boot.py --list-firmware` prints every path it looks at. Three exit
codes, and only the first is a pass:

| Exit | Meaning |
|---|---|
| 0 | real OVMF booted the PC5 kernel; `PC5-OVMF-BOOT-OK` and `build/ovmf-report.json` written |
| 1 | the boot ran and a check failed — the report names it |
| 3 | **NOT TESTED**: no emulator, no firmware, or a file that is not a firmware volume |

The harness copies the VARS image before every boot (firmware writes to it),
records the firmware and QEMU versions and the SHA-256 of both images, keeps the
serial logs under `build/ovmf/`, and never commits firmware to the repository.

## Continuous integration and releases

The pipeline is written and validated, but **not yet active on GitHub**: it lives
in `ci/build.yml` because the GitHub App that authored it has repository admin
rights but not the *workflows* permission, so GitHub refuses any push that
creates `.github/workflows/build.yml`. Activating it is one command:

```sh
git mv ci/build.yml .github/workflows/build.yml
git commit -m "ci: activate the build and release pipeline" && git push
```

`ci/README.md` records why, and what has been proven without it. The description
below is what the pipeline does once it is in `.github/workflows/`.

| Trigger | What runs | What is published |
|---|---|---|
| push to any branch, pull request | build job | workflow artifact `pc5-<sha>` (30 days) + logs |
| push tag `v*` or `pc5-*` | build job, then release job | the three assets on that release |
| manual dispatch | build job | workflow artifact only |

The build job, in order: check out the exact commit → record the toolchain →
set `BUILD_ID=$GITHUB_SHA` and `SOURCE_DATE_EPOCH` to the commit's timestamp →
`make clean && make iso` → `make verify` → `make unit` → host test suite →
`npm install v86-system && make boot-test` → **build a second time and fail the
job unless both images hash identically** → re-verify, re-test and stage the
assets with `make release-assets` → assert `sha256sum -c` and that the
verification verdict in `build-info.json` is `PASS` → upload.

The release job runs only for tags, only when the build job succeeded, and is
the only job with `contents: write`. It downloads the verified artifacts,
re-checks the checksum, creates the release if it does not exist (otherwise
updates its notes), and uploads `pc5.iso`, `pc5.iso.sha256` and
`build-info.json` with `--clobber`, so re-running a release is safe.

To cut a release:

```sh
# on main, with a clean tree
git tag -a v0.2.0 -m "PC5 0.2.0"
git push origin v0.2.0
gh run watch            # build + release
gh release view v0.2.0  # the three assets
```

Third-party actions are pinned to commit SHAs (enforced by
`tests/test_tools.py::WorkflowTests`), no secrets are used, and the pipeline
fails closed: nothing is published if any build, verification or test step
fails.

Publishing itself is `tools/publish_release.sh`, not inline YAML, so it can be
exercised without GitHub: `tests/test_release.py` runs it against a stub `gh`
and asserts the checksum gate, the verdict gate, create-then-update (no
duplicate assets), `--clobber`, and the final "all three assets attached" check.
That is a test of the logic, not proof that GitHub accepted an upload — only a
real run can show that.

### What the metadata records

`make metadata` runs `tools/buildmeta.py`, which appends a `build` object to
`build/build-info.json` (schema `pc5.build-metadata/1`) containing the version,
tag, commit, build id, `SOURCE_DATE_EPOCH`, architecture, the compiler and
toolchain versions, the artifact hash **re-computed from the file**, and the
result of every test that was run (ISO checks, boot checks, kernel unit checks,
host tests, each with the SHA-256 of the log it came from). It never modifies
the image, so provenance cannot affect reproducibility; it refuses to write a
record when the image no longer matches its hash or when a report contains
failures.

## Layout

```
boot/loader.S        stage-1 loader (real mode, 4096 bytes, descriptor at 0xE00)
kernel/              freestanding 32-bit kernel (see docs/ARCHITECTURE.md)
tools/               ISO writer, verifier, firmware analysis, operator CLI
tests/               emulator harness, boot assertions, host + kernel unit tests
docs/                engineering documentation
build/               generated; not committed
```

Generated boot artifacts, all pinned by the Makefile:

| File | Size | What it is |
|---|---|---|
| `build/loader.bin` | exactly 4096 | stage-1 loader (`boot/loader.S`), loaded at `07C0:0000` |
| `build/mbr.bin` | exactly 440 | hybrid MBR bootstrap (`boot/mbr.S`), first bytes of sector 0 |
| `build/efi.img` | 1,474,560 | FAT12 ESP holding `\EFI\BOOT\BOOTX64.EFI` |
| `build/kernel.bin` | ≤ 585,728 | the 32-bit kernel |

`tools/mkiso.py --mbr-code build/mbr.bin` receives only the 440 bytes of code: it
writes the disk signature, the partition table (start LBA 0, length = the whole
image in 512-byte sectors, type `0x17`, boot flag set, CHS derived from the same
LBAs), the `55 AA` word, and patches the boot-image LBA and length into the
bootstrap from the El Torito entry. A build without a bootstrap is refused — an
image that only boots as a CD is a support case nobody can debug in the field.

## Adding a file to the ISO

`make iso` passes `--file NAME=PATH` to `tools/mkiso.py`. File names are
normalised to ISO9660 level 1 (`NAME.EXT;1`) and must fit one 2048-byte root
directory sector — the writer fails the build rather than writing a broken
volume.

## Build guard rails

* loader must be exactly 4096 bytes (the boot descriptor offset is compiled in),
* MBR bootstrap must be exactly 440 bytes (the partition table starts at 0x1B8),
* the MBR partition must cover the whole image and name the El Torito boot image
  (`make verify` re-reads sector 0 and fails on any disagreement),
* kernel must be ≤ 585,728 bytes (real-mode load window),
* `tools/mkiso.py` refuses to write past the end of the image and asserts the
  final size,
* `make verify` re-parses the finished image from scratch.
