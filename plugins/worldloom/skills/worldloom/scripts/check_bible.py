"""Structure checks for a Worldloom Story Bible, and "revise, don't recast" checks for a revision.

Usage: python check_bible.py BIBLE [--against ORIGINAL]
Exit 0 when every check passes, 1 otherwise. Prints PASS/FAIL lines with names and labels only,
never bible prose. Stdlib only.
"""
import argparse
import re
import sys
from pathlib import Path

SECTIONS = ["1. Working Title, Tags & Logline", "2. The World", "3. Main Cast", "4. Supporting Cast & Antagonists",
            "5. World State & Dramatic Situation", "6. Core Memory & Tone", "7. Generation Notes"]
# Field labels the bible format defines. Other "Something: ..." lines are prose and are ignored.
# P1's MAIN_CAST row: the cast size each tier's budget assumes.
MAIN_CAST = {"Tablet": 2, "Scroll": 3, "Opus": 4}
LABELS = ["Working Title", "Genres", "Logline", "Hard Rules", "Player Character", "Narrative Weight", "Role", "Age",
          "Gender", "Occupation", "Appearance", "Look", "Personality", "Background", "Wants", "Want", "Fears",
          "Reflex under pressure", "Source of friction", "Relationships at start", "Skills & Items", "Voice",
          "Sample line", "Pull", "Function", "Texture", "If unopposed", "Status Quo",
          "Recent Events & Temporary Conditions", "Known Upcoming", "Active Pressures", "Possible Directions",
          "Open Questions & Secrets", "Core Memory Candidates", "Tone & Atmosphere", "Genre Contract",
          "Tag Conflict Resolutions", "Consistency Fixes", "Starting Point", "Cast Sizing Decisions"]
LABEL = re.compile(r"(?:- )?(%s):" % "|".join(map(re.escape, LABELS)))
BANNED = re.compile(r"\b(Elara|Lyra|Thorne|Valerius|Kael|Kaelen|Ava|Marcus)\b")


def parse(text):
    """Return (lines, entities, labels). entities: name -> (Narrative Weight, Role)."""
    lines = [l.strip() for l in text.replace("\r\n", "\n").split("\n")]
    entities = {}
    for i, line in enumerate(lines):
        if line.startswith("Narrative Weight:") and i:
            role = lines[i + 1].split(":", 1)[1].strip() if i + 1 < len(lines) and lines[i + 1].startswith("Role:") else ""
            entities[lines[i - 1]] = (line.split(":", 1)[1].strip(), role)
    labels = [m.group(1) for m in map(LABEL.match, lines) if m]
    return lines, entities, labels


def structure(lines):
    fails = []
    if not lines or not re.fullmatch(r"TIER: (Tablet|Scroll|Opus)", lines[0]):
        fails.append("line 1 must be \"TIER: Tablet\", \"TIER: Scroll\" or \"TIER: Opus\"")
    found = [l for l in lines if l in SECTIONS]
    if found != SECTIONS:
        missing = [s for s in SECTIONS if found.count(s) != 1]
        fails.append("section headings missing, repeated or out of order: %s" % (", ".join(missing) or "order"))
    players = [l for l in lines if l.startswith("Player Character:")]
    if len(players) != 1 or not players[0].split(":", 1)[1].strip():
        fails.append("expected exactly one \"Player Character: <name>\" line, found %d" % len(players))
    if any(l.startswith("```") for l in lines):
        fails.append("code fence found; the bible file is plain text")
    # A rename logged as "original → new" may quote a banned name the user supplied.
    hits = sorted({h for l in lines if "→" not in l and "->" not in l for h in BANNED.findall(l)})
    if hits:
        fails.append("banned name: %s" % ", ".join(hits))
    return fails


def cast_warnings(lines):
    """Main Cast above the size the tier's budget assumes. Never a failure: the user's cast always wins."""
    tier = lines[0][6:] if lines and lines[0].startswith("TIER: ") else ""
    if tier not in MAIN_CAST or SECTIONS[2] not in lines or SECTIONS[3] not in lines:
        return []
    cast = sum(l.startswith("Narrative Weight:") for l in lines[lines.index(SECTIONS[2]):lines.index(SECTIONS[3])])
    if cast <= MAIN_CAST[tier]:
        return []
    tiers = list(MAIN_CAST)
    bigger = tiers[tiers.index(tier) + 1:]
    return ["Main Cast is %d; the %s lorebook budget assumes %d, so entries will be short and Stage 3 may not fit. %s" % (
        cast, tier, MAIN_CAST[tier],
        "A larger tier (%s) gives them room, if your NovelAI plan has it." % " or ".join(bigger) if bigger
        else "Opus is the largest tier.")]


def revision(new, old):
    """new, old: results of parse(). The revision may change what is true, never who or what exists."""
    fails = []
    (_, ents, labels), (_, old_ents, old_labels) = new, old
    for name in sorted(set(old_ents) - set(ents)):
        fails.append("named entity removed or renamed: %s" % name)
    for name in sorted(set(ents) - set(old_ents)):
        fails.append("named entity added: %s" % name)
    for name in sorted(set(ents) & set(old_ents)):
        if ents[name] != old_ents[name]:
            fails.append("Narrative Weight or Role changed for %s: %s -> %s" % (
                name, " / ".join(filter(None, old_ents[name])), " / ".join(filter(None, ents[name]))))
    player = lambda lines: [l for l in lines if l.startswith("Player Character:")]
    if player(new[0]) != player(old[0]):
        fails.append("Player Character line changed")
    if labels != old_labels:
        i = next((k for k, (a, b) in enumerate(zip(labels, old_labels)) if a != b), min(len(labels), len(old_labels)))
        at = lambda seq: seq[i] if i < len(seq) else "end of file"
        fails.append("labelled fields differ at field %d: original has %r, revision has %r" % (i + 1, at(old_labels), at(labels)))
    return fails


def check(text, original=None):
    """Return a list of (check name, [failure messages])."""
    parsed = parse(text)
    results = [("structure", structure(parsed[0]))]
    if original is not None:
        results.append(("revision keeps cast and layout", revision(parsed, parse(original))))
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bible")
    ap.add_argument("--against", help="the original bible this one revises")
    a = ap.parse_args()
    try:
        text = Path(a.bible).read_text(encoding="utf-8")
        original = Path(a.against).read_text(encoding="utf-8") if a.against else None
    except (OSError, ValueError) as e:
        print("FAIL cannot read: %s" % e)
        sys.exit(1)
    results = check(text, original)
    for name, fails in results:
        print("%s %s" % ("FAIL" if fails else "PASS", name))
        for f in fails:
            print("     - " + f)
    for w in cast_warnings(parse(text)[0]):
        print("WARN " + w)
    failed = sum(1 for _, fails in results if fails)
    print("RESULT: %s %d/%d checks passed" % ("FAIL" if failed else "PASS", len(results) - failed, len(results)))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
