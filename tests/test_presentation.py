"""The presentation layer has to be generated, and it has to stay honest.

The README is the first thing anybody reads, which makes it the easiest place in this
repository to overstate progress. These tests hold it to three rules:

  * the figures and the status table are *derived* from `roadmap.json` — change a
    milestone state and the drawing changes, without editing a single SVG;
  * the checks that guard the README actually fire: a stale figure, a hand-edited
    status row, a broken link, an image without alt text and a banned claim each have
    a test that expects a failure;
  * nothing in the presentation claims evidence the repository does not have — no
    screenshot, no percentage of compatibility, no "CI passing".
"""

from __future__ import annotations

import copy
import contextlib
import json
import re
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import presentation as P  # noqa: E402

SVG_NS = "{http://www.w3.org/2000/svg}"


def roadmap():
    return json.loads((REPO / "docs/architecture/roadmap.json").read_text(encoding="utf-8"))


def with_state(data, milestone, state):
    changed = copy.deepcopy(data)
    for entry in changed["milestones"]:
        if entry["id"] == milestone:
            entry["state"] = state
    return changed


class FigureTest(unittest.TestCase):
    def setUp(self):
        self.data = roadmap()

    def test_every_figure_is_well_formed_svg(self):
        for name, body in P.rendered(self.data).items():
            root = ET.fromstring(body)
            self.assertEqual(root.tag, SVG_NS + "svg", name)
            self.assertTrue(root.get("viewBox"), f"{name} has no viewBox")
            self.assertTrue(int(root.get("width")) > 0 and int(root.get("height")) > 0)
            self.assertIsNotNone(root.find(f"{SVG_NS}title"), f"{name} has no title")
            self.assertIsNotNone(root.find(f"{SVG_NS}desc"), f"{name} has no desc")

    def test_figures_are_deterministic(self):
        first = P.rendered(roadmap())
        second = P.rendered(roadmap())
        self.assertEqual(first, second)

    def test_figures_carry_no_external_references(self):
        for name, body in P.rendered(self.data).items():
            # the SVG namespace is the only URI allowed to appear in a figure
            for bad in ("https://", "<image", "@font-face", "xlink:href", "url("):
                self.assertNotIn(bad, body, f"{name} reaches outside the repository: {bad}")

    def test_a_milestone_change_changes_the_drawing(self):
        """Derivation, proven: no SVG is edited by hand for a status change."""
        before = P.rendered(self.data)
        after = P.rendered(with_state(self.data, "M1a", "blocked"))
        self.assertNotEqual(before["pc5-architecture.svg"], after["pc5-architecture.svg"])

    def test_the_destination_is_drawn_as_blocked(self):
        body = P.rendered(self.data)["pc5-architecture.svg"]
        self.assertIn("BLOCKED", body)
        self.assertIn("Genuine Sony PS5 system software", body)

    def test_firmware_is_not_drawn_as_verified(self):
        """M1h completing must not promote firmware on a real machine."""
        body = P.rendered(self.data)["pc5-architecture.svg"]
        firmware = body.split("Firmware", 1)[1][:900]
        self.assertIn("NOT TESTED", firmware)
        self.assertNotIn("VERIFIED", firmware)

    def test_the_progress_figure_counts_states_from_the_graph(self):
        data = self.data
        complete = sum(1 for m in data["milestones"] if m["state"] == "complete")
        body = P.rendered(data)["pc5-progress.svg"]
        self.assertIn(f"{complete} of {len(data['milestones'])} complete", body)
        for stream_id in ("WS10", "WS12"):
            blocked = sum(1 for m in data["milestones"]
                          if m["workstream"] == stream_id and m["state"] == "blocked")
            self.assertTrue(blocked > 0, stream_id)
            self.assertIn(f"{blocked} blocked", body)

    def test_long_workstream_names_are_clipped_not_overflowing(self):
        body = P.rendered(self.data)["pc5-progress.svg"]
        for text in re.findall(r">([^<>]{45,})</text>", body):
            if "PS5 platform compatibility" in text or "Hardware discovery" in text:
                self.assertIn("\u2026", text, f"unclipped label: {text!r}")


class StatusTableTest(unittest.TestCase):
    def setUp(self):
        self.data = roadmap()
        self.rows = P.status_rows(self.data)
        self.labels = {title: label for title, label, _colour, _evidence in self.rows}

    def test_one_row_per_declared_capability(self):
        self.assertEqual(len(self.rows), len(P.ROWS))
        self.assertEqual(len({row[0] for row in self.rows}), len(P.ROWS))

    def test_labels_come_from_the_roadmap(self):
        by_id = {m["id"]: m["state"] for m in self.data["milestones"]}
        expected = P.STATE_STYLE[by_id["M10"]][0]
        self.assertEqual(self.labels["PS5 platform contract"], expected)
        self.assertEqual(self.labels["Genuine Sony system software executing"], "BLOCKED")

    def test_physical_boot_is_not_tested_and_not_verified(self):
        self.assertEqual(self.labels["Physical PC boot"], "NOT TESTED")

    def test_a_filed_physical_record_promotes_the_row(self):
        """The row is evidence-driven: the label follows the records, not the prose."""
        original = P.physical_evidence
        try:
            P.physical_evidence = lambda: [REPO / "docs/evidence/M1_RECORD_TEMPLATE.json"]
            rows = dict((t, l) for t, l, _c, _e in P.status_rows(self.data))
            self.assertEqual(rows["Physical PC boot"], "VERIFIED")
        finally:
            P.physical_evidence = original

    def test_the_readme_block_matches_the_generator(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn(P.status_markdown(self.data), readme)

    def test_the_block_lists_every_row(self):
        block = P.status_markdown(self.data)
        for title, _label, _colour, _evidence in self.rows:
            self.assertIn(f"| {title} |", block)


@contextlib.contextmanager
def redirected(root: Path):
    """Point the checker at a temporary copy of the two files it edits/reads."""
    saved = (P.README, P.ASSETS)
    P.README = root / "README.md"
    P.ASSETS = root / "docs/assets"
    try:
        yield
    finally:
        P.README, P.ASSETS = saved


class CheckTest(unittest.TestCase):
    """Each guard gets a failure it is supposed to catch."""

    def setUp(self):
        self.data = roadmap()
        self.tmp = Path(tempfile.mkdtemp())
        # the checker resolves README links against the file's own directory, so the
        # temporary copy needs the real documentation tree, linked not copied
        (self.tmp / "docs").mkdir()
        for entry in (REPO / "docs").iterdir():
            if entry.name == "assets":
                continue
            (self.tmp / "docs" / entry.name).symlink_to(entry, target_is_directory=entry.is_dir())
        # requirements-harness.txt is linked too: the README documents it at
        # the repository root, and a fixture without it would report a dead link.
        for name in ("CONTRIBUTING.md", "LICENSE", "requirements-harness.txt", "ci"):
            (self.tmp / name).symlink_to(REPO / name, target_is_directory=(REPO / name).is_dir())
        (self.tmp / "docs/assets").mkdir()
        for name, body in P.rendered(self.data).items():
            (self.tmp / "docs/assets" / name).write_text(body, encoding="utf-8")
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        # the copy has no docs/PRESENTATION.md; the checker skips a missing file
        (self.tmp / "README.md").write_text(readme, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def check(self) -> list:
        with redirected(self.tmp):
            return P.check(self.data)

    def test_the_real_repository_passes(self):
        self.assertEqual(P.check(self.data), [])

    def test_a_stale_figure_is_caught(self):
        path = self.tmp / "docs/assets/pc5-banner.svg"
        path.write_text(path.read_text().replace("PC5", "PC5!"), encoding="utf-8")
        problems = self.check()
        self.assertTrue(any("stale" in problem for problem in problems), problems)

    def test_a_hand_edited_status_row_is_caught(self):
        path = self.tmp / "README.md"
        text = path.read_text()
        good = P.status_markdown(self.data)
        self.assertIn("| Physical PC boot | **NOT TESTED** |", good)
        path.write_text(text.replace("| Physical PC boot | **NOT TESTED** |",
                                     "| Physical PC boot | **VERIFIED** |"))
        problems = self.check()
        self.assertTrue(any("status block" in problem for problem in problems), problems)

    def test_a_broken_image_path_is_caught(self):
        path = self.tmp / "README.md"
        path.write_text(path.read_text().replace("docs/assets/pc5-progress.svg",
                                                 "docs/assets/missing.svg"))
        problems = self.check()
        self.assertTrue(any("missing.svg" in problem for problem in problems), problems)

    def test_a_percent_encoded_nul_link_is_caught_not_raised(self):
        """`a%00b.md` decodes to a path with an embedded NUL.

        `Path.resolve()` raises `ValueError` for it. A link check must report the
        broken target rather than die on it - `link_problems` is the whole reason
        the presentation gate exists.
        """
        path = self.tmp / "README.md"
        path.write_text(path.read_text() + "\nSee [nul](docs/a%00b.md).\n")
        problems = self.check()
        self.assertTrue(any("link target missing" in problem for problem in problems),
                        problems)

    def test_an_image_without_alt_text_is_caught(self):
        path = self.tmp / "README.md"
        text = path.read_text()
        text = re.sub(r"!\[[^\]]*\]\(docs/assets/pc5-banner\.svg\)",
                      "![](docs/assets/pc5-banner.svg)", text)
        path.write_text(text)
        problems = self.check()
        self.assertTrue(any("alt text" in problem for problem in problems), problems)

    def test_a_banned_claim_is_caught(self):
        path = self.tmp / "README.md"
        path.write_text(path.read_text() + "\nPC5 boots on any PC.\n")
        problems = self.check()
        self.assertTrue(any("boots on any pc" in problem for problem in problems), problems)

    def test_a_missing_honesty_token_is_caught(self):
        path = self.tmp / "README.md"
        text = path.read_text().replace("NOT TESTED", "fine").replace("not tested", "fine")
        path.write_text(text)
        problems = self.check()
        self.assertTrue(any("NOT TESTED" in problem for problem in problems), problems)

    def test_a_figure_dropped_from_the_readme_is_caught(self):
        path = self.tmp / "README.md"
        path.write_text(path.read_text().replace("docs/assets/pc5-boot-workflow.svg",
                                                 "docs/assets/pc5-banner.svg"))
        problems = self.check()
        self.assertTrue(any("does not embed docs/assets/pc5-boot-workflow.svg" in problem
                            for problem in problems), problems)


class CommandContractTest(unittest.TestCase):
    """`make presentation` writes; `make presentation-check` reads; `make check` reads.

    The repository shipped the opposite for one release: the documentation said
    `presentation` regenerated the figures, while the target only checked them and the
    write lived in an undocumented, non-phony `presentation-sync`. These tests make the
    three-way contract explicit, so a future rename cannot quietly invert it again.
    """

    def setUp(self):
        self.makefile = (REPO / "Makefile").read_text(encoding="utf-8")
        self.targets = dict()
        current = None
        for line in self.makefile.splitlines():
            if line and not line[0].isspace() and line.rstrip().endswith(":") or (
                    line and not line[0].isspace() and ":" in line and "=" not in line.split(":")[0]):
                if ":" in line and not line.startswith("#"):
                    name = line.split(":")[0].strip()
                    if name and " " not in name and "=" not in name:
                        current = name
                        self.targets.setdefault(current, [])
                        continue
            if line.startswith("\t") and current:
                self.targets[current].append(line.strip())

    def recipe(self, name: str) -> str:
        return "\n".join(self.targets.get(name, []))

    def test_presentation_writes(self):
        self.assertIn("presentation.py sync", self.recipe("presentation"))

    def test_presentation_check_reads(self):
        self.assertIn("presentation.py check", self.recipe("presentation-check"))
        self.assertNotIn("sync", self.recipe("presentation-check"))

    def test_make_check_uses_the_read_only_target(self):
        """`check` runs the read-only gate and never the writer.

        Asserted across the whole rule -- prerequisite line plus recipe.  It used to
        look at the `check:` line alone, which stopped being the right place to look
        when the legs moved into the recipe so that a failed gate could not pre-empt
        the suite (tests/test_make_check_contract.py).  A one-line check would now be
        satisfied by a rule that runs the gate nowhere at all.
        """
        prereqs = [line for line in self.makefile.splitlines()
                   if line.startswith("check:")]
        self.assertTrue(prereqs)
        rule = prereqs[0] + "\n" + self.recipe("check")
        self.assertIn("presentation-check", rule,
                      "check must run the read-only presentation gate")
        self.assertNotIn("presentation.py sync", rule,
                         "check must not regenerate figures as a side effect")
        # The legs live in a shell loop now, so look at the loop's own list: the
        # writer must not be one of them.  (Checking only that the *string*
        # `$(MAKE) presentation` is absent would pass even if the gate had been
        # dropped from the loop entirely, which is the failure being guarded.)
        # `; do`, not ` do`: the latter silently matched the space before
        # "docs-check" and reported the loop as holding two gates.
        legs = re.search(r"for target in ([^;]+); do", rule)
        self.assertTrue(legs, "check no longer runs its gates through a loop; "
                              "update this test to read the new shape rather than "
                              "letting the guard go quietly stale")
        names = legs.group(1).split()
        self.assertEqual(names, ["unit", "psm", "docs-check", "citations-check",
                                 "presentation-check", "brand-check"])
        self.assertNotIn("presentation", names,
                         "check must not invoke the writing target")

    def test_every_documented_presentation_command_is_phony(self):
        phony = [line for line in self.makefile.splitlines() if line.startswith(".PHONY:")][0]
        for name in ("presentation", "presentation-check", "docs-check"):
            self.assertIn(name, phony.split(), f"{name} is not declared .PHONY")

    def test_the_old_alias_is_gone(self):
        self.assertNotIn("presentation-sync:", self.makefile)

    def test_generation_updates_stale_output_and_check_notices(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "docs").mkdir()
            for entry in (REPO / "docs").iterdir():
                if entry.name != "assets":
                    (tmp / "docs" / entry.name).symlink_to(
                        entry, target_is_directory=entry.is_dir())
            for name in ("CONTRIBUTING.md", "LICENSE", "requirements-harness.txt",
                         "ci", "brand"):
                (tmp / name).symlink_to(REPO / name,
                                        target_is_directory=(REPO / name).is_dir())
            (tmp / "docs/assets").mkdir(parents=True)
            for name, body in P.rendered(roadmap()).items():
                (tmp / "docs/assets" / name).write_text("stale\n", encoding="utf-8")
            (tmp / "README.md").write_text(
                (REPO / "README.md").read_text().replace(
                    P.status_markdown(roadmap()), P.BEGIN + "\n" + P.END),
                encoding="utf-8")
            with redirected(tmp):
                self.assertTrue(P.check(roadmap()), "stale output must fail the check")
                P.write(roadmap())
                self.assertEqual(P.check(roadmap()), [], "generation must fix it")
                before = {p: p.read_bytes() for p in (tmp / "docs/assets").iterdir()}
                self.assertEqual(P.write(roadmap()), [], "a clean generation writes nothing")
                self.assertEqual(before, {p: p.read_bytes() for p in (tmp / "docs/assets").iterdir()})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_check_does_not_modify_the_repository(self):
        tracked = [REPO / "README.md"] + sorted((REPO / "docs/assets").iterdir())
        before = {path: path.read_bytes() for path in tracked}
        P.check(roadmap())
        self.assertEqual(before, {path: path.read_bytes() for path in tracked})

    def test_generation_is_deterministic_byte_for_byte(self):
        first = P.rendered(roadmap())
        second = P.rendered(roadmap())
        self.assertEqual({k: v.encode() for k, v in first.items()},
                         {k: v.encode() for k, v in second.items()})


class LayoutGuardTest(unittest.TestCase):
    """Figures are geometry; text that leaves its box is a defect, not a taste question."""

    def test_no_text_runs_outside_a_figure(self):
        data = roadmap()
        for name, body in P.rendered(data).items():
            width = int(re.search(r'width="(\d+)"', body).group(1))
            self.assertEqual(P.overflow(body, width), [], name)

    def test_the_overflow_guard_actually_fires(self):
        long_line = P.text(10, 20, "x" * 200, size=14)
        body = P.svg(400, 60, long_line, "t", "d")
        self.assertTrue(P.overflow(body, 400))

    def test_workstream_labels_stay_clear_of_the_bars(self):
        body = P.rendered(roadmap())["pc5-progress.svg"]
        bar_x = 372
        for x, size, anchor, content in P.TEXT_ELEMENT.findall(body):
            if float(x) != 96.0:
                continue
            label = re.sub(r"<[^>]+>", "", content)
            self.assertLess(float(x) + len(label) * float(size) * 0.62, bar_x - 6,
                            f"label would overlap its bar: {label!r}")

    def test_every_figure_scales_for_mobile(self):
        for name, body in P.rendered(roadmap()).items():
            width = int(re.search(r'width="(\d+)"', body).group(1))
            self.assertLessEqual(width, 1200, name)
            largest = max(float(size) for _x, size, _a, _c in P.TEXT_ELEMENT.findall(body))
            smallest = min(float(size) for _x, size, _a, _c in P.TEXT_ELEMENT.findall(body))
            self.assertGreaterEqual(smallest, 10, f"{name} has text too small to read")
            self.assertLessEqual(largest, 64, name)


class DynamicDashboardTest(unittest.TestCase):
    """A change in the data must change the page. That is the whole contract."""

    def setUp(self):
        self.data = roadmap()
        self.records = P.load_records()
        self.assertTrue(self.records, "no validation records committed: the dashboard would "
                                      "have nothing to quote")

    def test_changing_a_milestone_changes_the_statistics(self):
        before = P.stats_markdown(self.data, self.records)
        after = P.stats_markdown(with_state(self.data, "M1a", "blocked"), self.records)
        self.assertNotEqual(before, after)
        self.assertIn("| Blocked | 7 |", after)

    def test_changing_a_workstream_changes_the_dashboard(self):
        changed = copy.deepcopy(self.data)
        changed["workstreams"].append({"id": "WS99", "name": "probe", "serves_level": "1",
                                       "purpose": "test fixture"})
        self.assertNotEqual(P.dashboard(self.data, self.records),
                            P.dashboard(changed, self.records))

    def test_changing_the_destination_state_changes_the_figures(self):
        before = P.dashboard(self.data, self.records)
        after = P.dashboard(with_state(self.data, "M19", "in_progress"), self.records)
        self.assertNotEqual(before, after)
        self.assertIn("in progress", after)

    def test_a_changed_record_updates_the_evidence_block(self):
        before = P.evidence_markdown(self.records)
        changed = copy.deepcopy(self.records)
        changed["boot-test"]["result"] = "not-tested"
        after = P.evidence_markdown(changed)
        self.assertNotEqual(before, after)
        self.assertIn("**not-tested**", after)

    def test_an_old_record_is_stamped_with_its_own_commit(self):
        """It is a snapshot, never a statement about the current tree."""
        block = P.evidence_markdown(self.records)
        commit = self.records["check"]["commit"][:7]
        self.assertIn(f"`{commit}`", block)
        self.assertNotIn("current commit", block)
        self.assertIn("not evidence for the current one", block)

    def test_missing_evidence_never_becomes_verified(self):
        block = P.evidence_markdown({})
        self.assertIn("**no record**", block)
        self.assertNotIn("passed", block)
        self.assertIn("**NOT TESTED**", block)
        self.assertIn("**BLOCKED**", block)

    def test_the_physical_row_follows_the_filed_records(self):
        # no physical record filed in this repository, so the row says so
        self.assertIn("NOT TESTED", P.evidence_markdown(self.records))
        original = P.physical_records
        try:
            P.physical_records = lambda: [("2026-11-20-example.json", {"outcome": "booted",
                                                                       "date": "2026-11-20"})]
            block = P.evidence_markdown(self.records)
            self.assertIn("**booted**", block)
        finally:
            P.physical_records = original

    def test_every_block_states_the_numbers_the_data_holds(self):
        counts = P.distribution(self.data)
        block = P.stats_markdown(self.data, self.records)
        self.assertIn(f"| Complete | {counts['complete']} |", block)
        self.assertIn(f"| Blocked | {counts['blocked']} |", block)
        self.assertIn(f"| In progress | {counts['in_progress']} |", block)
        self.assertIn(f"| Not started | {counts['not_started']} |", block)

    def test_blocked_milestones_are_listed_with_their_blocker(self):
        block = P.blockers_markdown(self.data)
        for milestone in self.data["milestones"]:
            if milestone["state"] == "blocked":
                self.assertIn(f"`{milestone['id']}`", block)
                self.assertIn("| `", block)

    def test_the_pup_block_is_read_from_the_pointer(self):
        facts = P.pup_facts()
        block = P.pup_markdown()
        self.assertTrue(facts["pointer"])
        self.assertIn(f"{facts['bytes']} bytes", block)
        self.assertIn(facts["sha256"][:12], block)
        self.assertIn("UNVERIFIED", block)


class StrayStatisticTest(unittest.TestCase):
    """A number in the prose is a number that will be wrong in a month."""

    def test_a_typed_check_count_is_caught(self):
        found = P.stray_statistics("It passes 119 checks today.\n")
        self.assertTrue(found)

    def test_a_typed_milestone_count_is_caught(self):
        self.assertTrue(P.stray_statistics("35 milestones in 14 workstreams.\n"))

    def test_a_typed_byte_count_is_caught(self):
        self.assertTrue(P.stray_statistics("a 135-byte pointer\n"))
        self.assertTrue(P.stray_statistics("a 1.42 GB payload\n"))

    def test_numbers_inside_a_generated_block_are_fine(self):
        block = "<!-- pc5:stats:begin -->\n9 of 35 milestones\n<!-- pc5:stats:end -->"
        self.assertEqual(P.stray_statistics(block), [])

    def test_the_real_readme_has_no_stray_statistics(self):
        self.assertEqual(P.stray_statistics((REPO / "README.md").read_text()), [])


class ValidationRecordTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(REPO / "tools"))
        import validation
        self.validation = validation

    def test_committed_records_are_internally_consistent(self):
        self.assertEqual(self.validation.problems(), [])

    def test_a_record_cannot_claim_passed_without_exit_zero(self):
        bogus = [{"file": "x.json", "schema": "pc5.validation/1", "gate": "check",
                  "result": "passed", "exit_code": 2, "commit": "0" * 40,
                  "date": "2026-11-16"}]
        self.assertTrue(self.validation.problems(bogus))

    def test_a_failed_result_with_exit_zero_is_caught(self):
        bogus = [{"file": "x.json", "schema": "pc5.validation/1", "gate": "check",
                  "result": "failed", "exit_code": 0, "commit": "0" * 40,
                  "date": "2026-11-16"}]
        self.assertTrue(self.validation.problems(bogus))

    def test_an_uncommitted_or_malformed_sha_is_caught(self):
        bogus = [{"file": "x.json", "schema": "pc5.validation/1", "gate": "check",
                  "result": "failed", "exit_code": 1, "commit": "abc", "date": "2026-11-16"}]
        self.assertTrue(self.validation.problems(bogus))

    def test_a_missing_dependency_is_not_a_pass(self):
        self.assertEqual(self.validation.classify(
            "ovmf-test", 2, "NOT TESTED: no QEMU"), "not-tested")
        self.assertEqual(self.validation.classify("stubtest", 2, "install unicorn"), "skipped")
        self.assertEqual(self.validation.classify("boot-test", 77, "SKIP: no node"), "skipped")
        self.assertEqual(self.validation.classify("check", 1, "FAILED"), "failed")
        self.assertEqual(self.validation.classify("check", 0, "OK"), "passed")

    def test_test_counts_are_read_from_the_run_line(self):
        output = ("registry OK\nPASSED: 165 checks, 0 failures\n"
                  "Ran 501 tests in 51s\n\nOK (skipped=2)\n")
        self.assertEqual(self.validation.counts(output),
                         {"passed": 499, "total": 501, "skipped": 2})

    def test_the_summary_prefers_the_test_verdict(self):
        output = "registry OK\nPASSED: 165 checks, 0 failures\nRan 501 tests in 51s\n"
        self.assertEqual(self.validation.summarise(output), "Ran 501 tests in 51s")


class PresentationHygieneTest(unittest.TestCase):
    def test_no_screenshots_are_shipped_as_evidence(self):
        """There is no physical boot to photograph, so there are no photographs."""
        assets = sorted(path.name for path in (REPO / "docs/assets").iterdir())
        self.assertEqual(assets, sorted(P.FIGURES),
                         "docs/assets must contain exactly the generated figures")

    def test_the_build_targets_exist(self):
        makefile = (REPO / "Makefile").read_text(encoding="utf-8")
        self.assertIn("presentation:", makefile)
        self.assertIn("tools/presentation.py", makefile)

    def test_the_presentation_document_explains_the_generation(self):
        text = (REPO / "docs/PRESENTATION.md").read_text(encoding="utf-8")
        for token in ("make presentation", "roadmap.json", "docs/assets/pc5-banner.svg",
                      "pipeline definition"):
            self.assertIn(token, text)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
