"""Assemble a NovelAI .scenario (or .lorebook) from scenario_content.json and the fixed blocks.

Usage: python build_scenario.py scenario_content.json [--out-dir DIR] [--lorebook] [--validate [--tier TIER]]
Prints the path of the file it wrote. With --validate it then runs the validator on it, writes
validation.txt beside it, prints the report, and exits 0 on a pass, 1 otherwise. Stdlib only.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
FIXED = json.loads((SKILL / "assets" / "fixed_blocks.json").read_text(encoding="utf-8"))
TEMPLATE = (SKILL / "references" / "system-prompt-template.md").read_text(encoding="utf-8").rstrip("\n").split("\n")


def system_prompt(sp):
    """Fill the template's marked places. sp: romance, litrpg, examples, scenarioBans, eventSystem."""
    out, block = [], None
    for line in TEMPLATE:
        if line.startswith("[ROMANCE BLOCK"):
            block = "romance"
        elif line.startswith("[EXAMPLES BLOCK"):
            block = "examples"
        elif line.startswith("[END "):
            block = None
        elif line.startswith("[LitRPG only:"):
            if sp.get("litrpg"):
                out.append(line.split('"')[1])
        elif line.startswith("[SCENARIO BANS"):
            out += ["- NEVER use: " + words for words in sp.get("scenarioBans", [])]
        elif line.startswith("[EVENT SYSTEM"):
            out += ["- " + bullet for bullet in sp["eventSystem"]]
        elif block and not sp.get(block):
            continue
        elif block == "examples" and line.startswith("Attraction.") and not sp.get("romance"):
            continue
        else:
            out.append(line)
    return "\n".join(out)


def prefill(continuation):
    p = FIXED["prefill"]
    return "\n".join(p["head"] + ["- " + line for line in continuation or p["defaultContinuation"]] + p["tail"])


def voice_guard(extra):
    lines = list(FIXED["voiceGuard"])
    if extra:
        lines[2] += " " + extra.strip()
    return "\n".join(lines)


def entry(spec, number):
    role = FIXED["roles"][spec["role"]]
    e = copy.deepcopy(FIXED["defaultEntry"])
    e["text"] = spec["text"]
    e["displayName"] = FIXED["fixedNames"].get(spec["role"]) or spec["name"]
    e["id"] = "00000000-0000-4000-8000-%012d" % number
    e["keys"] = spec.get("keys", [])
    e["searchRange"] = role["searchRange"]
    e["enabled"] = role["enabled"]
    e["forceActivation"] = role["forceActivation"]
    e["contextConfig"]["budgetPriority"] = role["budgetPriority"]
    e["contextConfig"]["trimDirection"] = role["trimDirection"]
    return e


def build(content):
    specs = list(content["entries"])
    if not any(s["role"] == "voice_guard" for s in specs):
        # Voice Guard is fixed text; the content file only extends its forbidden list.
        specs.insert(1, {"role": "voice_guard", "text": voice_guard(content.get("voiceGuardExtra"))})
    bias = [FIXED["commaBiasGroup"]] + [
        {"phrases": [{"sequences": [], "sequence": w, "type": 2} for w in g["words"]],
         "ensureSequenceFinish": False, "generateOnce": g["bias"] > 0, "bias": g["bias"],
         "enabled": True, "whenInactive": False}
        for g in content["phraseBias"]]
    return {
        "scenarioVersion": 3,
        "title": content["title"],
        "description": content["description"],
        "prompt": content["prologue"],
        "tags": content["tags"],
        "context": [{"text": content["memory"], "contextConfig": FIXED["memoryContextConfig"]},
                    {"text": content["authorsNote"], "contextConfig": FIXED["authorsNoteContextConfig"]}],
        "ephemeralContext": [],
        "placeholders": [],
        "settings": FIXED["settings"],
        "lorebook": {"lorebookVersion": 6, "entries": [entry(s, i + 1) for i, s in enumerate(specs)],
                     "settings": {"orderByKeyLocations": False}, "categories": []},
        "author": "Worldloom",
        "storyContextConfig": FIXED["storyContextConfig"],
        "contextDefaults": FIXED["contextDefaults"],
        "phraseBiasGroups": bias,
        "bannedSequenceGroups": FIXED["bannedSequenceGroups"],
        "messageSettings": {
            "systemPrompt": content.get("systemPromptOverride") or system_prompt(content["systemPrompt"]),
            "prefill": prefill(content.get("prefillContinuation"))},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("content")
    ap.add_argument("--out-dir")
    ap.add_argument("--lorebook", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--tier", default="Tablet", choices=list(FIXED["tiers"]))
    a = ap.parse_args()
    src = Path(a.content)
    try:
        scenario = build(json.loads(src.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, KeyError, TypeError) as err:
        sys.exit("build failed: %s: %s (see references/content-schema.md)" % (type(err).__name__, err))
    name = re.sub(r"\s+", "_", re.sub(r'[<>:"/\\|?*]', "", scenario["title"]).strip())
    out = Path(a.out_dir or src.parent) / (name + (".lorebook" if a.lorebook else ".scenario"))
    built = scenario["lorebook"] if a.lorebook else scenario
    out.write_text(json.dumps(built, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out)
    if a.validate:
        import validate_scenario as V  # beside this script
        info = []
        errors, warnings = V.validate(built, a.tier, a.lorebook, info)
        text = V.report(errors, warnings, a.tier, a.lorebook, info)
        (out.parent / "validation.txt").write_text(text, encoding="utf-8")
        sys.stdout.write(text)
        sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
