"""`make check` has to run the suite even when a gate is broken, and keep its exit code.

Why this exists
---------------
`check` used to list its documentation and contract gates as *prerequisites*:

    check: unit psm docs-check citations-check presentation-check brand-check
            python3 -m unittest discover -s tests -p 'test_*.py' -v

Make stops when a prerequisite fails, so one broken link in an evidence document, or one
roadmap milestone pointing at a file that does not exist yet, ended the run *before* the
suite started.  The exit code then described the gate, and a developer asking "did my
change break a test?" got no answer at all -- in this repository's history that shape
cost real debugging time, because the message names a document, not a test.

Why a test rather than a review comment
---------------------------------------
The fix is three lines of shell and it is exactly the kind of thing a later "cleanup"
reverts, because the prerequisite form is shorter and looks equivalent.  So the
behaviour is pinned here by *executing* make, not by grepping the Makefile.

How that works
--------------
The recipe under test is extracted from the real `Makefile`, so this cannot drift into
checking a copy of it.  It is pasted into a scratch project whose `unit`, `psm`,
`docs-check` and friends are stubs that append to a log and exit with a chosen status.
Then `make check` runs there and the log says who actually executed, in what order.

Four cases:

  * everything passes -- suite first, then every gate, exit 0;
  * a late gate fails -- the suite still ran, the gate is named, and the gates after
    it are skipped;
  * the suite fails -- it is named, and no gate runs afterwards;
  * the *old* prerequisite form, built from the same stubs as a control, where a failing
    gate really does prevent the suite from running.  Without this last case the first
    three could be satisfied by a stub project that merely happens to be ordered.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAKEFILE = os.path.join(REPO, "Makefile")
GATES = ("unit", "psm", "docs-check", "citations-check", "presentation-check",
         "brand-check")

# The historical form, kept here deliberately rather than derived from the repository:
# it is the mutation that the fix removes, and the control that proves the other three
# cases are sensitive to something.
OLD_FORM = "check: " + " ".join(GATES) + "\n" \
    "\tpython3 -m unittest discover -s tests -p 'test_*.py' -v\n"


def extract_check_recipe(path=MAKEFILE):
    """The `check` rule's shell text, dedented, straight out of the real Makefile.

    Refuses to invent a recipe: if `check:` takes prerequisites, or the rule cannot be
    found unambiguously, that is itself the regression, and saying so is more useful
    than silently testing something else.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(r"^check:([^\n]*)\n((?:\t[^\n]*\n)+)", text, re.M)
    if match is None:
        raise AssertionError("no `check:` rule with a recipe found in Makefile")
    prereqs = match.group(1).strip()
    recipe = "\n".join(line[1:] for line in match.group(2).splitlines())
    return prereqs, recipe


class MakeRunner:
    """A scratch project whose only real content is the extracted `check` recipe."""

    def __init__(self, check_rule, gate_status=None, suite_fails=False):
        self.dir = tempfile.TemporaryDirectory(prefix="pc5-check-contract-")
        root = self.dir.name
        self.log = os.path.join(root, "log.txt")
        os.makedirs(os.path.join(root, "tests"))
        with open(os.path.join(root, "Makefile"), "w", encoding="utf-8") as handle:
            handle.write(self.makefile_text(check_rule, gate_status))
        self.write_suite(suite_fails)

    def makefile_text(self, check_rule, gate_status):
        lines = ["SHELL := /bin/sh\n",
                 "# Every leg is a stub: the point is who runs, in what order, and\n"
                 "# what status the recipe hands back -- not what the real gates do.\n"]
        for gate in GATES:
            status = (gate_status or {}).get(gate, 0)
            lines.append("%s:\n\t@echo %s >> %s%s\n"
                         % (gate, gate, self.log,
                            "; exit %d" % status if status else ""))
        lines.append(check_rule if check_rule.endswith("\n") else check_rule + "\n")
        return "\n".join(lines)

    def write_suite(self, fails):
        """A `tests/` directory that either passes or fails with a known code.

        A failing test exits unittest with status 1, so `check`'s code has to be 1 for
        the suite case and cannot be confused with a gate's chosen status.
        """
        body = ("import unittest\n\n\nclass Suite(unittest.TestCase):\n    def test_ok"
                "(self):\n        self.assertEqual(1, 1)\n")
        if fails:
            body = body.replace("self.assertEqual(1, 1)",
                                "self.fail('deliberate suite failure')")
        with open(os.path.join(self.dir.name, "tests", "test_dummy.py"),
                  "w", encoding="utf-8") as handle:
            handle.write(body)

    def run(self):
        # MAKEFLAGS/MFLAGS are dropped on purpose.  This test runs inside the suite,
        # which is often started *by* `make check`, and make exports those variables
        # to every child: inheriting `-k` from `make -k check` would let the scratch
        # project keep going past a failing prerequisite and the control case would
        # then "prove" the old form was fine.  A control has to be insulated from the
        # flags of the run that is checking it.
        env = {key: value for key, value in os.environ.items()
               if key not in ("MAKEFLAGS", "MFLAGS")}
        result = subprocess.run(
            ["make", "--no-print-directory", "-C", self.dir.name, "check"],
            capture_output=True, text=True, timeout=180, env=env)
        ran = []
        if os.path.exists(self.log):
            with open(self.log, encoding="utf-8") as handle:
                ran = [line.strip() for line in handle if line.strip()]
        # unittest writes its report to stderr, so any assertion about what the suite
        # said has to look at both streams; checking stdout alone would "prove" the
        # suite never ran.
        return {"exit": result.returncode, "ran": ran,
                "stdout": result.stdout, "stderr": result.stderr,
                "combined": result.stdout + result.stderr}

    def close(self):
        self.dir.cleanup()


class CheckRuleShape(unittest.TestCase):
    """What the Makefile itself promises, before any of it is executed."""

    def test_check_takes_no_prerequisites(self):
        prereqs, _ = extract_check_recipe()
        self.assertEqual(
            prereqs, "",
            "`check` must not list gates as prerequisites: make exits on a failed "
            "prerequisite and the suite would never run")

    def test_the_suite_precedes_every_gate_leg(self):
        _, recipe = extract_check_recipe()
        # `unittest discover` must be reached before the loop that invokes the gates;
        # position in the shell text is what decides whether a gate can pre-empt it.
        suite = recipe.find("unittest discover")
        gates = recipe.find("$(MAKE)")
        self.assertGreaterEqual(suite, 0, "the recipe does not run the suite at all")
        self.assertGreaterEqual(gates, 0, "the recipe does not run the gates at all")
        self.assertLess(suite, gates,
                        "the suite has to be the first thing `check` runs, not a leg "
                        "that an earlier failure can skip")

    def test_the_old_form_is_still_recognisable(self):
        # Guards the control: if this test's copy of the historical rule stopped
        # matching the shape that made the bug, the control case proves nothing.
        self.assertTrue(OLD_FORM.startswith("check: unit psm docs-check"))


class CheckExecution(unittest.TestCase):
    """`make check` executed, four ways."""

    projects = []

    @classmethod
    def tearDownClass(cls):
        for project in cls.projects:
            project.close()
        cls.projects = []

    def project(self, gate_status=None, suite_fails=False, rule=None):
        prereqs, recipe = extract_check_recipe()
        check_rule = rule if rule is not None else "check:\n" + "".join(
            "\t" + line + "\n" for line in recipe.splitlines())
        handle = MakeRunner(check_rule, gate_status=gate_status,
                            suite_fails=suite_fails)
        type(self).projects.append(handle)
        return handle

    def test_everything_passes(self):
        outcome = self.project().run()
        self.assertEqual(outcome["exit"], 0, outcome["stdout"] + outcome["stderr"])
        self.assertEqual(outcome["ran"], list(GATES),
                         "the suite and every gate, in order")

    def test_a_broken_gate_does_not_silence_the_suite(self):
        outcome = self.project(gate_status={"docs-check": 3}).run()
        # 2, not 3: `make` collapses any failed command to status 2, which is why the
        # leg has to be *named* -- the code alone cannot say what went wrong.
        self.assertEqual(outcome["exit"], 2, outcome["stderr"])
        self.assertIn("docs-check", outcome["ran"])
        self.assertEqual(outcome["ran"], ["unit", "psm", "docs-check"],
                         "gates after the failure are skipped, and the ones before it "
                         "ran -- so the suite really was reached")
        self.assertIn("make check FAILED in 'docs-check'", outcome["stdout"])
        # The suite leg prints a unittest summary; if it never ran there would be none.
        self.assertRegex(outcome["combined"], r"Ran 1 test")

    def test_a_failing_suite_is_named_and_reaches_the_caller(self):
        outcome = self.project(suite_fails=True).run()
        # The suite's own status is 1 and the recipe forwards it, but make reports 2
        # for any failure.  The failure *text* is what a caller can act on, and it
        # says `suite` rather than leaving unittest's output to be inferred.
        self.assertEqual(outcome["exit"], 2, outcome["stderr"])
        self.assertRegex(outcome["combined"], r"FAILED \(failures=1\)")
        self.assertRegex(outcome["combined"], r"deliberate suite failure")
        self.assertIn("make check FAILED in 'suite'", outcome["stdout"])
        self.assertEqual(outcome["ran"], [],
                         "no gate runs once the suite has failed: the first failure "
                         "is the one reported")

    def test_control_the_prerequisite_form_reaches_nobody(self):
        """The historical rule, same stubs: a failing gate swallows the suite.

        This is the case the fix exists for, so it is worth stating precisely what the
        old form does: make stops at the first failing prerequisite, `check`'s own
        recipe never starts, and the output says only that a command failed.  Nothing
        in it mentions a test.
        """
        outcome = self.project(gate_status={"docs-check": 3}, rule=OLD_FORM).run()
        self.assertNotIn("Ran 1 test", outcome["combined"],
                         "with prerequisites, a failing gate must have prevented the "
                         "suite -- if the suite ran here, the control proves nothing "
                         "and the bug was never where the comment says it was")
        self.assertIn("docs-check", outcome["ran"])
        self.assertNotIn("brand-check", outcome["ran"],
                         "gates after the failure are skipped by make itself")
        self.assertEqual(outcome["exit"], 2,
                         "both forms report make's generic error status; only the "
                         "new one can also say which leg produced it")
        self.assertNotIn("make check FAILED in", outcome["stdout"],
                         "the old form cannot name the leg it skipped, because it "
                         "never got there")


if __name__ == "__main__":
    unittest.main(verbosity=2)
