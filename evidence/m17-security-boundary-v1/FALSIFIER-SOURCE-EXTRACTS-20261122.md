# Falsifier source extracts, retrieved 2026-11-22 — provenance for `SECURITY_BOUNDARY.md` §4

Why this file exists: §4 of the analysis rests on claims about material outside the repository, and
a claim about an external project that cannot be re-checked is worth nothing in an evidence tree.
Every extract below was read **in this sandbox** on the date shown, by the command shown, and is
quoted with enough context that a reader can tell whether the summary in the analysis is faithful.
Nothing was fetched from these projects beyond public repository metadata and README text: no
firmware, no keys, no payload, no tool binaries. No command here contacts a Sony asset other than
via a search-result excerpt, and none downloads any executable.

## 1. Method actually used (reproducible)

```sh
# repository metadata, primary source (GitHub REST, unauthenticated reads via the gh client)
gh api repos/sharpemu/sharpemu   --jq '{desc:.description,created:.created_at,pushed:.pushed_at,stars:.stargazers_count,license:.spdx_id,homepage:.homepage}'
gh api repos/KytyPS5/KytyPS5     --jq '...'      # same shape
gh api repos/RPCSX/rpcsx         --jq '...'      # same shape
gh api 'search/repositories?q=ps5+emulator&sort=stars&order=desc&per_page=12' \
   --jq '.items[]|"\(.full_name) ★\(.stargazers_count) created \(.created_at) pushed \(.pushed_at) :: \(.description)"'

# README text of the two projects whose status sections matter
gh api repos/sharpemu/sharpemu/readme  --jq '.content' | base64 -d
gh api repos/KytyPS5/KytyPS5/readme    --jq '.content' | base64 -d
gh api repos/RPCSX/rpcsx/readme        --jq '.content' | base64 -d
```

Timestamps: the metadata reads ran at `2026-11-22T00:5x–01:0xZ`; `date -u` in the same session
reported `2026-11-22T00:57:06Z`. Star counts and `pushed_at` are therefore as-of values, not
constants, and the analysis quotes them as measured here rather than as properties of the projects.

## 2. `sharpemu/sharpemu` — quoted

Metadata: `description: "An experimental PlayStation 5 emulator for Windows and Linux"`,
`created_at: 2026-03-11T12:46:36Z`, `pushed_at: 2026-11-20T22:16:39Z`, `stargazers_count: 6692`,
`language: C#`, `spdx_id: null` at the repository level with `SPDX-License-Identifier:
GPL-2.0-or-later` in the README header.

README, "Status" section:

> The emulator can currently load the `eboot.bin` of real games, execute native CPU instructions,
> and partially handle gpu-related functionality. Included 3D games.
> Platform support is still experimental, so compatibility and performance vary by game, operating
> system, and GPU driver.

README, legal/ownership section:

> All games used during development and testing are dumped from consoles that we personally own.
> Users are expected to use legally obtained copies of their games.

README, "Disclaimer":

> SharpEmu is an experimental emulator intended for research and educational purposes.
> This project does not contain any copyrighted system firmware, game data, or proprietary
> PlayStation assets.

**What the analysis takes from it, and no more:** a substantial, active, public PS5 emulator exists;
its own description of its current capability is *game executable loading* plus partial GPU
handling; it states that it ships no system firmware. **Nothing in it** is read as a claim about
emulating the console's security processor or booting the signed system software, and §4 of the
analysis says so rather than inferring silence either way.

## 3. `KytyPS5/KytyPS5` — quoted

Metadata: `description: "PlayStation 5 translation layer for Windows, Linux and macOS"`,
`created_at: 2026-06-09T14:58:38Z`, `pushed_at: 2026-11-21T22:48:19Z`, `stargazers_count: 12461`,
`language: C++`, licence badge `GPL-2.0`, status badge `active development`.

README, note and status:

> not distribute games or copyrighted system software. Use only game files that you have obtained
> legally.
>
> **Current Status** — Development is currently focused on expanding game compatibility and
> improving boot reliability.
>
> macOS support is experimental. … A small number of titles have been verified in-game

README, first-run section (what the project consumes as input):

> The launcher searches those folders recursively for game directories containing `eboot.bin` and
> ZArchive (`.zar`) game dumps whose archive root contains `eboot.bin`.

**Reading:** the object being booted is a *game dump supplied by the user*, and "boot reliability"
is about game boot, not system-software boot. Recorded because the phrase "booting PS5" in a
secondary report about this project would otherwise be ambiguous: the project's own words scope it
to titles.

## 4. `RPCSX/rpcsx` — quoted, and what is *not* said

Metadata: `created_at: 2023-06-22T23:36:21Z`, `pushed_at: 2026-06-29T21:12:31Z`,
`stargazers_count: 2043`, `description: null`, `homepage: null`.

README in full essence: `*An experimental PlayStation 4 and PlayStation 5 emulator for Linux written
in C++*`; a warning that "Do not ask for link to games or system files. Piracy is not permitted on
the GitHub nor in the Discord."; build/usage document pointers; licence note (GPLv2, with
`orbis-kernel` MIT); derived from RPCS3 sources.

**No status section, no boot claim, and the repository has not been pushed since 2026-06-29.** The
secondary reports surfaced by the same search assert more — that this project "boots the PS5's VSH
(its system shell and menu layer) and safe mode, with working audio and controller input" (a 2026-10
blog, and echoed elsewhere). That claim is **not** supported by anything read in the project's own
README, and the analysis marks it `not-verified` rather than using it. Had it been established, it
would engage falsifier F-2 directly — which is exactly why the distinction between "a secondary
source says a shell started" and "published evidence of a full-SoC emulator booting signed software
on commodity hardware" is kept explicit in §4.

## 5. The noise class, recorded so it is not mistaken for signal

The same GitHub search returned many repositories whose descriptions contain "PS5" and "emulator"
in the *opposite* direction — software that runs on a jailbroken console, e.g. "A PS5 emulator for
the PS4. Runs on a jailbroken PS4 with Linux" and "native GameCube and Wii emulator for jailbroken
PS5". These are evidence about console-side homebrew environments; they say nothing about executing
the console's system software on a PC, and none is cited in the analysis. They are listed here
because a search-and-summarise pass would otherwise have promoted them.

## 6. The lawful-channel facts (S1, F-1)

Two facts used by §2 (S1) and §4 (F-1) come from Sony's own support text, as surfaced by the search
retriever on 2026-11-22 (`located`: page not fetched here; the URL is already cited by
`docs/FIRMWARE_ANALYSIS.md` §2, which is where the repository keeps its pointer to this page):

> Download the PS5 console update file below and save it in the "UPDATE" folder. Save the file as
> "PS5UPDATE.PUP". There must be approximately 1,1GB of free space. … How to *reinstall* the PS5
> console system software … Download the reinstallation file below … approximately 1,2GB of free
> space.
>
> Don't download or install the update using data other than the official update file provided
> online by Sony Interactive Entertainment. … If you download or install the update data from a
> different source, by a different method, or on a console that has been altered or modified in any
> way, the console might not operate properly and might not be able to install the official update
> data.

**Reading used in the analysis:** (a) an official, public channel exists for the **outer package**,
in both update and reinstallation flavours — which is why F-1 is answered by *separating* "the
package" from "the inner components" instead of dismissed; (b) the publisher's own framing of use is
console-side, and it names an alteration check — that is S1 and S10, and it is the reason the
analysis says a lawful download does not imply a licensed execution target.

## 7. The community checksum list, used only for §10 item 1

`MewX/ps5-official-firmware-list` (retrieved excerpt, `located`):

> The community-contributed PlayStation 5 official firmware list with checksums. By default, no
> downloads will be offered by this repo. … In the PS5UPDATE.PUP download URL that updatelist.xml
> points at, the `sys_<SHA256>` path segment is the SHA-256 of the file itself …

This is the whole basis of §10's proposal — that the *URL structure Sony's own `updatelist.xml`
uses* embeds the file's SHA-256, so the repository's declared object id could be identified against
published metadata **without fetching any payload**. The proposal is recorded as a procedure and
deliberately **not executed**: this sandbox's egress does not include those hosts, the payload was
never pulled into any workspace here, and identification of the package is `M9`'s question, so the
step belongs to the maintainer's decision. The repository's own rule for such work already exists
and is unchanged: `docs/PS5_SYSTEM_SOFTWARE_TARGET.md` §3.1 ("Establish identity first, in a
workspace outside the repository… Record the summary only… Never the payload").

## 8. Honest limits of this provenance file

1. Network egress in this environment is limited to a small host allowlist, so the two `located`
   rows (Sony's support page, the AMD/IOActive material) were read as retrieved excerpts, not as
   fetched pages. The analysis marks them that way and never writes `verified` about them.
2. Star counts, dates and "last pushed" values are as-of 2026-11-22 and will drift; the analysis
   quotes them as measurements with a timestamp for exactly that reason.
3. README text is what a project says about itself. It is *good* evidence of the project's own
   claims — which is all §4 needs — and no substitute for running anything. Nothing here was run.
4. `docs/FIRMWARE_ANALYSIS.md` §2 already cites a gbatemp "PUP decrypt tool" thread and a research
   issue, and labels them "third-party reports, not verified facts". This file keeps that stance
   verbatim; §6 of `SECURITY_BOUNDARY.md` is the reason no such tool is ever a candidate path.
