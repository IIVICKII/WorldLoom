"""Checks for build_scenario.py and validate_scenario.py against the known-good reference.

Run: python tests/test_scripts.py
"""
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "plugins/worldloom/skills/worldloom-compile/scripts"
sys.path.insert(0, str(SCRIPTS))
import build_scenario as B  # noqa: E402
import validate_scenario as V  # noqa: E402

REF = json.loads((ROOT / "worldloom_source/The_Quiet_Ledger.scenario").read_text(encoding="utf-8"))
SP = V.FIXED["systemPrompt"]


def content_from(scenario):
    """Reverse the builder: recover the story-specific content a model would have written."""
    sp = scenario["messageSettings"]["systemPrompt"].split("\n")
    pre = scenario["messageSettings"]["prefill"].split("\n")
    event = sp[sp.index("## Dynamic Event System") + 1:]
    event = event[:next(i for i, l in enumerate(event) if l.startswith("## "))]
    entries, extra = [], ""
    for e in scenario["lorebook"]["entries"]:
        role = V.role_of(e)
        if role == "voice_guard":
            extra = e["text"].split("\n")[2][len(V.FIXED["voiceGuard"][2]):].strip()
            continue
        entries.append({"role": role, "name": e["displayName"], "text": e["text"], "keys": e["keys"]})
    return {
        "title": scenario["title"], "description": scenario["description"], "prologue": scenario["prompt"],
        "tags": scenario["tags"], "memory": scenario["context"][0]["text"], "authorsNote": scenario["context"][1]["text"],
        "systemPrompt": {
            "romance": "## Showing Attraction" in sp, "litrpg": False, "examples": "## Examples" in sp,
            "scenarioBans": [l[len("- NEVER use: "):] for l in sp
                             if l.startswith("- NEVER use: ") and l not in (SP["ozoneLine"], SP["analyticalLine"])],
            "eventSystem": [l[2:] for l in event]},
        "prefillContinuation": [l[2:] for l in pre[pre.index("**Continuation:**") + 1:-2]],
        "voiceGuardExtra": extra,
        "phraseBias": [{"words": [p["sequence"] for p in g["phrases"]], "bias": g["bias"]}
                       for g in scenario["phraseBiasGroups"][1:]],
        "entries": entries,
    }


def entry(d, name):
    return next(e for e in d["lorebook"]["entries"] if e["displayName"] == name)


def set_text(d, name, old, new):
    e = entry(d, name)
    assert old in e["text"], old
    e["text"] = e["text"].replace(old, new)


def swap_keys(d):
    items = list(d.items())
    items[1], items[2] = items[2], items[1]
    d.clear()
    d.update(items)


def sp_replace(d, old, new):
    assert old in d["messageSettings"]["systemPrompt"], old
    d["messageSettings"]["systemPrompt"] = d["messageSettings"]["systemPrompt"].replace(old, new)


# (name, expected failing check, mutation)
MUTATIONS = [
    ("top-level key order", 1, swap_keys),
    ("author changed", 1, lambda d: d.update(author="Someone")),
    ("temperature changed", 2, lambda d: d["settings"]["parameters"].update(temperature=1.0)),
    ("comma bias group altered", 2, lambda d: d["phraseBiasGroups"][0].update(bias=-1.0)),
    ("DEFAULT_ENTRY altered", 2, lambda d: d["contextDefaults"]["loreDefaults"][0].update(searchRange=2000)),
    ("categories not empty", 3, lambda d: d["lorebook"]["categories"].append({"name": "People"})),
    ("entry category set", 4, lambda d: entry(d, "Mira Fenlow").update(category="People")),
    ("duplicate id", 5, lambda d: entry(d, "Hollis Bray").update(id=entry(d, "Mira Fenlow")["id"])),
    ("random uuid", 5, lambda d: entry(d, "Glossary").update(id="125f8dfa-a2a3-492c-b92f-c38cbf7aa8a2")),
    ("Operator Reference not last", 6, lambda d: d["lorebook"]["entries"].insert(0, d["lorebook"]["entries"].pop())),
    ("Voice Guard missing", 6, lambda d: d["lorebook"]["entries"].remove(entry(d, "Voice Guard"))),
    ("wrong priority", 7, lambda d: entry(d, "Story So Far")["contextConfig"].update(budgetPriority=800)),
    ("character searchRange 1000", 7, lambda d: entry(d, "Mira Fenlow").update(searchRange=1000)),
    ("Operator Reference keyed", 7, lambda d: entry(d, "Operator Reference").update(keys=["secret"])),
    ("Operator Reference enabled", 7, lambda d: entry(d, "Operator Reference").update(enabled=True)),
    ("Keys: line in text", 8, lambda d: set_text(d, "Hollis Bray", "\nLook:", "\nKeys: hollis\nLook:")),
    ("Voice Guard reworded", 8, lambda d: set_text(d, "Voice Guard", "Distinct: No two", "Distinct: Few")),
    ("Now line", 9, lambda d: set_text(d, "Story So Far", "Earlier:", "Now: Mira arrives.\nEarlier:")),
    ("Upcoming label changed", 9, lambda d: set_text(d, "Story So Far", "Upcoming (not happened yet):", "Upcoming:")),
    ("ATTG title mismatch", 10, lambda d: d.update(title="The Loud Ledger")),
    ("two-line Memory", 10, lambda d: d["context"][0].update(text=d["context"][0]["text"] + "\nAldwick is a town.")),
    ("style line missing", 11, lambda d: d["context"][1].update(text="[ Narration: warm. ]")),
    ("blank line in Prologue", 12, lambda d: d.update(prompt=d["prompt"].replace("\n", "\n\n", 1))),
    ("header removed", 13, lambda d: sp_replace(d, "## Voice Discipline\n", "")),
    ("unfilled marker", 13, lambda d: sp_replace(d, "## Before Output", "[SCENARIO BANS: add lines here]\n## Before Output")),
    ("Examples on Tablet", 13, lambda d: sp_replace(d, "## Before Output", "## Examples\nFlow. Bad: x. Good: y.\n## Before Output")),
    ("Prefill tail changed", 13, lambda d: d["messageSettings"].update(prefill=d["messageSettings"]["prefill"] + "\n")),
    ("bias too strong", 14, lambda d: d["phraseBiasGroups"][1].update(bias=1.5)),
    ("two-word bias phrase", 14, lambda d: d["phraseBiasGroups"][1]["phrases"][0].update(sequence="lamp oil")),
    ("banned name in Prologue", 15, lambda d: d.update(prompt=d["prompt"].replace("Hollis Bray", "Marcus Bray", 1))),
    ("banned name as key", 15, lambda d: entry(d, "Hollis Bray")["keys"].append("thorne")),
    ("lorebook over cap", 16, lambda d: set_text(d, "House Varlen", "Purpose:", "Purpose: " + "old stone and river fog, " * 60)),
    ("Author's Note over cap", 16, lambda d: d["context"][1].update(text=d["context"][1]["text"] + " rain" * 300)),
]


def add(d, key, text):
    d[key] = d[key] + text


def note_add(d, text):
    d["context"][1]["text"] += text


# (name, text expected in a warning, mutation); none of these may fire on the reference
WARNINGS = [
    ("lorebook over fit target", "over the fit target", lambda d: set_text(d, "House Varlen", "Purpose:", "Purpose: " + "old stone and river fog, " * 10)),
    ("last spoken line is the player character's", "last spoken line", lambda d: d.update(prompt=d["prompt"].replace('"I\'ll bring tea," he said', '"I\'ll bring tea," I said'))),
    ("Prologue ends on a question", "ends on a question", lambda d: add(d, "prompt", "\nWho had opened it?")),
    ("appositive after said", "appositive", lambda d: add(d, "prompt", '\n"Yes," Hollis said, his voice low.')),
    ("not X but Y", "not X but Y", lambda d: add(d, "prompt", "\nIt was not a house but a ledger.")),
    ("leak word in Core Memory", "Core Memory: possible premise leak word 'will'", lambda d: add(entry(d, "Core Memory"), "text", "\nMira will inherit the house.")),
    ("leak word in Prologue", "Prologue: possible premise leak word 'one day'", lambda d: add(d, "prompt", "\nOne day the house would fall.")),
    ("leak word in Author's Note", "Author's Note: possible premise leak word 'eventually'", lambda d: note_add(d, "\n[ Warmth eventually wins. ]")),
    ("bias word already banned", "already in a NEVER use line", lambda d: sp_replace(d, "## Before Output", "- NEVER use: %s\n## Before Output" % d["phraseBiasGroups"][1]["phrases"][0]["sequence"])),
    ("ATTG Genre not in tags", "is not among", lambda d: d["tags"].pop()),
    ("tag not lowercase", "is not lowercase", lambda d: d["tags"].append("Rainy")),
    ("cast name in Author's Note", "Author's Note names 'Mira Fenlow'", lambda d: note_add(d, "\n[ Mira watches closely. ]")),
    ("duplicate key, different case", "is on both", lambda d: entry(d, "Hollis Bray")["keys"].append(entry(d, "Mira Fenlow")["keys"][0].upper())),
]


def main():
    errors, warnings = V.validate(REF, "Tablet")
    assert not errors, errors
    print("reference passes %d checks, %d warning(s)" % (len(V.CHECKS), len(warnings)))

    built = B.build(content_from(REF))
    assert built == REF, [k for k in REF if built.get(k) != REF[k]]
    assert json.dumps(built) == json.dumps(REF), "key order differs from the reference"
    print("round trip: content -> build equals the reference, key order included")

    full = dict(content_from(REF), systemPrompt={"romance": True, "litrpg": True, "examples": True,
                                                 "scenarioBans": [], "eventSystem": ["If x goes unaddressed, y may happen."]})
    sp = B.build(full)["messageSettings"]["systemPrompt"]
    assert "## Examples" in sp and "Attraction. Bad:" in sp and "- Lines starting with - are system" in sp and "[" + "END" not in sp
    plain = B.system_prompt({"examples": True, "eventSystem": ["x"]})
    assert "Attraction. Bad:" not in plain and "## Showing Attraction" not in plain and not V.SLOT.search(plain)
    assert B.prefill(None).split("\n")[-5:-2] == ["- " + l for l in V.FIXED["prefill"]["defaultContinuation"]]
    print("template blocks: romance, LitRPG, examples and default prefill fill correctly")

    for name, check, mutate in MUTATIONS:
        d = copy.deepcopy(REF)
        mutate(d)
        failed = {n for n, _ in V.validate(d, "Tablet")[0]}
        assert check in failed, "%s: expected check %d to fail, failed: %s" % (name, check, sorted(failed))
    print("%d mutations rejected, each by the expected check" % len(MUTATIONS))

    for name, expected, mutate in WARNINGS:
        assert not any(expected in w for w in warnings), "%s: fires on the reference" % name
        d = copy.deepcopy(REF)
        mutate(d)
        got = V.validate(d, "Tablet")[1]
        assert any(expected in w for w in got), "%s: no warning with %r in %s" % (name, expected, got)
    print("%d warnings fire on their mutation and not on the reference" % len(WARNINGS))

    assert V.validate(REF["lorebook"], lorebook=True)[0] == []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "content.json").write_text(json.dumps(content_from(REF)), encoding="utf-8")
        (tmp / "broken.scenario").write_text('{"scenarioVersion": 3,', encoding="utf-8")
        run = lambda *args: subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
        out = run(SCRIPTS / "build_scenario.py", tmp / "content.json")
        assert out.returncode == 0 and Path(out.stdout.strip()).name == "The_Quiet_Ledger.scenario", out
        ok = run(SCRIPTS / "validate_scenario.py", out.stdout.strip(), "--tier", "Tablet", "--report", tmp / "validation.txt")
        assert ok.returncode == 0 and "RESULT: PASS 16/16" in (tmp / "validation.txt").read_text(encoding="utf-8"), ok
        assert all(s in ok.stdout for s in ("INFO Author's Note ~", "INFO System Prompt ~", "INFO Lorebook", "INFO   Core Memory ~")), ok.stdout
        (tmp / "one").mkdir()
        (tmp / "one/content.json").write_text(json.dumps(content_from(REF)), encoding="utf-8")
        one = run(SCRIPTS / "build_scenario.py", tmp / "one/content.json", "--validate", "--tier", "Tablet")
        assert one.returncode == 0 and one.stdout.splitlines()[0].endswith("The_Quiet_Ledger.scenario"), one
        assert (tmp / "one/validation.txt").read_text(encoding="utf-8") == one.stdout.split("\n", 1)[1], one.stdout
        over = dict(content_from(REF), authorsNote=REF["context"][1]["text"] + " rain" * 300)
        (tmp / "one/content.json").write_text(json.dumps(over), encoding="utf-8")
        one = run(SCRIPTS / "build_scenario.py", tmp / "one/content.json", "--validate")
        assert one.returncode == 1 and "FAIL 16" in (tmp / "one/validation.txt").read_text(encoding="utf-8"), one
        bad = run(SCRIPTS / "validate_scenario.py", tmp / "broken.scenario")
        assert bad.returncode == 1 and "FAIL 01" in bad.stdout, bad
        lore = run(SCRIPTS / "build_scenario.py", tmp / "content.json", "--lorebook")
        assert lore.stdout.strip().endswith(".lorebook"), lore
        assert run(SCRIPTS / "validate_scenario.py", lore.stdout.strip(), "--lorebook").returncode == 0
    print("CLI: build, validate (exit 0), build --validate (exit 0 and 1), unparseable file (exit 1), lorebook build and validate")
    print("ALL PASS")


if __name__ == "__main__":
    main()
