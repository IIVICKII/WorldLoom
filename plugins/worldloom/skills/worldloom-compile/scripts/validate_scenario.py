"""Deterministic checks for a Worldloom .scenario (or .lorebook) file.

Usage: python validate_scenario.py FILE [--tier Tablet|Scroll|Opus] [--lorebook] [--report validation.txt]
Exit 0 when every check passes, 1 otherwise. Stdlib only, no network.
"""
import argparse
import copy
import json
import math
import re
import sys
from pathlib import Path

FIXED = json.loads((Path(__file__).resolve().parent.parent / "assets" / "fixed_blocks.json").read_text(encoding="utf-8"))

CHECKS = {1: "json structure and key order", 2: "fixed blocks", 3: "lorebook container", 4: "entries match DEFAULT_ENTRY",
          5: "entry ids", 6: "entry order", 7: "entry role settings", 8: "entry text format", 9: "Story So Far shape",
          10: "Memory ATTG line", 11: "Author's Note style line", 12: "Prologue layout", 13: "System Prompt and Prefill",
          14: "phrase bias", 15: "banned names", 16: "tier budgets"}
LOREBOOK_CHECKS = range(3, 10)
ID = re.compile(r"00000000-0000-4000-8000-(\d{12})$")
NAMES = re.compile(r"\b(%s)\b" % "|".join(FIXED["bannedNames"]), re.I)
LEAK = re.compile(r"\b(will|eventually|later|comes to|destined|fated|turns out to be|is secretly|is actually|"
                  r"is revealed to be|unbeknownst to|by the end|ultimately|one day)\b", re.I)
SLOT = re.compile(r"\[(ROMANCE BLOCK|END |SCENARIO BANS|EVENT SYSTEM|EXAMPLES BLOCK|LitRPG only)")
ROLE_BY_NAME = {name: role for role, name in FIXED["fixedNames"].items()}
LEAK_ROLES = ("core_memory", "characters", "glossary")  # Story So Far is exempt: Upcoming needs these words
FIT = 0.92
ORDER = ["core_memory", "voice_guard", "characters", "story_so_far", "glossary", "tier1", "tier2", "operator_reference"]


def tokens(text):
    return len(text) / 4


def role_of(e):
    """Role from the entry itself: fixed display names, else Type line plus priority."""
    name = e.get("displayName")
    if name in ROLE_BY_NAME:
        return ROLE_BY_NAME[name]
    tier = {500: "tier1", 450: "tier2"}.get(e.get("contextConfig", {}).get("budgetPriority"))
    if not tier:
        return None
    lines = e.get("text", "").split("\n")
    return tier + ("_character" if len(lines) > 1 and lines[1] == "Type: character" else "_other")


def check_entries(lb, err, warn):
    if lb.get("lorebookVersion") != 6 or lb.get("settings") != {"orderByKeyLocations": False}:
        err(3, "lorebookVersion must be 6 and settings {\"orderByKeyLocations\": false}")
    if lb.get("categories") != []:
        err(3, "\"categories\" must be []")
    entries = lb.get("entries")
    if not isinstance(entries, list) or not entries:
        err(3, "\"entries\" must be a non-empty list")
        return []
    roles, seen_keys = [], {}
    for n, e in enumerate(entries, 1):
        if not isinstance(e, dict) or not isinstance(e.get("text"), str) or not isinstance(e.get("contextConfig"), dict):
            err(4, "entry %d: must be an object with a text string and a contextConfig" % n)
            roles.append(None)
            continue
        name = e.get("displayName") or "entry %d" % n
        text = e.get("text", "")
        lines = text.split("\n")
        # 4: only the documented fields may differ from DEFAULT_ENTRY
        norm, base = copy.deepcopy(e), copy.deepcopy(FIXED["defaultEntry"])
        for d in (norm, base):
            for k in ("text", "displayName", "id", "keys", "searchRange", "forceActivation", "enabled"):
                d.pop(k, None)
            for k in ("budgetPriority", "trimDirection"):
                d.get("contextConfig", {}).pop(k, None)
        if norm != base:
            err(4, "%s: a field outside the allowed set differs from DEFAULT_ENTRY" % name)
        if not e.get("displayName"):
            err(4, "entry %d: displayName is empty" % n)
        # 5
        m = ID.match(str(e.get("id")))
        if not m or int(m.group(1)) != n:
            err(5, "%s: id %r, expected counter %012d" % (name, e.get("id"), n))
        # 7
        role = role_of(e)
        roles.append(role)
        if role is None:
            err(7, "%s: not a fixed entry and budgetPriority is not 500 or 450" % name)
            continue
        want = FIXED["roles"][role]
        got = {"forceActivation": e.get("forceActivation"), "enabled": e.get("enabled"),
               "searchRange": e.get("searchRange"), "budgetPriority": e["contextConfig"].get("budgetPriority"),
               "trimDirection": e["contextConfig"].get("trimDirection")}
        for k, v in want.items():
            if got[k] != v:
                err(7, "%s (%s): %s is %r, expected %r" % (name, role, k, got[k], v))
        keyed = role.startswith("tier")
        keys = e.get("keys")
        if keyed and not keys:
            err(7, "%s: keyed entry has no keys" % name)
        if not keyed and keys != []:
            err(7, "%s: keys must be [] for always-on entries and Operator Reference" % name)
        if keyed:
            if not 4 <= len(keys) <= 6:
                warn("%s: %d keys, expected four to six" % (name, len(keys)))
            for k in keys:
                if str(k).lower() in seen_keys:
                    warn("key %r is on both %s and %s" % (k, seen_keys[str(k).lower()], name))
                seen_keys[str(k).lower()] = name
        if keyed or role in LEAK_ROLES:
            leak_words(name, text, warn)
        # 8
        if role == "operator_reference":
            if lines[0] != FIXED["operatorReferenceWarning"]:
                err(7, "Operator Reference must begin with the fixed warning line")
            continue
        for line in lines:
            if line.startswith(("----", "***")):
                err(8, "%s: entry text contains a ---- or *** line" % name)
            if line.startswith(("Keys:", "Category:")):
                err(8, "%s: entry text contains a Keys: or Category: line" % name)
        if role in ("characters", "glossary"):
            if lines[0] != e["displayName"] + ":":
                err(8, "%s: first line must be \"%s:\"" % (name, e["displayName"]))
        elif role != "story_so_far":
            if lines[0] != e["displayName"] or len(lines) < 2 or not re.match(r"Type: [a-z]+$", lines[1]):
                err(8, "%s: line 1 must be the entry name and line 2 \"Type: <entity_type>\"" % name)
            for line in lines[2:]:
                if re.match(r"[^:]+:\s*(nothing of note\.?)?\s*$", line, re.I):
                    err(8, "%s: empty key %r" % (name, line))
        if role == "voice_guard":
            vg = FIXED["voiceGuard"]
            if lines[:2] != vg[:2] or len(lines) != 6 or not lines[2].startswith(vg[2]) or lines[3:] != vg[3:]:
                err(8, "Voice Guard: fixed text altered (only the Forbidden line may be extended)")
        if role == "story_so_far":
            check_story_so_far(lines, err)
    # 6
    for must in ("core_memory", "voice_guard", "characters", "story_so_far", "operator_reference"):
        if roles.count(must) != 1:
            err(6, "expected exactly one %s entry, found %d" % (FIXED["fixedNames"][must], roles.count(must)))
    rank = [ORDER.index(r[:5] if r.startswith("tier") else r) for r in roles if r]
    if rank != sorted(rank):
        err(6, "entries out of order; expected Core Memory, Voice Guard, Characters, Story So Far, Glossary, "
               "Tier 1, Tier 2, Operator Reference")
    return list(zip(entries, roles))


def leak_words(where, text, warn):
    for hit in sorted({h.lower() for h in LEAK.findall(text)}):
        warn("%s: possible premise leak word %r" % (where, hit))


def check_prologue(prompt, cast, warn):
    """Habits the session copies from the Prologue. Heuristics, so warnings only."""
    quoted = [p for p in prompt.split("\n") if '"' in p]
    if cast and quoted:
        pc = "|".join(re.escape(n) for n in {cast[0], cast[0].split()[0]})
        narration = re.sub(r'"[^"]*"', "", quoted[-1])
        if re.search(r"\b(%s|I|[Yy]ou) (said|says|say)\b|\b(said|says) (%s)\b" % (pc, pc), narration):
            warn("Prologue: the last spoken line is the player character's; the final line belongs to another "
                 "character or the scene")
    if prompt.rstrip('"').endswith("?"):
        warn("Prologue ends on a question; it should end on an unresolved sensory or emotional beat")
    m = re.search(r"\b(said|says), (her|his|their|its|my|your) \w+", prompt)
    if m:
        warn("Prologue: appositive modifier after a speech verb (%r)" % m.group(0))
    m = re.search(r"\bnot (?:[\w'-]+ ){1,4}but\b", prompt)
    if m:
        warn("Prologue: \"not X but Y\" construction (%r)" % m.group(0))


def check_story_so_far(lines, err):
    """Story So Far / Type: memory / Earlier list / Upcoming (not happened yet) list; no Now line."""
    def section(i, label):
        if i < len(lines) and lines[i] == label + " nothing yet":
            return i + 1
        if i >= len(lines) or lines[i] != label:
            err(9, "Story So Far: expected %r at line %d" % (label, i + 1))
            return None
        j = i + 1
        while j < len(lines) and lines[j].startswith("- "):
            j += 1
        if j == i + 1:
            err(9, "Story So Far: %r has no \"- \" lines; write \"%s nothing yet\"" % (label, label))
        return j

    if any(l.startswith("Now:") for l in lines):
        err(9, "Story So Far: no Now line allowed")
    if lines[:2] != ["Story So Far", "Type: memory"]:
        err(9, "Story So Far: must start \"Story So Far\" then \"Type: memory\"")
    i = section(2, "Earlier:")
    if i is not None:
        i = section(i, "Upcoming (not happened yet):")
    if i is not None and i != len(lines):
        err(9, "Story So Far: unexpected line %r" % lines[i])


def validate(d, tier="Tablet", lorebook=False, info=None):
    """Return (errors, warnings); errors are (check number, message). Budget lines are appended to info."""
    errors, warnings = [], []
    info = [] if info is None else info
    err = lambda n, msg: errors.append((n, msg))
    warn = warnings.append
    if lorebook:
        check_entries(d, err, warn)
        return errors, warnings
    caps = FIXED["tiers"][tier]

    # 1
    if list(d) != FIXED["topLevelKeys"]:
        err(1, "top-level keys or their order are wrong; expected %s" % ", ".join(FIXED["topLevelKeys"]))
        return errors, warnings
    for key, want in (("scenarioVersion", 3), ("author", "Worldloom"), ("ephemeralContext", []), ("placeholders", []),
                      ("bannedSequenceGroups", FIXED["bannedSequenceGroups"])):
        if d[key] != want:
            err(1, "\"%s\" must be %s" % (key, json.dumps(want)))
    ctx, ms, bias = d["context"], d["messageSettings"], d["phraseBiasGroups"]
    shapes_ok = (isinstance(ctx, list) and len(ctx) == 2 and all(isinstance(c, dict) and isinstance(c.get("text"), str) for c in ctx)
                 and isinstance(ms, dict) and list(ms) == ["systemPrompt", "prefill"] and all(isinstance(v, str) for v in ms.values())
                 and isinstance(bias, list) and bias and isinstance(d["lorebook"], dict) and isinstance(d["tags"], list)
                 and all(isinstance(d[k], str) for k in ("title", "description", "prompt")))
    if not shapes_ok:
        err(1, "context (2 items), messageSettings (systemPrompt, prefill), phraseBiasGroups, lorebook, or a text field has the wrong shape")
        return errors, warnings
    memory, note, sp, pre, prompt = ctx[0]["text"], ctx[1]["text"], ms["systemPrompt"], ms["prefill"], d["prompt"]

    # 2
    for label, got, want in (("settings (FIXED_SETTINGS)", d["settings"], FIXED["settings"]),
                             ("contextDefaults (incl. DEFAULT_ENTRY)", d["contextDefaults"], FIXED["contextDefaults"]),
                             ("storyContextConfig", d["storyContextConfig"], FIXED["storyContextConfig"]),
                             ("Memory contextConfig", ctx[0].get("contextConfig"), FIXED["memoryContextConfig"]),
                             ("Author's Note contextConfig", ctx[1].get("contextConfig"), FIXED["authorsNoteContextConfig"]),
                             ("first phrase bias group (comma)", bias[0], FIXED["commaBiasGroup"])):
        if got != want:
            err(2, "%s differs from the fixed block" % label)

    # 3-9
    entries = check_entries(d["lorebook"], err, warn)

    # 10
    m = re.match(r"\[ Author: [^;\n]+; Title: ([^\n]+?); Tags: [^;\n]+; Genre: ([^;\n]+) \]$", memory)
    if not m:
        err(10, "Memory must be one line: [ Author: ...; Title: ...; Tags: ...; Genre: ... ]")
    elif m.group(1) != d["title"]:
        err(10, "ATTG title %r does not match \"title\" %r" % (m.group(1), d["title"]))
    tags = [str(t) for t in d["tags"]]
    for t in tags:
        if t != t.lower():
            warn("tag %r is not lowercase" % t)
    for g in (m.group(2).split(",") if m else []):
        if g.strip() not in tags:
            warn("ATTG Genre %r is not among \"tags\"" % g.strip())
    leak_words("Memory", memory, warn)
    # 11
    if not note.startswith("[ Write in a style that conveys the following: "):
        err(11, "Author's Note line 1 must be [ Write in a style that conveys the following: ... ]")
    cast = [l.split(":")[0].strip() for e, role in entries if role == "characters"
            for l in e["text"].split("\n")[1:] if ":" in l]
    for name in cast:
        if re.search(r"\b(%s)\b" % "|".join(re.escape(n) for n in {name, *name.split()}), note):
            warn("Author's Note names %r; it shapes narration only and carries no names" % name)
    leak_words("Author's Note", note, warn)
    # 12
    if re.search(r"\n[ \t]*\n", prompt) or prompt != prompt.strip() or not prompt:
        err(12, "Prologue has a blank line (or is empty); each paragraph starts after a single \\n")
    spoken = sum(1 for para in prompt.split("\n") if '"' in para)
    if spoken < 6:
        warn("Prologue has %d paragraphs with quoted speech; the rule asks for six spoken lines unless it lapsed" % spoken)
    check_prologue(prompt, cast, warn)
    leak_words("Prologue", prompt, warn)

    # 13
    spf, sp_lines = FIXED["systemPrompt"], sp.split("\n")
    if sp_lines[0] != spf["firstLine"]:
        err(13, "System Prompt first line altered")
    if [l for l in sp_lines if l in spf["headers"]] != spf["headers"]:
        err(13, "System Prompt headers missing or out of order: %s" % ", ".join(spf["headers"]))
    for label in ("ozoneLine", "namesLine"):
        if spf[label] not in sp_lines:
            err(13, "System Prompt fixed line missing or altered: %s" % spf[label])
    if spf["analyticalLine"] not in sp_lines:
        warn("System Prompt analytical-register ban line is absent; allowed only on the operator's request, noted in NOTES")
    if SLOT.search(sp):
        err(13, "System Prompt still has an unfilled template marker")
    if "## Dynamic Event System" in sp_lines:
        nxt = sp_lines[sp_lines.index("## Dynamic Event System") + 1:][:1]
        if not nxt or not nxt[0].startswith("- "):
            err(13, "Dynamic Event System has no \"-\" bullets")
    if tier == "Tablet" and "## Examples" in sp_lines:
        err(13, "Examples block is for Scroll and Opus only")
    pf = FIXED["prefill"]
    if not pre.startswith(pf["head"][0] + "\n") or not pre.endswith("\n" + "\n".join(pf["tail"])):
        err(13, "Prefill must start with the \"Understood.\" line and end \"---\\n[Story continues:]\"")
    for label in ("voiceLine", "appositiveLine"):
        if pf[label] not in pre.split("\n"):
            err(13, "Prefill %s missing or altered" % label)

    # 14
    banned_words = {w for l in sp_lines if l.startswith("- NEVER use:")
                    for w in re.findall(r"[a-z']+", l.split(":", 1)[1].lower())}
    if not 2 <= len(bias) <= 3:
        err(14, "expected the comma group plus one or two story groups, found %d groups" % len(bias))
    for g in bias[1:]:
        b, words = g.get("bias"), [p.get("sequence") for p in g.get("phrases", []) if isinstance(p, dict)]
        shell = {k: v for k, v in g.items() if k not in ("phrases", "bias", "generateOnce")}
        if (not isinstance(b, (int, float)) or b == 0 or abs(b) > 0.5 or g.get("generateOnce") is not (b > 0)
                or shell != {"ensureSequenceFinish": False, "enabled": True, "whenInactive": False}):
            err(14, "story bias group: bias must be non-zero within +-0.5, generateOnce true only for a positive group")
        if not 4 <= len(words) <= 8 or any(p != {"sequences": [], "sequence": w, "type": 2}
                                            for p, w in zip(g.get("phrases", []), words)):
            err(14, "story bias group needs four to eight phrases shaped {\"sequences\": [], \"sequence\": w, \"type\": 2}")
        for w in words:
            if not isinstance(w, str) or not re.match(r"[a-z]+$", w):
                err(14, "bias word %r must be one lowercase word, no space or punctuation" % w)
            elif w in banned_words:
                warn("bias word %r is already in a NEVER use line" % w)

    # 15
    texts = [("title", d["title"]), ("description", d["description"]), ("Prologue", prompt), ("Memory", memory),
             ("Author's Note", note), ("Prefill", pre), ("tags", " ".join(map(str, d["tags"]))),
             ("System Prompt", "\n".join(l for l in sp_lines if l != spf["namesLine"]))]
    texts += [(e.get("displayName", "entry"), "%s\n%s\n%s" % (e.get("displayName"), e.get("text"), " ".join(map(str, e.get("keys") or []))))
              for e, _ in entries]
    for where, text in texts:
        for hit in sorted(set(NAMES.findall(text))):
            err(15, "banned name %r in %s" % (hit, where))

    # 16
    lb = sum(tokens(e.get("text", "")) for e, role in entries if role != "operator_reference")
    # Where a lorebook cut can come from: the keyed entries and the Glossary, largest first.
    sizes = sorted(((tokens(e.get("text", "")), e.get("displayName")) for e, role in entries
                    if role and (role.startswith("tier") or role == "glossary")), reverse=True)
    first = "; largest trimmable entries: " + ", ".join("%s ~%d" % (n, t) for t, n in sizes[:4]) if sizes else ""
    for label, got, cap in (("Author's Note", tokens(note), caps["AN"]), ("System Prompt", tokens(sp), caps["SP"]),
                            ("Lorebook (Operator Reference excluded)", lb, caps["LB"])):
        fit = round(cap * FIT)
        info.append("%s ~%d / %d (fit %d)" % (label, got, cap, fit))
        over = math.ceil(got - fit)
        cut = "; cut about %d tokens (~%d characters) to reach the fit target of %d%s" % (
            over, over * 4, fit, first if label.startswith("Lorebook") else "")
        if label.startswith("Lorebook") and over > 0 and sizes:
            # Scale every trimmable entry by the same factor, so the always-on entries keep their size.
            trimmable = sum(t for t, _ in sizes)
            room = fit - (got - trimmable)
            cut += "; one split that reaches the fit target: " + ", ".join(
                "%s ~%d (~%d characters)" % (n, t * room // trimmable, t * room // trimmable * 4)
                for t, n in sizes) if room > 0 else "; the always-on entries alone are over the fit target"
        if got > cap:
            err(16, "%s ~%d tokens, over the %s cap of %d%s" % (label, got, tier, cap, cut))
        elif got > fit:
            warn("%s ~%d tokens, over the fit target of %d (cap %d)%s" % (label, got, fit, cap, cut))
    info += ["  %s ~%d%s" % (e.get("displayName"), tokens(e.get("text", "")),
                             " (excluded)" if role == "operator_reference" else "") for e, role in entries]
    for e, role in entries:
        if role == "core_memory" and not caps["CM"][0] <= tokens(e.get("text", "")) <= caps["CM"][1]:
            warn("Core Memory ~%d tokens, outside CM_RANGE %d-%d" % (tokens(e["text"]), *caps["CM"]))
    return errors, warnings


def report(errors, warnings, tier, lorebook=False, info=()):
    failed = {n for n, _ in errors}
    numbers = sorted(set(LOREBOOK_CHECKS if lorebook else CHECKS) | failed)
    lines = []
    for n in numbers:
        lines.append("%s %02d %s" % ("FAIL" if n in failed else "PASS", n, CHECKS[n]))
        lines += ["     - " + msg for k, msg in errors if k == n]
    lines += ["INFO " + i for i in info]
    lines += ["WARN " + w for w in warnings]
    lines.append("RESULT: %s %d/%d checks passed, %d warnings%s" % (
        "FAIL" if failed else "PASS", len(numbers) - len(failed), len(numbers), len(warnings),
        "" if lorebook else " (tier %s)" % tier))
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--tier", default="Tablet", choices=list(FIXED["tiers"]))
    ap.add_argument("--lorebook", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    info = []
    try:
        d = json.loads(Path(a.file).read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            raise ValueError("top level is not a JSON object")
    except (OSError, ValueError) as e:
        errors, warnings = [(1, "JSON does not parse: %s" % e)], []
    else:
        errors, warnings = validate(d, a.tier, a.lorebook, info)
    text = report(errors, warnings, a.tier, a.lorebook, info)
    if a.report:
        Path(a.report).write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
