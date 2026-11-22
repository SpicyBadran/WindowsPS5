"""A milestone that names a document as its deliverable must have that document.

Why this test exists
-------------------

`M17` — the security and authenticity boundary — names exactly one deliverable in
`docs/architecture/roadmap.json`: `docs/playstation/SECURITY_BOUNDARY.md`. That file did not exist
anywhere in `main` at `52f682c8435956c8210b3189cad23ebea973d2de`, while the milestone was being
worked as analysis, and nothing in the test suite noticed. The path appears once in the whole tree:
in `roadmap.json` itself.

The architecture gate had a hole shaped exactly like this. `tests/test_architecture.py` does check
that named deliverables exist — `test_deliverables_exist_and_are_substantive` — but its
`DELIVERABLES` mapping is a hand-written list of the documents under `docs/architecture/`, so a
deliverable named in the *data* for a milestone in some other directory was outside every check.
That is the general failure mode: a rule enforced over a copied list enforces the list, not the
rule.

So this test derives its expectations from `roadmap.json` — from the structure, not from a second
copy of the answer — and asks a deliberately narrow question, because the wide question would be
wrong:

  A milestone must have the document it names as a deliverable when the milestone is being
  executed (`state == "in_progress"`), or when the milestone's own `blocker` text says it may
  proceed as analysis (`state == "blocked"` and the blocker says "only as analysis").

**The limitation, stated rather than hidden.** The roadmap schema has no field meaning
"this milestone's deliverable is a document written as part of analysis". `M17` is recognised from
the sentence in its `blocker` — data that is authoritative and in the same object, but prose — and
that is the narrowest truthful generalisation available without inventing a schema. A `blocked`
milestone whose deliverable is an artifact to be built later (`M19`'s boot evidence, `M18`'s
loader) is *correctly* not required to have it yet, and the fourth case below pins that, so the
rule cannot silently widen itself into demanding that the destination be finished.

A `not_started` milestone is never demanded anything. A named deliverable that is not a
repository path (``psm/ — evidence registry, rule engine``, ``the repository-root package as a Git
LFS pointer only``) is not a document and is not checked: the test compares paths, not vocabulary.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROADMAP = os.path.join(ROOT, "docs", "architecture", "roadmap.json")

# A deliverable is a *named document* when it is written as a repository-relative path: a known
# top-level directory, a slash, then no spaces. That is what "docs/playstation/X.md" is, and what
# "kernel/usb/" (a directory to be created by a not_started milestone) and "psm/ — registry, ..."
# are not.
DOCUMENT = re.compile(r"^(?:docs|tools|tests|psm|kernel|boot|ci|evidence)/[^\s]+\.(?:md|json|py|c|h)$")

# The sentence in a blocker that makes a blocked milestone's analysis deliverable enforceable.
ANALYSIS_LICENCE = "only as analysis"


def requires_its_documents(milestone: dict) -> bool:
    """True when this milestone's state obliges it to have written what it names."""
    if milestone.get("state") == "in_progress":
        return True
    if milestone.get("state") == "blocked" and ANALYSIS_LICENCE in str(milestone.get("blocker", "")):
        return True
    return False


def named_documents(milestone: dict) -> list:
    return [d for d in milestone.get("deliverables", []) if DOCUMENT.match(d)]


def missing_documents(milestones: list, root: str) -> list:
    """Every (milestone id, deliverable) pair that is obliged and absent under `root`."""
    gaps = []
    for milestone in milestones:
        if not requires_its_documents(milestone):
            continue
        for document in named_documents(milestone):
            if not os.path.exists(os.path.join(root, document)):
                gaps.append((milestone["id"], document))
    return gaps


def load_roadmap(path: str = ROADMAP) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


class NamedDeliverableTest(unittest.TestCase):
    def test_every_obliged_document_deliverable_exists(self):
        data = load_roadmap()
        gaps = missing_documents(data["milestones"], ROOT)
        self.assertEqual(
            gaps, [],
            "milestones are executing (or authorised as analysis) without a document they name:\n"
            + "\n".join(f"  {mid}: {doc}" for mid, doc in gaps),
        )

    def test_m17_names_the_analysis_deliverable_and_it_is_substantive(self):
        """`M17`'s one deliverable, checked as a document rather than as a filename."""
        data = load_roadmap()
        milestone = next(m for m in data["milestones"] if m["id"] == "M17")
        self.assertEqual(
            named_documents(milestone), ["docs/playstation/SECURITY_BOUNDARY.md"],
            "M17's deliverable list was expected to be exactly the named analysis document",
        )
        self.assertEqual(milestone["state"], "blocked",
                         "M17's analysis may be published; the milestone stays blocked")
        self.assertIn(ANALYSIS_LICENCE, milestone["blocker"])

        path = os.path.join(ROOT, named_documents(milestone)[0])
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        lines = text.splitlines()
        headings = [l for l in lines if re.match(r"^## ", l)]
        self.assertGreaterEqual(len(lines), 150, f"{path} is too thin to be M17's analysis")
        self.assertGreaterEqual(len(headings), 8, f"{path} has too few sections to be an inventory")
        # The claims that make it a boundary document rather than an essay.
        for needle in ("RESTRICTED", "UNKNOWN", "falsifier", "trust anchor", "blocked"):
            self.assertIn(needle.lower(), text.lower(), f"{path} never addresses {needle!r}")
        for refusal in ("decrypt", "bypass", "key"):
            self.assertIn(refusal, text.lower(),
                          f"{path} must state the boundary item {refusal!r} explicitly")
        self.assertRegex(text, r"(?i)not legal advice|not a plan of record|analysis, not")

    def test_the_check_fires_when_a_named_deliverable_is_absent(self):
        """Non-vacuity, measured in a fixture rather than assumed.

        A directory-shaped stand-in: a roadmap with one in_progress milestone naming a document
        that does not exist, beside one that does. The same function the first case uses reports
        exactly the absent one. If this fixture ever passes by reporting nothing, the first case
        is decorative.
        """
        with tempfile.TemporaryDirectory() as tmp:
            docs = os.path.join(tmp, "docs")
            os.makedirs(docs)
            with open(os.path.join(docs, "present.md"), "w", encoding="utf-8") as handle:
                handle.write("# present\n")
            milestones = [
                {"id": "MX", "state": "in_progress",
                 "deliverables": ["docs/present.md", "docs/absent.md"]},
                {"id": "MY", "state": "blocked", "blocker": "blocked on hardware, not analysis",
                 "deliverables": ["docs/also-absent.md"]},
                {"id": "MZ", "state": "not_started",
                 "deliverables": ["docs/way-in-the-future.md"]},
            ]
            gaps = missing_documents(milestones, tmp)
        self.assertEqual(gaps, [("MX", "docs/absent.md")],
                         "the check must report the absent obliged document, and only that one")

    def test_a_blocked_build_milestone_is_not_demanded_a_document(self):
        """The scope limit, pinned: `M19` may not be produced by a test."""
        data = load_roadmap()
        milestone = next(m for m in data["milestones"] if m["id"] == "M19")
        self.assertEqual(milestone["state"], "blocked")
        self.assertNotIn(ANALYSIS_LICENCE, str(milestone.get("blocker", "")))
        self.assertFalse(requires_its_documents(milestone),
                         "M19's deliverable is boot evidence from the destination itself; no test "
                         "may demand it, and none here does")


if __name__ == "__main__":
    unittest.main()
