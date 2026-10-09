"""Checks for check_bible.py against the sample bible and, when present, the Phase 4 run outputs.

Run: python tests/test_bible.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/worldloom/skills/worldloom/scripts/check_bible.py"
sys.path.insert(0, str(SCRIPT.parent))
import check_bible as C  # noqa: E402

SAMPLE = (ROOT / "worldloom_source/SAMPLE_TEST_BIBLE_FOR_P3.md").read_text(encoding="utf-8")


def swap(old, new):
    def mutate(text):
        assert old in text, old
        return text.replace(old, new, 1)
    return mutate


# (name, text expected in a failure, mutation of the bible under test, compare against the sample?)
MUTATIONS = [
    ("TIER line removed", "line 1 must be", swap("TIER: Tablet\n", ""), False),
    ("section 4 heading removed", "4. Supporting Cast & Antagonists", swap("4. Supporting Cast & Antagonists\n", ""), False),
    ("banned name added", "banned name: Marcus", swap("Hollis Bray", "Marcus Bray"), False),
    ("code fence", "code fence", lambda t: "TIER: Tablet\n```\n" + t.split("\n", 1)[1], False),
    ("second Player Character line", "exactly one", swap("Player Character: Mira Fenlow", "Player Character: Mira Fenlow\nPlayer Character: Josselin Varlen"), False),
    ("entity renamed in revision", "named entity removed or renamed: Hollis Bray", swap("Hollis Bray\nNarrative Weight", "Hollis Brandt\nNarrative Weight"), True),
    ("entity added in revision", "named entity added: The Counting House", swap("House Varlen\nNarrative Weight: Supporting", "House Varlen\nNarrative Weight: Supporting\nThe Counting House\nNarrative Weight: Background"), True),
    ("Narrative Weight changed", "Narrative Weight or Role changed for House Varlen", swap("House Varlen\nNarrative Weight: Supporting", "House Varlen\nNarrative Weight: Core"), True),
    ("Role changed", "Narrative Weight or Role changed for Perrin Ashgrove", swap("Role: Rival", "Role: Antagonist"), True),
    ("labelled field removed", "labelled fields differ", swap("Logline:", "Summary:"), True),
    ("Player Character changed", "Player Character line changed", swap("Player Character: Mira Fenlow", "Player Character: Josselin Varlen"), True),
]


def failures(text, original=None):
    return [f for _, fails in C.check(text, original) for f in fails]


def main():
    assert failures(SAMPLE) == [], failures(SAMPLE)
    assert failures(SAMPLE, SAMPLE) == []
    assert failures(SAMPLE.replace("\n", "\r\n"), SAMPLE) == [], "line endings must not matter"
    print("sample bible passes structure, and passes as a revision of itself")

    for name, expected, mutate, against in MUTATIONS:
        got = failures(mutate(SAMPLE), SAMPLE if against else None)
        assert any(expected in f for f in got), "%s: no failure with %r in %s" % (name, expected, got)
    print("%d mutations rejected, each naming the fault" % len(MUTATIONS))

    reworded = SAMPLE.replace("Logline:", "Logline: A changed hook.", 1) + "\nA prose line with a colon: still prose."
    assert failures(reworded, SAMPLE) == [], "rewording a field or adding prose is allowed"
    print("a reworded field and an added prose line pass")

    lines = lambda text: C.parse(text)[0]
    lead = "A Third Lead\nNarrative Weight: Core\n"
    assert C.cast_warnings(lines(SAMPLE)) == [], "the sample's Main Cast fits Tablet"
    third = SAMPLE.replace("\n4. Supporting Cast & Antagonists\n", "\n" + lead + "\n4. Supporting Cast & Antagonists\n", 1)
    warned = C.cast_warnings(lines(third))
    assert len(warned) == 1 and "Main Cast is 3" in warned[0] and "Scroll or Opus" in warned[0], warned
    assert failures(third) == [], "a large cast warns, it never fails"
    opus = third.replace("TIER: Tablet", "TIER: Opus").replace(lead, lead * 3)
    assert "Opus is the largest" in C.cast_warnings(lines(opus))[0]
    print("Main Cast above the tier's size warns and does not fail")

    runs = [d for d in sorted((ROOT / "worldloom-output").glob("*")) if (d / "bible_v1.txt").exists() and (d / "bible_v2.txt").exists()]
    for d in runs:
        v1, v2 = ((d / n).read_text(encoding="utf-8") for n in ("bible_v1.txt", "bible_v2.txt"))
        assert failures(v1) == [] and failures(v2, v1) == [], (d.name, failures(v1), failures(v2, v1))
    print("%d run folder(s) under worldloom-output pass (v1 structure, v2 against v1)" % len(runs))

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "v1.txt").write_text(SAMPLE, encoding="utf-8")
        (tmp / "v2.txt").write_text(SAMPLE.replace("Role: Rival", "Role: Antagonist"), encoding="utf-8")
        run = lambda *args: subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
        ok, bad, gone = run(tmp / "v1.txt"), run(tmp / "v2.txt", "--against", tmp / "v1.txt"), run(tmp / "none.txt")
        assert ok.returncode == 0 and "RESULT: PASS 1/1" in ok.stdout and "WARN" not in ok.stdout, ok
        (tmp / "big.txt").write_text(third, encoding="utf-8")
        big = run(tmp / "big.txt")
        assert big.returncode == 0 and "WARN Main Cast is 3" in big.stdout and "RESULT: PASS 1/1" in big.stdout, big
        assert bad.returncode == 1 and "RESULT: FAIL 1/2" in bad.stdout and "Perrin Ashgrove" in bad.stdout, bad
        assert gone.returncode == 1 and "FAIL cannot read" in gone.stdout, gone
    print("CLI: pass (exit 0), cast warning (exit 0), failed revision (exit 1), unreadable file (exit 1)")
    print("ALL PASS")


if __name__ == "__main__":
    main()
